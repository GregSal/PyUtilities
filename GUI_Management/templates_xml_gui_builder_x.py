'''
Created on Feb 23 2019

@author: Greg Salomons
Test ground for constructing GUI
'''
from typing import Union, TypeVar, List, Dict, Tuple, Callable, Any
from pathlib import Path
from collections import OrderedDict, namedtuple
from functools import partial
import xml.etree.ElementTree as ET
import re

import tkinter as tk
import tkinter.font as tkFont
import tkinter.ttk as ttk
from tkinter import messagebox

# Set the path to the Utilities Package.
from __init__ import add_path
add_path('utilities_path')
add_path('variable_path')
add_path('templates_path')


import file_select_window
import file_utilities
import templates
from file_utilities import set_base_dir, FileTypes, PathInput
from data_utilities import select_data, true_iterable
from spreadsheet_tools import load_reference_table
from custom_variable_sets import StringV, StrPathV, PathV, CustomVariableSet
from manage_template_lists import load_template_references


VariableDef = namedtuple('VariableDef', ['name', 'variable_type', 'data_ref'])
CommandDef = namedtuple('CommandDef', ['name', 'function', 'args', 'kwargs'])
WidgetDef = namedtuple('WidgetDef', ['name', 'widget_type', 'parent'])
StringValue = Union[tk.StringVar, str]
Definition = Dict[str, Dict[str, Any]]
Widgets = Union[List[WidgetDef], tk.Toplevel]
ObjectDef = Union[Callable,type]
ArgType = TypeVar('ArgType', List[Any], Dict[str, Any])


class TemplateSelectionsSet(CustomVariableSet):
    template_directory = set_base_dir(
            r'Work\Structure Dictionary\Template Spreadsheets')
    variable_definitions = [
        {
            'name': 'spreadsheet_directory',
            'variable_type': StrPathV,
            'file_types':'directory',
            'default': template_directory,
            'required': False
        },
        {
            'name': 'output_directory',
            'variable_type': StrPathV,
            'file_types':'directory',
            'default': r'Work\Structure Dictionary\Template XML Files',
            'required': False
        },
        {
            'name': 'structures_file',
            'variable_type': PathV,
            'file_types':'Excel Files',
            'default': template_directory / 'Structure Lookup.xlsx',
            'required': False
        },
        {
            'name': 'structures_pickle',
            'variable_type': PathV,
            'file_types':'Pickle File',
            'default': template_directory / 'StructureData.pkl',
            'required': False
        },
        {
            'name': 'template_list_file',
            'variable_type': PathV,
            'file_types':'Excel Files',
            'default': template_directory / 'Template List.xlsx',
            'required': False
        },
        {
            'name': 'template_pickle',
            'variable_type': PathV,
            'file_types':'Pickle File',
            'default': template_directory / 'TemplateData.pkl',
            'required': False
        },
        {
            'name': 'selected_templates',
            'variable_type': StringV,
            'default': '',
            'required': False
        }
        ]

class reference_tracker():
    token = '::'
    expr = '^[{id_set}]{token}(.*)$'
    module_lookup = {'tk': tk, 'ttk': ttk,
                     'fg': file_select_window,
                     'tp': templates}

    def __init__(self, *args, **kwargs):
        self.lookup_groups = dict()
        self.id_list = list()

    def add_lookup_group(self, identifier: str, lookup: OrderedDict = None):
        id = identifier[0] # Single character identifiers only
        if lookup is None:
            lookup = OrderedDict()
        self.lookup_groups[id] = lookup
        self.id_list.append(id)
        self.build_rx()

    def build_rx(self):
        specs = dict(token=self.token,
                     id_set=''.join(self.id_list)
                     )
        full_expression = self.expr.format(specs)
        self.rx = re.compile(expr)

    def add_item(self, identifier: str, name: str, item: Any):
        id = identifier[0]
        self.lookup_groups[id][name] = item

    def item_lookup(self, item_reference: str):
        matched = self.rx.search(item_reference)
        if matched:
            group_id = matched.group(1)
            item_name = matched.group(2)
            return self.lookup_groups[group_id][item_name]
        return item_reference

    def lookup_references(self, ref_set):
        updated_references = list()
        for value in ref_set:
            updated_value = self.item_lookup(value)
            updated_references.append(updated_value)
        return updated_references
