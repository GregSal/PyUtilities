'''
Created on Feb 23 2019

@author: Greg Salomons
Test ground for constructing GUI
'''
from typing import Union, TypeVar, List, Dict, Callable, Any
from pathlib import Path
from functools import partial
import xml.etree.ElementTree as ET
import re

import tkinter as tk
import tkinter.font as tkFont
import tkinter.ttk as ttk
from tkinter import scrolledtext


import GUI_Management.gui_methods as gm
import GUI_Management.template_config as tp
from GUI_Management.object_reference_management import ReferenceTracker
from GUI_Management.object_reference_management import ReferenceSet
from GUI_Management.object_reference_management import ObjectSet
from CustomVariableSet.custom_variable_sets import StringV
from CustomVariableSet.custom_variable_sets import CustomVariableSet


ObjectDef = Union[Callable, type]
StringValue = Union[tk.StringVar, str]
TkItem = Union[tk.Widget, ttk.Widget, tk.Wm]
Definition = Dict[str, Dict[str, Any]]
ArgType = TypeVar('ArgType', List[Any], Dict[str, Any])

# TODO Need to clean extra white space from all findtext calls
# TODO Need to pass all findtext results through resolve
# TODO Need method to handle binding events


class GuiManager():
    identifier_list = ['Widget', 'Variable', 'Image', 'Command', 'Font', 'X']
    lookup_list = [('Tkinter', {'tk': tk, 'ttk': ttk, 'gm': gm})]
    # TODO Create import method that builds a sub-class GuiManager and merges its top window/widget with the current GuiManager
    # Use geometry to a widget, link a window to a related window or widget
    # Merge the reference attribute

    def __init__(self, data_set: CustomVariableSet, xml_file: Path):
        self.reference = ReferenceTracker(self.identifier_list,
                                          self.lookup_list)
        self.reference.add_lookup_group('Data', data_set)
        # Question is it a good idea to include globals in the reference set?
        self.reference.add_lookup_group('Globals', globals())
        self.data_link = dict()
        self.definition = self.load_xml(xml_file)
        self.make_root()
        self.initialize_variables()
        self.initialize_images()
        self.initialize_styles()
        self.initialize_windows()
        self.initialize_widgets()
        self.initialize_commands()
        root_widget = self.definition.find('RootWindow')
        self.configure_window(root_widget)
        for window_def in self.definition.findall(r'.//Window'):
            self.configure_window(window_def)
        self.configure_widgets()

    def load_xml(self, xml_file: Path):
        xml_tree = ET.parse(str(xml_file))
        return xml_tree.getroot()

    def make_root(self):
        root = tk.Tk()
        self.reference.set_item('Widget', 'root', root)

    def execute(self):
        root = self.lookup_item('Window', 'root')
        root.mainloop()

    def resolve(self, ref_set: ReferenceSet)->ObjectSet:
        '''Convert a one or more reference strings to their corresponding
            objects.  The return container type will match the input container
            type.

        Arguments:
            ref_set {ReferenceSet} -- A dictionary, sequence or individual
            string containing object references.

        Returns:
            {ObjectDict} -- An object or container with the same structure as
                the input, with all string references replaced by the object
                referenced every non-matching element will be left unchanged.
        '''
        return self.reference.lookup_references(ref_set)

    def lookup_item(self, group_id: str, item_name: str) -> Any:
        '''Fetch an object reference.
        Arguments:
            group_id {str} -- A single character used to identify the
                reference group. Only the first character of the supplied
                string is uses as the identifier.
            item_name {str} -- The reference name of the group item.
        Returns:
            {Any} -- The object referenced.
        '''
        return self.reference.lookup_item(group_id, item_name)

    def set_reference(self, identifier: str, name: str, item: Any):
        '''Add or update a reference item.

        Arguments:
            identifier {str} -- A single character used to identify the
                reference group. Only the first character of the supplied
                string is uses as the identifier.
            name {str} -- The name used to reference the group item.
            item {Any} -- The object to be referenced
        '''
        self.reference.set_item(identifier, name, item)

    def get_class(self, object_def: ET.Element, class_lookup: str)->ObjectDef:
        object_str = object_def.findtext(class_lookup)
        return self.resolve(object_str)

    def get_parent(self, name: str)->tk.Widget:
        parent_search = './/*[@name="{}"]../..'.format(name)
        parent_name = self.definition.find(parent_search).attrib['name']
        parent = self.lookup_item('W', parent_name)
        return parent

    def build_data_link(self, variable: ET.Element):
        variable_name = variable.attrib['name']
        data_name = variable.findtext('data_reference')
        if data_name is not None:
            self.data_link[variable_name] = data_name
        pass

    def initialize_variables(self):
        for variable in self.definition.findall('VariableSet/*'):
            name = variable.attrib['name']
            variable_class = self.get_class(variable, 'variable_class')
            new_variable = variable_class(name=name)
            self.set_reference('Variable', name, new_variable)
            self.build_data_link(variable)
            self.update_variable(name, 'from_data')

    def initialize_images(self):
        for image in self.definition.findall('ImageSet/*'):
            name = image.attrib['name']
            image_file = image.attrib['file_path']
            image_type = image.tag
            if 'PhotoImage' in image_type:
                new_image = tk.PhotoImage(file=image_file)
            elif 'BitmapImage' in image_type:
                options = dict()
                fg_colour = image.attrib.get('foreground')
                if fg_colour:
                    options['foreground'] = fg_colour
                bg_colour = image.attrib.get('background')
                if bg_colour:
                    options['background'] = bg_colour
                new_image = tk.BitmapImage(file=image_file, **options)
            self.set_reference('Image', name, new_image)

    def initialize_styles(self):
        theme = self.definition.findtext('Styles/Theme')
        style = ttk.Style()
        style.theme_use(theme)
        for font_def in self.definition.findall('Styles/Font'):
            name = font_def.attrib['name']
            options = dict()
            options['family'] = font_def.findtext('family')
            options['size'] = int(font_def.findtext('size'))
            options['weight'] = font_def.findtext('weight')
            new_font = tkFont.Font(**options)
            self.set_reference('Font', name, new_font)

    def initialize_windows(self):
        for window_def in self.definition.findall(r'.//WindowSet/*'):
            name = window_def.attrib['name']
            parent = self.get_parent(name)
            new_window = tk.Toplevel(name=name, master=parent)
            self.set_reference('Window', name, new_window)

    def initialize_widgets(self):
        for widget_def in self.definition.findall(r'.//WidgetSet/*'):
            name = widget_def.attrib['name']
            parent = self.get_parent(name)
            widget_class = self.get_class(widget_def, 'widget_class')
            new_widget = widget_class(name=name, master=parent)
            self.set_reference('Widget', name, new_widget)

    def initialize_commands(self):
        def get_positional_arguments(command: ET.Element)->List[Any]:
            arg_set = [arg.text for arg in command.findall('PositionalArgs/*')]
            args = self.resolve(arg_set)
            if args is None:
                args = []
            return args

        def get_keyword_arguments(command)->Dict[str, Any]:
            keyword_args = command.find('KeywordArgs')
            kwargs = None
            if keyword_args is not None:
                kwargs = self.resolve(keyword_args.attrib)
            if not kwargs:
                kwargs = dict()
            return kwargs

        for command in self.definition.findall('CommandSet/*'):
            name = command.attrib['name']
            function = self.get_class(command, 'function')
            data_update = bool(command.findtext('update_data'))
            args = get_positional_arguments(command)
            kwargs = get_keyword_arguments(command)
            if data_update:
                command_callable = partial(self.update_and_run,
                                           function, *args, **kwargs)
            else:
                command_callable = partial(function, *args, **kwargs)
            self.set_reference('Command', name, command_callable)
            # The X:: reference indicates a reference to the output of the
            # C:: command reference ## Not yet implemented
            self.set_reference('Xecute', name, command_callable)
        pass

    def configure_item(self, tk_item: TkItem, item_def: ET.Element):
        configuration = item_def.find('Configure')
        if configuration is not None:
            options = self.resolve(configuration.attrib)
            if options:
                tk_item.configure(**options)
            for config_def in configuration.findall('Set'):
                item_method_name = str(config_def.text)
                item_method = getattr(tk_item, item_method_name)
                options = dict()
                options.update(self.resolve(config_def.attrib))
                item_method(**options)
        if hasattr(tk_item, 'build'):
            tk_item.build(item_def, self.reference)
        pass

    def set_appearance(self, tk_item: TkItem, item_def: ET.Element):
        options = dict()
        appearance = item_def.find('Appearance')
        if appearance is not None:
            options.update(self.resolve(appearance.attrib))
            tk_item.configure(**options)
        pass

    def grid_config(self, tk_item: TkItem, item_def: ET.Element):
        grid_def = item_def.find('GridConfigure')
        if grid_def is not None:
            for column_setting in grid_def.findall('ColumnConfigure'):
                column_options = self.resolve(column_setting.attrib)
                column_index = int(column_options.pop('column'))
                tk_item.columnconfigure(column_index, column_options)
            for row_setting in grid_def.findall('RowConfigure'):
                row_options = self.resolve(row_setting.attrib)
                row_index = row_options.pop('row')
                tk_item.rowconfigure(row_index, row_options)
        pass

    def set_fullscreen(self, window: tk.Wm, settings: ET.Element):
        fullscreen = settings.find('Fullscreen')
        if fullscreen:
            if 'true' in str(fullscreen.text):
                window.attributes('-fullscreen', True)
            elif 'false' in str(fullscreen.text):
                window.attributes('-fullscreen', False)
        pass

    def set_window_dimensions(self, window: tk.Wm, geometry: ET.Element):
        geometry_list = ['Width', 'Height', 'Xposition', 'Yposition']
        geometry_reg = re.compile(r'''
            (?P<Width>\d+)x(?P<Height>\d+) # Width x Height
            (?P<Xposition>[-+]\d+)         # Horizontal screen position
            (?P<Yposition>[-+]\d+)         # Vertical screen position
            ''', re.X)
        geometry_str = '{Width:d}x{Height:d}{Xposition:+d}{Yposition:+d}'

        current_size = geometry_reg.match(window.geometry())
        dimensions = dict()
        for dim in geometry_list:
            dimension = geometry.findtext(dim)
            if dimension is not None:
                dimensions[dim] = int(self.resolve(dimension))
            else:
                dimensions[dim] = int(current_size.group(dim))
        dimension_str = geometry_str.format(**dimensions)
        window.geometry(dimension_str)

    def stacking_adjustment(self, window: tk.Wm, geometry: ET.Element):
        stacking_group = geometry.find('Stacking')
        if stacking_group:
            for stacking_element in stacking_group.iter():
                stacking_name = stacking_element.tag
                if hasattr(tk.Tk, stacking_name):
                    stack_method = getattr(window, stacking_name)
                    stack_window = self.resolve(str(stacking_element.text))
                    stack_method(stack_window)
        pass

    def set_window_geometry(self, window: tk.Wm, settings: ET.Element):
        geometry = settings.find('Geometry')
        if geometry is not None:
            self.set_window_dimensions(window, geometry)
            self.stacking_adjustment(window, geometry)
        else:
            self.set_fullscreen(window, settings)
        pass

    def set_icon_state(self, window: tk.Wm, settings: ET.Element):
        newstate = settings.findtext(r'.//state')
        if newstate:
            window.state(newstate)
        pass

    def configure_window(self, window_def):
        name = window_def.attrib['name']
        window = self.lookup_item('Window', name)
        window_settings = window_def.find('Settings')
        if window_settings is not None:
            title_text = window_settings.findtext('title')
            if title_text:
                window.title(title_text)
            self.set_appearance(window, window_settings)
            self.grid_config(window, window_settings)
            self.set_window_geometry(window, window_settings)
            self.set_icon_state(window, window_settings)
        self.configure_item(window, window_def)

    def set_widget_geometry(self, widget: tk.Widget, settings: ET.Element):
        options = dict()
        geometry = settings.find('Geometry')
        padding = geometry.find('Padding')
        if padding is not None:
            options.update(self.resolve(padding.attrib))
        placement = geometry[0]
        options.update(self.resolve(placement.attrib))
        if 'Grid' in placement.tag:
            widget.grid(**options)
        elif 'Pack' in placement.tag:
            widget.pack(**options)
        pass

    def configure_widgets(self):
        for widget_def in self.definition.findall(r'.//WidgetSet/*'):
            name = widget_def.attrib['name']
            widget = self.lookup_item('Widget', name)
            self.configure_item(widget, widget_def)
            widget_settings = widget_def.find('Settings')
            self.set_appearance(widget, widget_settings)
            self.grid_config(widget, widget_settings)
            self.set_widget_geometry(widget, widget_settings)

    def update_variable(self, variable_name: str, update_method='from_data'):
        variable = self.lookup_item('Variable', variable_name)
        data_name = self.data_link.get(variable_name)
        if data_name:
            if update_method in 'from_data':
                data_item = self.lookup_item('Data', data_name)
                try:
                    data_value = data_item.value
                except AttributeError:
                    data_value = data_item
                variable.set(data_value)
            if update_method in 'to_data':
                data_value = variable.get()
                self.set_reference('Data', data_name, data_value)
        pass

    def update_data(self):
        for variable_name in self.data_link.keys():
            self.update_variable(variable_name, 'to_data')
        pass

    def update_and_run(self, command: Callable, *args, **kwargs)->Callable:
        self.update_data()
        command(*args, **kwargs)


def main():
    #gui_def_file = Path(r'.\FileSelectGUI.xml')
    gui_def_file = Path(r'.\TestGUI_4.xml')
    variable_definitions = [{'name': 'test_string',
                             'variable_type': StringV,
                             'default': 'Hi There!'
                             }
                            ]
    template_data_set = tp.TemplateSelectionsSet(variable_definitions)
    template_definitions = tp.load_template_list(template_data_set['template_pickle'])
    template_data_set['TemplateData'] = template_definitions

    gui = GuiManager(template_data_set, gui_def_file)
    gui.execute()

if __name__ == '__main__':
    main()
