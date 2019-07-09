'''
Created on Feb 23 2019

@author: Greg Salomons
Test ground for constructing GUI
Function:
    load_xml(xml_file: Path)->ET.ElementTree
        Read in the XML file
Class:
     GuiManager(data_set: CustomVariableSet, xml_file: Path)
        Build a Tkinter GUI from an XML file.
Methods:
    execute()
        Run the GUI.
    get_class(object_def: ET.Element, class_lookup: str)->ObjectDef
        Return the class object or callable of a given type.
    get_parent(name: str)->tk.Widget
        Return the parent widget of the widget with the given name.
    build_data_link(variable: ET.Element)
        Record the link between a TK variable and a Data item.
    initialize_variables()
        Read in the Variable definitions from the XML file and initialize the
        TK variables.
    initialize_windows()
        Read in the Window definitions from the XML file and initialize
        the TK windows.
    initialize_widgets()
        Read in the Widget definitions from the XML file and initialize
        all widgets.
    initialize_images()
        Read in the Image definitions from the XML file and create
        TK image objects.
    initialize_styles()
        Generate TK Style and Font objects from the XML file definitions.
    initialize_commands()
        Read in the Command definitions from the XML file and create
        referenced Callables using partial.
    configure_item(tk_item: TkItem, item_def: ET.Element)
        Set the Widget options defined in the Configure section of the
        widget's XML definition.
    set_appearance(tk_item: TkItem, item_def: ET.Element)
        Set the Widget options defined in the Appearance section of the
        widget's XML definition.
    grid_config(tk_item: TkItem, item_def: ET.Element)
        Set the Widget's grid row and column options defined in the
        GridConfigure section of the widget's XML definition.
    set_fullscreen(window: tk.Wm, settings: ET.Element)
        Set or Unset window full screen according to the XML setting.
    set_window_dimensions(window: tk.Wm, geometry: ET.Element)
        Set window size and shape according to the XML setting.
    stacking_adjustment(window: tk.Wm, geometry: ET.Element)
        Set window arrangement (in front of or behind other windows).
    set_window_geometry(window: tk.Wm, settings: ET.Element)
        Apply window geometry settings given in the XML element.
    set_icon_state(window: tk.Wm, settings: ET.Element)
        Set the window state as given in the XML element.
    configure_window(window_def)
        Apply window settings settings given in the XML element.
    set_widget_geometry(widget: tk.Widget, settings: ET.Element)
        Apply window geometry settings given in the XML element.
    configure_widgets()
        Apply all widget settings settings given in the GUI XML file.
    update_variable(variable_name: str, update_method='from_data')
        Synchronize a TK variable with its corresponding application data.
    update_data()
        Copy all TK variable values to their corresponding application data item.
    update_and_run(command: Callable, *args, **kwargs)
        A helper partial that forces a call to update_data before running command.

'''
from typing import Union, TypeVar, List, Dict, Callable, Any
from pathlib import Path
from functools import partial
import xml.etree.ElementTree as ET
import re
import tkinter as tk
import tkinter.font as tkFont
import tkinter.ttk as ttk
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


def load_xml(xml_file: Path)->ET.ElementTree:
    '''Read in the XML file
    Arguments:
        xml_file {Path} -- The full path to the XML file
    Returns:
        {ET.ElementTree} -- The Root XML element for th e file
    '''
    xml_tree = ET.parse(str(xml_file))
    return xml_tree.getroot()