######
# FIXME complete get_attribute
#####
    def get_attribute(self, atr_str, obj=None):
        if '.' in atr_str:
            ref_set = atr_str.split('.',1)
            obj_str, sub_atr_str = self.lookup_references(ref_set)
        else:
            sub_atr_str = atr_str
            obj_str = atr_str
        if obj:
            obj_atr = get_attribute(sub_obj_str, obj)
        else:
            getattr(self.__module__, obj_str, obj_str)
            if '.' in atr_str:
                sub_obj_str, new_atr_str = update_args(atr_str.split('.',1))

                return get_atribute(new_atr_str, sub_obj)
            return getattr(obj, atr_str)

            obj = module_lookup.get(obj_str, obj_str)
            return get_atribute(new_atr_str, obj)
        return atr_str



#####
# FIXME build reference_tracker object
####
widget_lookup = OrderedDict()
variable_lookup = OrderedDict()
command_lookup = OrderedDict()
data_set = TemplateSelectionsSet()




########
# FIXME convert to reference tracker
#############
def update_defs(reference_set, resolve_objects=False)->ArgType:
    def get_atribute(atr_str, obj=None):
        if obj:
            if '.' in atr_str:
                sub_obj_str, new_atr_str = update_args(atr_str.split('.',1))
                sub_obj = getattr(obj, sub_obj_str)
                return get_atribute(new_atr_str, sub_obj)
            return getattr(obj, atr_str)
        if '.' in atr_str:
            obj_str, new_atr_str = update_args(atr_str.split('.',1))
            obj = module_lookup.get(obj_str, obj_str)
            return get_atribute(new_atr_str, obj)
        return atr_str

    def value_lookup(value):
        value_str = str(value)
        value_name = value_str[3:]
        if value_str.startswith('W::'):
            use_value = widget_lookup[value_name]
        elif value_str.startswith('V::'):
            use_value = variable_lookup[value_name]
        elif value_str.startswith('D::'):
            use_value = data_set[value_name]
        elif value_str.startswith('C::'):
            use_value = command_lookup[value_name]
        else:
            use_value = value
        return use_value

    def update_args(arg_set):
        updated_args = list()
        for value in arg_set:
            use_value = value_lookup(value)
            updated_args.append(use_value)
        return updated_args

    def update_kwargs(kwarg_set):
        updated_kwargs = dict()
        for key_word, value in kwarg_set.items():
            use_value = value_lookup(value)
            updated_kwargs[key_word] = use_value
        return updated_kwargs

    updated_kwargs = dict()
    updated_args = list()
    try:
        updated_references = update_kwargs(reference_set)
    except AttributeError:
        updated_references = update_args(arg_set)
    if true_iterable(arg_set) and len(arg_set) > 1:
        return update_args(arg_set)
    elif arg_set:
        if resolve_objects:
            return get_atribute(arg_set[0])
        else:
            return update_args(arg_set)[0]
    elif kwarg_set:
        return update_kwargs(kwarg_set)
    return None


def get_class(object_def: ET.Element, class_lookup: str)->ObjectDef:
    object_str = object_def.findtext(class_lookup)
    return update_defs(object_str, resolve_objects=True)


def initialize_widgets(gui_definition: ET.Element):
    def method_name(gui_definition: ET.Element, name: str)->tk.Widget:
        parent_search = './/*[@name="{}"]../..'.format(name)
        parent_name = gui_definition.find(parent_search).attrib['name']
        parent = widget_lookup[parent_name]
        return parent

    for widget in gui_definition.findall(r'.//WidgetSet/*'):
        name = widget.attrib['name']
        parent = method_name(gui_definition, name)
        widget_class = get_class(widget, 'widget_class')
        new_widget = widget_class(name=name, master=parent)
        widget_lookup[name] = new_widget


def initialize_variables(gui_definition: ET.Element):
    def set_initial_value(variable: ET.Element, new_variable: tk.Variable):
        data_name = variable.findtext('data_reference')
        if data_name is not None:
            try:
                initial_value = data_set[data_name].value
            except AttributeError:
                initial_value = data_set[data_name]
            new_variable.set(initial_value)
        pass

    for variable in gui_definition.findall('VariableSet/*'):
        name = variable.attrib['name']
        variable_class = get_class(variable, 'variable_class')
        new_variable = variable_class(name=name)
        set_initial_value(variable, new_variable)
        variable_lookup[name] = new_variable


def initialize_commands(gui_definition: ET.Element):
    def get_positional_arguments(command: ET.Element)->List[Any]:
        arg_set = [arg.text for arg in command.findall('PositionalArgs/*')]
        args = update_defs(*arg_set)
        if args is None:
            args = []
        return args

    def get_keyword_arguments(command)->Dict[str, Any]:
        keyword_args = command.find('KeywordArgs')
        if keyword_args is not None:
            kwargs = update_defs(**keyword_args.attrib)
            if kwargs is None:
                 kwargs = dict()
        else:
            kwargs = dict()
        return kwargs

    for command in gui_definition.findall('CommandSet/*'):
        name = command.attrib['name']
        function = get_class(command, 'function')
        args = get_positional_arguments(command)
        kwargs = get_keyword_arguments(command)
        command_callable = partial(function, *args, **kwargs)
        command_lookup[name] = command_callable
    pass


def generic_configuration(widget: tk.Wm, widget_def: ET.Element):
    configuration = widget_def.find('Configure')
    if configuration is not None:
        options = dict()
        options.update(update_defs(**configuration.attrib))
        widget.configure(**options)
        for config_def in configuration.findall('Set'):
            method_name = str(config_def.text)
            method = getattr(widget, method_name)
            options = dict()
            options.update(update_defs(**config_def.attrib))
            method(**options)
    pass


def set_appearance(widget, widget_def):
    options = dict()
    appearance = widget_def.find('Appearance')
    if appearance is not None:
        options.update(update_defs(**appearance.attrib))
        widget.configure(**options)
    pass


def grid_config(widget: tk.Widget, widget_def: ET.Element):
    grid_configure_def = widget_def.find('GridConfigure')
    if grid_configure_def is not None:
        for column_setting in grid_configure_def.findall('ColumnConfigure'):
            column_options = update_defs(**column_setting.attrib)
            column_index = int(column_options.pop('column'))
            widget.columnconfigure(column_index, column_options)
        for row_setting in grid_configure_def.findall('RowConfigure'):
            row_options = update_defs(**row_setting.attrib)
            row_index = row_options.pop('row')
            widget.rowconfigure(row_index, row_options)
    pass


def set_widget_geometry(widget: tk.Widget, widget_settings: ET.Element):
    geometry = widget_settings.find('Geometry')
    if geometry is not None:
        options = dict()
        padding = geometry.find('Padding')
        if padding is not None:
            options.update(update_defs(**padding.attrib))
        placement = geometry.find('Placement/*')
        if placement is not None:
            options.update(update_defs(**placement.attrib))
            if 'Grid' in placement.tag:
                widget.grid(**options)
            elif 'Pack' in placement.tag:
                widget.pak(**options)
    pass


def set_window_geometry(window: tk.Wm, window_settings: ET.Element):
    def parsegeometry(geometry: str)->Tuple[int]:
        m = re.match("(\d+)x(\d+)([-+]\d+)([-+]\d+)", geometry)
        if not m:
            raise ValueError("failed to parse geometry string")
        return map(int, m.groups())

    def get_dimension(geometry, current_position, dimension_name):
        dimension_index = {'Width':0, 'Height': 1,
                           'Xposition': 2, 'Yposition': 3}
        dimension = update_defs(geometry.findtext(dimension_name))
        if not dimension:
            index = dimension_index[dimension_name]
            dimension = current_position[index]
        return int(dimension)

    geometry = window_settings.find('Geometry')
    if geometry is not None:
        current_position = list(parsegeometry(window.geometry()))
        width = get_dimension(geometry, current_position,
                              'Width')
        height = get_dimension(geometry, current_position,
                               'Height')
        x_position = get_dimension(geometry, current_position,
                                   'Xposition')
        y_position = get_dimension(geometry, current_position,
                                   'Yposition')
        geometry_str = '{:d}x{:d}{:+d}{:+d}'.format(width, height,
                                                    x_position, y_position)
        window.geometry(geometry_str)
    pass


def configure_window(window: tk.Wm, window_def: ET.Element):
    window_settings = window_def.find('Settings')
    if window_settings is not None:
        title_text = window_settings.findtext('title')
        if title_text:
            window.title = title_text
        set_appearance(window, window_settings)
        set_window_geometry(window, window_settings)
        grid_config(window, window_settings)
    generic_configuration(window, window_def)


def configure_widgets(gui_definition):
    for widget_def in gui_definition.findall(r'.//WidgetSet/*'):
        name = widget_def.attrib['name']
        widget = widget_lookup[name]
        widget_settings = widget_def.find('Settings')
        if widget_settings is not None:
            set_appearance(widget, widget_settings)
            set_widget_geometry(widget, widget_settings)
            grid_config(widget, widget_settings)
        generic_configuration(widget, widget_def)