class GuiManager():
    '''Build a Tkinter GUI from an XML file.
        Its Main role is to create the widgets and provide an interface to the
        GUIv through the references attribute.
        Arguments:
            data_set {CustomVariableSet, Dict[str, Any]} -- Variables passed to
                or from the GUI.
            xml_file {Path} -- The primary XML file describing the GUI.
    '''
    identifier_list = ['Widget', 'Variable', 'Image', 'Command', 'Font', 'X']
    lookup_list = [('Tkinter', {'tk': tk, 'ttk': ttk, 'gm': gm})]
    # TODO Create import method that builds a sub-class GuiManager and merges
    # its top window/widget with the current GuiManager
    # Use geometry to a widget, link a window to a related window or widget
    # Merge the reference attribute

    def __init__(self, data_set: CustomVariableSet, xml_file: Path):
        '''Build a Tkinter GUI from an XML file.
        Its Main role is to create the widgets and provide an interface to it
        through the references attribute.
        Arguments:
            data_set {CustomVariableSet, Dict[str, Any]} -- Variables passed to
                or from the GUI.
            xml_file {Path} -- The primary XML file describing the GUI.
        '''
        # TODO add ability to pass a pre-built ReferenceTracker
        self.reference = ReferenceTracker(self.identifier_list,
                                          self.lookup_list)
        self.reference.add_lookup_group('Data', data_set)
        # Question is it a good idea to include globals in the reference set?
        self.reference.add_lookup_group('Globals', globals())
        self.data_link = dict()
        self.definition = load_xml(xml_file)
        self.reference.set_item('Widget', 'root', tk.Tk())
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

    def execute(self):
        '''Run the GUI.
        '''
        root = self.reference.lookup_item('Window', 'root')
        root.mainloop()

    def get_class(self, object_def: ET.Element, class_lookup: str)->ObjectDef:
        '''Return the class object or callable of a given type.
        Arguments:
            object_def {ET.Element} -- The object definition element in the XML
            class_lookup {str} -- The type of object.
                Can be one of:
                    'variable_class'
                    'widget_class'
                    'function'
        Returns:
            ObjectDef -- A Tkinter widget or variable class or a callable.
        '''
        object_str = object_def.findtext(class_lookup)
        return self.reference.resolve(object_str)

    def get_parent(self, name: str)->tk.Widget:
        '''Return the parent widget of the widget with the given name.
            The parent is based on the parent element in the XML file.
            The parent must have already been initialized.
        Arguments:
            name {str} -- The name assigned to the widget in the XML file.
        Returns:
            tk.Widget -- The actual instance of the parent.
        '''
        parent_search = './/*[@name="{}"]../..'.format(name)
        parent_name = self.definition.find(parent_search).attrib['name']
        parent = self.reference.lookup_item('W', parent_name)
        return parent

    def build_data_link(self, variable: ET.Element):
        '''Record the link between a TK variable and a Data item.
        Arguments:
            variable {ET.Element} -- The XML variable element
        '''
        variable_name = variable.attrib['name']
        data_name = variable.findtext('data_reference')
        if data_name is not None:
            self.data_link[variable_name] = data_name
        pass

    def initialize_variables(self):
        '''Read in the Variable definitions from the XML file and initialize
            the TK variables.
        '''
        # Question Perhaps mofe initialization methods to the module level
        # and make one initialization method that calls all for them.
        for variable in self.definition.findall('VariableSet/*'):
            name = variable.attrib['name']
            variable_class = self.get_class(variable, 'variable_class')
            new_variable = variable_class(name=name)
            self.reference.set_item('Variable', name, new_variable)
            self.build_data_link(variable)
            self.update_variable(name, 'from_data')

    def initialize_windows(self):
        '''Read in the Window definitions from the XML file and initialize
            the TK windows.
        '''
        for window_def in self.definition.findall(r'.//WindowSet/*'):
            name = window_def.attrib['name']
            parent = self.get_parent(name)
            new_window = tk.Toplevel(name=name, master=parent)
            self.reference.set_item('Window', name, new_window)

    def initialize_widgets(self):
        '''Read in the Widget definitions from the XML file and initialize
            all widgets.
        '''
        for widget_def in self.definition.findall(r'.//WidgetSet/*'):
            name = widget_def.attrib['name']
            parent = self.get_parent(name)
            widget_class = self.get_class(widget_def, 'widget_class')
            new_widget = widget_class(name=name, master=parent)
            self.reference.set_item('Widget', name, new_widget)

    def initialize_images(self):
        '''Read in the Image definitions from the XML file and create
            TK image objects.
        '''
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
            self.reference.set_item('Image', name, new_image)

    def initialize_styles(self):
        '''Generate TK Style and Font objects from the XML file definitions.
        '''
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
            self.reference.set_item('Font', name, new_font)

    def initialize_commands(self):
        '''Read in the Command definitions from the XML file and create
            referenced Callables using partial.
        '''
        def get_positional_arguments(command: ET.Element)->List[Any]:
            '''Read in the pre-defined positional arguments for the command
                and resolve any references.
            Arguments:
                command {ET.Element} -- The XML element command definition.
            Returns:
                List[Any] -- A list of positional arguments (or an empty list)
            '''
            arg_set = [arg.text for arg in command.findall('PositionalArgs/*')]
            args = self.reference.resolve(arg_set)
            if args is None:
                args = []
            return args

        def get_keyword_arguments(command)->Dict[str, Any]:
            '''Read in the pre-defined keyword arguments for the command
                and resolve any references.
            Arguments:
                command {ET.Element} -- The XML element command definition.
            Returns:
                Dict[str, Any] -- A dictionary containing keyword arguments and
                their values (or an empty dictionary).
            '''
            keyword_args = command.find('KeywordArgs')
            kwargs = None
            if keyword_args is not None:
                kwargs = self.reference.resolve(keyword_args.attrib)
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
            self.reference.set_item('Command', name, command_callable)
            # The X:: reference indicates a reference to the output of the
            # C:: command reference ## Not yet implemented
            self.reference.set_item('Xecute', name, command_callable)
        pass

    def configure_item(self, tk_item: TkItem, item_def: ET.Element):
        '''Set the Widget options defined in the Configure section of the
            widget's XML definition.
        Arguments:
            tk_item {TkItem} -- The widget (or window) instance.
            item_def {ET.Element} -- The Widget/Window XML Element definition.
        '''
        # Question should configure_item become a module level function?
        configuration = item_def.find('Configure')
        if configuration is not None:
            options = self.reference.resolve(configuration.attrib)
            if options:
                tk_item.configure(**options)
            for config_def in configuration.findall('Set'):
                item_method_name = str(config_def.text)
                item_method = getattr(tk_item, item_method_name)
                options = dict()
                options.update(self.reference.resolve(config_def.attrib))
                item_method(**options)
        if hasattr(tk_item, 'build'): # Custom Wigets use a Build method
            tk_item.build(item_def, self.reference)
        pass

    def set_appearance(self, tk_item: TkItem, item_def: ET.Element):
        '''Set the Widget options defined in the Appearance section of the
            widget's XML definition.
        Arguments:
            tk_item {TkItem} -- The widget (or window) instance.
            item_def {ET.Element} -- The Widget/Window XML Element definition
        '''
        # Question Should I keep tha appearance Element?
        options = dict()
        appearance = item_def.find('Appearance')
        if appearance is not None:
            options.update(self.reference.resolve(appearance.attrib))
            tk_item.configure(**options)
        pass

    def grid_config(self, tk_item: TkItem, item_def: ET.Element):
        '''Set the Widget's grid row and column options defined in the
            GridConfigure section of the widget's XML definition.
        Arguments:
            tk_item {TkItem} -- The widget (or window) instance.
            item_def {ET.Element} -- The Widget/Window XML Element definition
        '''
        grid_def = item_def.find('GridConfigure')
        if grid_def is not None:
            for column_setting in grid_def.findall('ColumnConfigure'):
                column_options = self.reference.resolve(column_setting.attrib)
                column_index = int(column_options.pop('column'))
                tk_item.columnconfigure(column_index, column_options)
            for row_setting in grid_def.findall('RowConfigure'):
                row_options = self.reference.resolve(row_setting.attrib)
                row_index = row_options.pop('row')
                tk_item.rowconfigure(row_index, row_options)
        pass

    def set_fullscreen(self, window: tk.Wm, settings: ET.Element):
        '''Set or Unset window full screen according to the XML setting.
        Arguments:
            window {tk.Wm} -- The window instance.
            settings {ET.Element} -- The Window Settings XML Element.
        '''
        fullscreen = settings.find('Fullscreen')
        if fullscreen:
            if 'true' in str(fullscreen.text):
                window.attributes('-fullscreen', True)
            elif 'false' in str(fullscreen.text):
                window.attributes('-fullscreen', False)
        pass

    def set_window_dimensions(self, window: tk.Wm, geometry: ET.Element):
        '''Set window size and shape according to the XML setting.
        Arguments:
            window {tk.Wm} -- The window instance.
            geometry {ET.Element} -- The Window Geometry XML Element.
        '''
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
                dimensions[dim] = int(self.reference.resolve(dimension))
            else:
                dimensions[dim] = int(current_size.group(dim))
        dimension_str = geometry_str.format(**dimensions)
        window.geometry(dimension_str)

    def stacking_adjustment(self, window: tk.Wm, geometry: ET.Element):
        '''Set window arangement (in front of or behind other windows).
        Arguments:
            window {tk.Wm} -- The window instance.
            geometry {ET.Element} -- The Window Geometry XML Element.
        '''
        stacking_group = geometry.find('Stacking')
        if stacking_group:
            for stacking_element in stacking_group.iter():
                stacking_name = stacking_element.tag
                if hasattr(tk.Tk, stacking_name):
                    stack_method = getattr(window, stacking_name)
                    stack_window = self.reference.resolve(str(stacking_element.text))
                    stack_method(stack_window)
        pass

    def set_window_geometry(self, window: tk.Wm, settings: ET.Element):
        '''Apply window geometry settings given in the XML element.
        Arguments:
            window {tk.Wm} -- The window instance.
            settings {ET.Element} -- The Window Settings XML Element.
        '''
        geometry = settings.find('Geometry')
        if geometry is not None:
            self.set_window_dimensions(window, geometry)
            self.stacking_adjustment(window, geometry)
        else:
            self.set_fullscreen(window, settings)
        pass

    def set_icon_state(self, window: tk.Wm, settings: ET.Element):
        '''Set the window state as given in the XML element. One of:
                normal: Open
                iconify: Minimized
                withdrawn: Hidden
        Arguments:
            window {tk.Wm} -- The window instance.
            settings {ET.Element} -- The Window Settings XML Element.
        '''
        newstate = settings.findtext(r'.//state')
        if newstate:
            window.state(newstate)
        pass

    def configure_window(self, window_def):
        '''Apply window settings settings given in the XML element.
        Arguments:
            window_def {ET.Element} -- The Window Definition XML Element.
        '''
        name = window_def.attrib['name']
        window = self.reference.lookup_item('Window', name)
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
        '''Apply window geometry settings given in the XML element.
        Arguments:
            widget {tk.Widget} -- The widget instance.
            settings {ET.Element} -- The widget Settings XML Element.
        '''
        options = dict()
        geometry = settings.find('Geometry')
        padding = geometry.find('Padding')
        if padding is not None:
            options.update(self.reference.resolve(padding.attrib))
        placement = geometry[0]
        options.update(self.reference.resolve(placement.attrib))
        if 'Grid' in placement.tag:
            widget.grid(**options)
        elif 'Pack' in placement.tag:
            widget.pack(**options)
        pass

    def configure_widgets(self):
        '''Apply all widget settings settings given in the GUI XML file.
        '''
        for widget_def in self.definition.findall(r'.//WidgetSet/*'):
            name = widget_def.attrib['name']
            widget = self.reference.lookup_item('Widget', name)
            self.configure_item(widget, widget_def)
            widget_settings = widget_def.find('Settings')
            self.set_appearance(widget, widget_settings)
            self.grid_config(widget, widget_settings)
            self.set_widget_geometry(widget, widget_settings)

    def update_variable(self, variable_name: str, update_method='from_data'):
        '''Synchronize a TK variable with its corresponding application data.
        Arguments:
            variable_name {str} -- The name of the TK variable.
        Keyword Arguments:
            update_method {str} -- Whether to copy the current values from the
                application data to the variable or from the variable to the
                application data. One of:
                     from_data
                     to_data
                     (default: {'from_data'})
        '''
        variable = self.reference.lookup_item('Variable', variable_name)
        data_name = self.data_link.get(variable_name)
        if data_name:
            if update_method in 'from_data':
                data_item = self.reference.lookup_item('Data', data_name)
                try:
                    data_value = data_item.value
                except AttributeError:
                    data_value = data_item
                variable.set(data_value)
            if update_method in 'to_data':
                data_value = variable.get()
                self.reference.set_item('Data', data_name, data_value)
        pass

    def update_data(self):
        '''Copy all TK variable values to their corresponding application
            data item.
        '''
        for variable_name in self.data_link:
            self.update_variable(variable_name, 'to_data')
        pass

    def update_and_run(self, command: Callable, *args, **kwargs):
        '''A helper partial that forces a call to update_data before running
            command. *args, **kwargs arr passed on unmodified as arguments to
            command.
        Arguments:
            command {Callable} -- The function to be called after updating the
                variables.
        '''
        self.update_data()
        command(*args, **kwargs)


def main():
    '''Test methods and definitions.
    '''
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