xml_file = Path(r'.\FileSelectGUI.xml')
xml_tree = ET.parse(str(xml_file))
gui_definition = xml_tree.getroot()
root_element = gui_definition.find('RootWindow')
root = tk.Tk()
widget_lookup['root'] = root

initialize_widgets(gui_definition)
initialize_variables(gui_definition)
initialize_commands(gui_definition)

root = widget_lookup['root']
configure_window(root, root_element)
configure_widgets(gui_definition)

root = widget_lookup['root']
root.mainloop()


class GuiManager():
    def __init_(self, gui_definition: PathInput):
        self.variable_lookup = OrderedDict()
        self.widget_lookup = OrderedDict()
        self.command_lookup = OrderedDict()
        self.update_list = OrderedDict()
        xml_tree = ET.parse(str(gui_definition))
        self.gui_definition = xml_tree.getroot()


    def configure_widget(self,widget_def):
        widget_name = widget_def.get('name')
        widget = self.widget_lookup[widget_name]
        widget_configure = widget_def.find('Configure')
        if widget_configure:
            options = self.update_kwargs(**widget_configure.attrib)
            widget.configure(**options)
        pass

    def configure_window(self, window_def):

        def stacking_adjustment():
            stacking_group = window_def.find(Stacking)
            for stacking_element in stacking_group.iter():
                stacking_name = stacking_element.tag
                if hasattr(tk.Tk, stacking_name):
                    stack_method = getattr(tk.Tk, stacking_name)
                    stack_window = self.value_lookup(str(stack_type.text))
                    widget.stack_method(stack_window)
            pass

        def set_fullscreen():
            root_fullscreen = window_def.find('Fullscreen')
            if root_fullscreen:
                if 'true' in str(root_fullscreen.text):
                    widget.attributes('-fullscreen', True)
            pass

        def window_geometry():
            geometry = dict()
            geometry_template = ('{width:d}x{height:d}'
                                 '{x_pos:+d}{x_pos:+d}')
            geometry_group = window_def.find(Geometry)
            if geometry_group:
                geometry['height'] = geometry_group.findtext('.//Height')
                geometry['width'] = geometry_group.findtext('.//Width')
                geometry['x_pos'] = geometry_group.findtext('.//Xposition')
                geometry['y_pos'] = geometry_group.findtext('.//Yposition')
                if all(geometry.values()):
                    geometry_str = geometry_template.format(geometry)
                    widget.geometry(geometry_str)
                else:
                    widget.configure(height=geometry['height'],
                                     width=geometry['width'])
            pass

        def set_icon_state():
            newstate = window_def.findtext(r'.//state')
            if newstate:
                widget.state(newstate)
            pass

        main_gui.title('Test GUI') # FIXME Make title into generic window method




    def make_root():
        root = tk.Tk()
        self.widget_lookup['root'] = root
        root_widget = self.gui_definition.find('RootGUI')
        configure_window(root, root_widget)

        make_exit_button(root)
        # root.update()
        return root
        self.widget_lookup[top_name] = top_window
        if data_set:
            self.data_set = data_set
        else:
            self.data_set = dict()
        self.add_widgets(widget_set, variable_set, command_set)

    def add_widgets(self, widget_set: Widgets,
                 variable_set: List[VariableDef] = None,
                 command_set: List[CommandDef] = None):
        if widget_set:
            self.initialize_widgets(widget_set)
        if variable_set:
            self.initialize_variables(variable_set)
        if command_set:
            self.initialize_commands(command_set)
        pass

    def initialize_widgets(self, widget_set: List[WidgetDef]):
        '''parent must come before child in list
        '''
        for widget in widget_set:
            if 'top' in widget.parent:
                parent_name = ''
            else:
                parent_name = widget.parent + '.'
            # full_name = parent_name + widget.name
            full_name = widget.name
            parent = self.widget_lookup[widget.parent]
            self.widget_lookup[full_name] = widget.widget_type(master=parent)

    def initialize_variables(self, variable_set: List[VariableDef]):
        for variable_def in variable_set:
            variable = variable_def.variable_type()
            variable_name = variable_def.name
            data_name = variable_def.data_ref
            if data_name:
                try:
                    initial_value = self.data_set[data_name].value
                except AttributeError:
                    initial_value = self.data_set[data_name]
                variable.set(initial_value)
                self.update_list[variable_name] = data_name
            self.variable_lookup[variable_name] = variable

    def value_lookup(self, value):
        value_str = str(value)
        value_name = value_str[3:]
        if value_str.startswith('W::'):
            use_value = self.widget_lookup[value_name]
        elif value_str.startswith('V::'):
            use_value = self.variable_lookup[value_name]
        elif value_str.startswith('D::'):
            use_value = self.data_set[value_name]
        elif value_str.startswith('C::'):
            use_value = self.command_lookup[value_name]
        else:
            use_value = value
        return use_value

    def update_kwargs(self, kwarg_set: Dict[str, Any])->Dict[str, Any]:
        updated_kwargs = dict()
        if kwarg_set:
            for key_word, value in kwarg_set.items():
                use_value = self.value_lookup(value)
                updated_kwargs[key_word] = use_value
        return updated_kwargs

    def update_args(self, arg_set: tuple):
        updated_args = list()
        if arg_set:
            for value in arg_set:
                use_value = self.value_lookup(value)
                updated_args.append(use_value)
        return updated_args



    def define_widgets(self, widget_definitions: Definition,
                       widget_appearance: Definition):
        widget_name_list = set(widget_definitions.keys())
        widget_name_list.update(set(widget_appearance.keys()))
        for widget_name in widget_name_list:
            widget = self.widget_lookup[widget_name]
            widget_settings = dict()
            definition = widget_definitions.get(widget_name, dict())
            appearance = widget_appearance.get(widget_name, dict())
            widget_settings.update(appearance)
            widget_settings.update(definition)
            parameter_set = self.update_kwargs(widget_settings)
            widget.config(**parameter_set)

    def construct_gui(self, widget_placement: Definition):

        def build_widget(widget: tk.Widget, width=None,
                         layout_method: str = None,
                         **build_instructions):
            if width:
                widget.configure(width=width)
            if 'grid' in layout_method:
                widget.grid(**build_instructions)
            elif 'pack' in layout_method:
                widget.pack(**build_instructions)
            else:
                raise ValueError('layout_method must be "pack" or "grid"')
        for widget_name, build_instructions in widget_placement.items():
            widget = self.widget_lookup[widget_name]
            if hasattr(widget, 'build'):
                widget.build(**build_instructions)
            else:
                build_widget(widget, **build_instructions)


def make_root():
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.configure(background='white')
    make_exit_button(root)
    # root.update()
    return root


def build_top(root: tk.Tk)->tk.Tk:
    '''Generate a top level test window with an exit button in the background.
    Arguments:
        root: {tk.Tk} -- The primary GUI object.
    Returns:
        The main GUI widget.
    '''
    # Define TopLevel geometry as 1024x768, centered on the screen
    scr_w = root.winfo_screenwidth()
    scr_h = root.winfo_screenheight()
    workwindow = (str(1024) + "x" + str(768)+ "+"
                  +str(int((scr_w-1024)/2)) + "+" +str(int((scr_h-768)/2)))
    main_gui = tk.Toplevel(root)
    main_gui.configure(bg='light blue')
    main_gui.geometry(workwindow)
    main_gui.title('Test GUI')
    main_gui.rowconfigure(0, weight=1)
    main_gui.columnconfigure(0, weight=1)
    size_grip = ttk.Sizegrip(main_gui)
    size_grip.grid(row=3, column=3)
    main_gui.lift(root)
    return main_gui


def print_selection():
        select_list = [str(item) for item in template_selector.selection()]
        select_str = '\n'.join(select_list)
        messagebox.showinfo('Selected Templates', select_str)


def update_selection(event, variable: StringValue):
        select_list = [str(item) for item in event.widget.selection()]
        select_str = '\n'.join(select_list)
        variable.set(select_str)


def print_select(event):
        selected = str(event.widget.focus())
        messagebox.showinfo('Selected File', selected)


def file_select(event):
        selected_file = event.widget.focus()
        file_templates = event.widget.get_children(item=selected_file)
        select_list = event.widget.selection()
        a = (template in select_list for template in file_templates)
        select_str = '\n'.join([str(item) for item in file_templates])
        heading = '{} Selected:'.format(str(selected_file))
        #messagebox.showinfo(heading, select_str)
        if all(a):
            event.widget.selection_remove(*file_templates)
            event.widget.item(selected_file, open=True)
            #messagebox.showinfo(heading, select_str)
        else:
            event.widget.selection_add(*file_templates)
            event.widget.item(selected_file, open=True)
            #messagebox.showinfo(heading, select_str)
        #


def insert_template_items(template_selector, workbooks, show_vars):
    '''Add the template items to the workbook.
    '''
    #top_level = template_selector.insert('', 0, text='Structure Templates')
    template_ref = dict()
    for workbook, sheets in workbooks:
        workbook_str = workbook.split('.', 1)[0]
        file_ref = template_selector.insert('', 'end', workbook_str,
                                            text=workbook_str,
                                            open=True,
                                            tags=('File',))
        template_ref[workbook_str] = file_ref
        for template_data in sheets.itertuples():
            name = template_data.TemplateID
            template_values = [getattr(template_data, item)
                               for item in show_vars]
            id = template_selector.insert(file_ref, 'end', name, text=name,
                                          values=template_values,
                                          tags=('Template',))
            template_ref[name] = id


def file_select_test():
    '''Test entry in top level window.
    '''
    projects_path = set_base_dir(sub_dir=r'Python\Projects')
    test_file_path = projects_path / r"Utilities\Testing\Test Data\Test table.xlsx"
    path_data = FileSelectionSet(template_file=test_file_path)
    variable_set = [
        VariableDef('template_filename', tk.StringVar, 'template_file'),
        VariableDef('template_dir', tk.StringVar, 'spreadsheet_directory')
        ]
    widget_set = [
        WidgetDef('fle_selector_group', ttk.Frame, 'top'),
        WidgetDef('template_select', FileSelectGUI, 'fle_selector_group'),
        WidgetDef('input_dir_select', FileSelectGUI, 'fle_selector_group'),
        WidgetDef('exit_button', ttk.Button, 'fle_selector_group'),
        WidgetDef('refresh_template_list', ttk.Button, 'fle_selector_group')
        ]
    command_set = [
        CommandDef('Exit',  tk.Tk.destroy, ('W::top',),{}),
        CommandDef('Show_File', message_window, (), {
            'window_text': 'File String',
            'variable': 'V::template_filename',
            'parent_window': 'W::fle_selector_group'
            })
        ]
    widget_definitions = {
        'template_select': dict(
            text='Test Template File Selection',
            title='Select File',
            path_variable='V::template_filename',
            type_selection=FileTypes('Excel Files'),
            starting_path=Path.cwd(),
            action='open',
            button_text='Browse'
            ),
        'input_dir_select': dict(
            text='Test Directory Selection',
            title='Select Directory',
            path_variable='V::template_dir',
            type_selection=FileTypes('directory'),
            starting_path=Path.cwd(),
            action='open',
            button_text='Browse'
            ),
        'exit_button': dict(
            text='Exit',
            command='C::Exit'
            ),
        'refresh_template_list': dict(
            text='Refresh Template List',
            command='C::Show_File'
            )
        }
    widget_appearance = {
        'template_select': dict(
            borderwidth=10,
            relief='groove',
            entry_cursor='xterm',
            entry_justify='left',
            entry_width=115,
            button_width=10
            ),
        'input_dir_select': dict(
            borderwidth=10,
            relief='groove',
            entry_cursor='xterm',
            entry_justify='left',
            entry_width=115,
            button_width=10
            ),
        'exit_button': dict(
            width=26
            ),
        'refresh_template_list': dict(
            width=26
            )
        }
    widget_placement = {
       'fle_selector_group': dict(
            layout_method='grid',
            padx=5, pady=5,
            column=0, row=0, sticky='nsew'
            ),
        'template_select': dict(
            layout_method='grid',
            padx=5, pady=5,
            column=0, row=0, sticky='nsew'
            ),
        'input_dir_select': dict(
            layout_method='grid',
            padx=5, pady=5,
            column=0, row=1, sticky='nsew'
            ),
        'refresh_template_list': dict(
            layout_method='grid',
            padx=5, pady=5,
            column=1, row=0
            ),
        'exit_button': dict(
            layout_method='grid',
            padx=5, pady=5,
            column=1, row=1
            )
        }

    root = make_root()
    main_gui = build_top(root)
    fle_selector_group=ttk.Frame(master=main_gui)
    test_window = GuiManager(main_gui,  data_set=path_data)
    test_window.add_widgets(widget_set, variable_set, command_set)
    test_window.define_widgets(widget_definitions, widget_appearance)
    test_window.construct_gui(widget_placement)
    show_message(button_parent=root, parent_window=main_gui,
                 button_text='show file string', window_text='File String',
                 variable=test_window.variable_lookup['template_filename'])
    root.iconify()
    #root.withdraw()
    root.mainloop()


def template_select_test():
    '''Test entry in top level window.
    '''
    widget_set = [
        WidgetDef('template_selector_group', ttk.Frame, 'top'),
        WidgetDef('template_selector', ttk.Treeview, 'template_selector_group'),
        WidgetDef('selector_scrollbar_h', ttk.Scrollbar, 'template_selector_group'),
        WidgetDef('selector_scrollbar_v', ttk.Scrollbar, 'template_selector_group'),
        WidgetDef('selection_button', ttk.Button, 'top')
        ]
    variable_set = [
        VariableDef('template_filename', tk.StringVar, None),
        VariableDef('template_dir', tk.StringVar, None),
        VariableDef('template_selection', tk.StringVar, None)
        ]
    command_set = [
        CommandDef('Exit',  tk.Tk.destroy, ('W::top',),{}),
        CommandDef('Template xview', ttk.Treeview.xview,
                   ('W::template_selector',), {}),
        CommandDef('Template yview', ttk.Treeview.yview,
                   ('W::template_selector',), {}),
        CommandDef('Template H Scroll', ttk.Scrollbar.set,
                   ('W::selector_scrollbar_h',), {}),
        CommandDef('Template V Scroll', ttk.Scrollbar.set,
                   ('W::selector_scrollbar_v',), {}),
        CommandDef('Show_File', message_window, (),
                   {'window_text': 'File String',
                    'variable': 'V::template_filename',
                    'parent_window': 'W::template_selector_group'
                    }),
        CommandDef('Show_Selected', message_window, (),
                   {'window_text': 'Selected Templates',
                    'variable': 'V::template_selection',
                    'parent_window': 'W::template_selector_group'
                    }),
        CommandDef('UpdateSelected', update_selection, (),
                   {'variable': 'V::template_selection'})
        ]
    widget_definitions = {
        'selector_scrollbar_h': dict(
            orient='horizontal',
            command='C::Template xview'
            ),
        'selector_scrollbar_v': dict(
            orient='vertical',
            command='C::Template yview'
            ),
        'template_selector': dict(
            xscrollcommand='C::Template H Scroll',
            yscrollcommand='C::Template V Scroll'
            ),
        'selection_button': dict(
            text='Show Selected',
            command='C::Show_Selected'
            )
        }

    widget_appearance = {
        'template_selector_group': dict(
            borderwidth=10,
            relief='groove',
            ),
        'selection_button': dict(
            width=26
            )
        }

    widget_placement = {
        'template_selector_group': dict(
            layout_method='grid',
            padx=0, pady=0,
            column=0, row=0, sticky='nsew'
            ),
        'template_selector': dict(
            layout_method='grid',
            padx=5, pady=5,
            column=0, row=0, sticky='nsew'
            ),
        'selector_scrollbar_h': dict(
            layout_method='grid',
            padx=0, pady=0,
            column=0, row=1, sticky='ew'
            ),
        'selector_scrollbar_v': dict(
            layout_method='grid',
            padx=0, pady=0,
            column=1, row=0, sticky='ns'
            ),
        'selection_button': dict(
            layout_method='grid',
            padx=10, pady=10,
            column=0, row=2
            )
        }


    root = make_root()
    main_gui = build_top(root)
    #root.withdraw()
    #root.iconify()

    # Add a window icon
    ico_pict = r'.\icons\DocumentApprovalt.png'
    root.iconphoto(root, tk.PhotoImage(file=ico_pict))

    main_gui.title('Template Selection')
    test_window = GuiManager(main_gui)
    test_window.add_widgets(widget_set, variable_set, command_set)
    test_window.define_widgets(widget_definitions, widget_appearance)

    template_selector_group = test_window.widget_lookup['template_selector_group']
    template_selector_group.columnconfigure(0, weight=1)
    template_selector_group.rowconfigure(0, weight=1)

    style = ttk.Style()
    style.theme_use('vista')
    normal_font = tkFont.Font(family='Calibri', size=11, weight='normal')
    button_font = tkFont.Font(family='Calibri', size=12, weight='bold')
    title_font = tkFont.Font(family='Tacoma', size=36, weight='bold')
    style.configure('TButton', font=button_font)
    style.configure('Treeview', font=normal_font)

    projects_path = set_base_dir(sub_dir=r'Python\Projects')
    icon_folder = r'EclipseRelated\EclipseTemplates\ManageStructuresTemplates\icons'
    icon_path = projects_path / icon_folder
    file_icon = icon_path / 'Box2.png'
    template_icon = icon_path / 'Blueprint2.png'
    file_image = tk.PhotoImage(file=file_icon)
    template_image = tk.PhotoImage(file=template_icon)


    test_data = TemplateData()
    active_templates = test_data.get_template_data()
    workbooks = test_data.get_workbook_data()
    vars = ['workbook_name', 'sheet_name', 'TemplateID', 'TemplateCategory',
            'TreatmentSite', 'modification_date', 'Diagnosis', 'Author',
            'template_file_name', 'Status']

    columns = ['TemplateID', 'TemplateCategory', 'TreatmentSite', 'Diagnosis',
               'modification_date', 'Author', 'Status',
               'Number_of_Structures', 'sheet_name', 'Description',
               'TemplateType', 'ApprovalStatus', 'Columns',
               'template_file_name']
    displaycolumns = ['TemplateID', 'TemplateCategory', 'TreatmentSite',
                      'Diagnosis', 'modification_date', 'Status']

    column_def = dict(
        workbook_name = {'anchor': 'w', 'minwidth': 95, 'stretch':'TRUE', 'width': 234},
        TemplateID = {'anchor': 'w', 'minwidth': 11, 'stretch':'TRUE', 'width': 102},
        TemplateCategory = {'minwidth': 16, 'stretch':'TRUE', 'width': 42},
        TreatmentSite = {'anchor': 'w', 'minwidth': 21, 'stretch':'TRUE', 'width': 102},
        Diagnosis = {'anchor': 'w', 'minwidth': 74, 'stretch':'TRUE', 'width': 150},
        modification_date = {'anchor': 'w', 'minwidth': 69, 'stretch':'TRUE', 'width': 96},
        Author = {'minwidth': 21, 'stretch':'TRUE', 'width': 24},
        Status = {'minwidth': 32, 'stretch':'TRUE', 'width': 48},
        Number_of_Structures = {'minwidth': 5, 'stretch':'TRUE', 'width': 12},
        sheet_name = {'anchor': 'w', 'minwidth': 11, 'stretch':'TRUE', 'width': 132},
        Description = {'anchor': 'w', 'minwidth': 16, 'stretch':'TRUE', 'width': 1308},
        TemplateType = {'minwidth': 28, 'stretch':'TRUE', 'width': 54},
        ApprovalStatus = {'minwidth': 42, 'stretch':'TRUE', 'width': 60},
        Columns = {'minwidth': 5, 'stretch':'TRUE', 'width': 6},
        template_file_name = {'anchor': 'w', 'minwidth': 0, 'stretch':'TRUE', 'width': 156}
        )
    heading_def = dict(
        workbook_name = { 'text': 'Structure Templates '},
        sheet_name = { 'text': 'Worksheet '},
        TemplateID = { 'text': 'Template '},
        TemplateCategory = { 'text': 'Category '},
        TreatmentSite = { 'text': 'Site '},
        modification_date = { 'text': 'Modification Date '},
        Diagnosis = { 'text': 'Diagnosis '},
        Author = { 'text': 'Author '},
        template_file_name = { 'text': 'Template file name '},
        Status = { 'text': 'Status '},
        Number_of_Structures = { 'text': '# Structures '},
        Description = { 'text': 'Description '},
        TemplateType = { 'text': 'Template Type '},
        ApprovalStatus = { 'text': 'Approval Status '},
        Columns = { 'text': 'Columns '}
        )


    #test_vars = ['workbook_name', 'TemplateID', 'TemplateCategory']
    #test_show_vars = ['TemplateID', 'TemplateCategory']
    template_selector = test_window.widget_lookup['template_selector']
    template_selector['columns'] = columns
    template_selector['displaycolumns'] = displaycolumns
    tree_opts = column_def.pop('workbook_name')
    column_def['#0'] = tree_opts
    for column, options in column_def.items():
        template_selector.column(column, **options)
    tree_opts = heading_def.pop('workbook_name')
    heading_def['#0'] = tree_opts
    for column, options in heading_def.items():
        template_selector.heading(column, **options)
    insert_template_items(template_selector, workbooks, columns)
    template_selector.tag_configure('File', foreground='blue',
                                    background='light grey', image=file_image)
    template_selector.tag_configure('Template', image=template_image)
    template_selector.tag_bind('File', '<Double-ButtonRelease-1>', callback=file_select)  # the item clicked can be found via tree.focus()
    template_update = test_window.command_lookup['UpdateSelected']
    template_selector.bind('<<TreeviewSelect>>', template_update, add='+')

    test_window.construct_gui(widget_placement)

    show_message(button_parent=root, parent_window=main_gui,
                 button_text='show file string', window_text='File String',
                 variable=test_window.variable_lookup['template_filename'])
    root.iconify()
    #root.withdraw()
    root.mainloop()


#if __name__ == '__main__':
#    main()