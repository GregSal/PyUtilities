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

from template_config import TemplateSelectionsSet
from object_reference_management import ReferenceTracker, ReferenceSet, ObjectSet
import file_select_window
import file_utilities
import templates
from file_utilities import set_base_dir, FileTypes, PathInput
from data_utilities import select_data, true_iterable
from spreadsheet_tools import load_reference_table
from custom_variable_sets import StringV, StrPathV, PathV, CustomVariableSet
from manage_template_lists import load_template_references


ObjectDef = Union[Callable,type]
StringValue = Union[tk.StringVar, str]
TkItem = Union[tk.Widget, ttk.Widget, tk.Wm]
Definition = Dict[str, Dict[str, Any]]
ArgType = TypeVar('ArgType', List[Any], Dict[str, Any])


class GuiManager():
    identifier_list = ['Widget', 'Variable', 'Command', 'Xecute']
    data_set = TemplateSelectionsSet()
    module_lookup = [('M', {'tk': tk, 'ttk': ttk})]

    def __init_(self, data_set: CustomVariableSet, xml_file: Path):
        data_set = TemplateSelectionsSet()
        self.reference = ReferenceTracker(self.identifier_list, self.lookup_list)
        self.reference.add_lookup_group('D', data_set)
        self.definition = self.load_xml(xml_file)
        self.make_root()
        self.initialize_variables()
        self.initialize_widgets()
        self.initialize_commands()
        root_widget = self.definition.find('RootWindow')
        configure_window(root, root_widget)
        for window_def in self.definition.findall(r'.//Window'):
            self.configure_window(window_def)

    def load_xml(self, xml_file: Path):
        xml_tree = ET.parse(str(xml_file))
        return xml_tree.getroot

    def make_root(self):
        root = tk.Tk()
        self.reference.add_item('Widget', 'root', root)

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

    def call_item(self, group_id: str, item_name: str) -> Any:
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

    def add_reference(self, identifier: str, name: str, item: Any):
        '''Add a new item for reference.

        Arguments:
            identifier {str} -- A single character used to identify the
                reference group. Only the first character of the supplied
                string is uses as the identifier.
            name {str} -- The name used to reference the group item.
            item {Any} -- The object to be referenced
        '''
        self.reference.add_item(identifier, name, item)

    def get_class(self, object_def: ET.Element, class_lookup: str)->ObjectDef:
        object_str = object_def.findtext(class_lookup)
        return self.resolve(object_str)

    def get_parent(self, name: str)->tk.Widget:
        parent_search = './/*[@name="{}"]../..'.format(name)
        parent_name = self.definition.find(parent_search).attrib['name']
        parent = self.lookup_item('W', parent_name)
        return parent

    def initialize_variables(self):
        def get_initial_value(variable: ET.Elemente)->Any:
            data_name = variable.findtext('data_reference')
            if data_name is not None:
                data_item = self.lookup_item('D', data_name)
                try:
                    initial_value = data_item.value
                except AttributeError:
                    initial_value = data_item
            else:
                initial_value = None
            return initial_value

        for variable in self.definition.findall('VariableSet/*'):
            name = variable.attrib['name']
            variable_class = self.get_class(variable, 'variable_class')
            new_variable = variable_class(name=name)
            new_variable.set(get_initial_value(variable))
            self.add_reference('Variable', name, new_variable)

    def initialize_windows(self):
        for window_def in self.definition.findall(r'.//Window/*'):
            name = window_def.attrib['name']
            parent = self.get_parent(name)
            new_window = tk.Toplevel(name=name, master=parent)
            self.add_reference('Window', name, new_window)

    def initialize_widgets(self):
        for widget_def in self.definition.findall(r'.//WidgetSet/*'):
            name = widget_def.attrib['name']
            parent = self.get_parent(name)
            widget_class = get_class(widget_def, 'widget_class')
            new_widget = widget_class(name=name, master=parent)
            self.add_reference('Widget', name, new_widget)

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
            function = get_class(command, 'function')
            args = get_positional_arguments(command)
            kwargs = get_keyword_arguments(command)
            command_callable = partial(function, *args, **kwargs)
            self.add_reference('Command', name, command_callable)
            # The X:: reference indicates a reference to the output of the
            # C:: command reference ## Not yet implemented
            self.add_reference('Xecute', name, command_callable)
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
                widget.columnconfigure(column_index, column_options)
            for row_setting in grid_def.findall('RowConfigure'):
                row_options = self.resolve(row_setting.attrib)
                row_index = row_options.pop('row')
                widget.rowconfigure(row_index, row_options)
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
        for dim in geometry_list:
            dimension = geometry.findtext(dim)
            if dimension is not None:
                dimensions[dim] = self.resolve(dimension)
            else:
                dimensions[dim] = current_size.group(dim)
        dimension_str = geometry_str.format(**dimensions)
        window.geometry(dimension_str)

    def stacking_adjustment(self, window: tk.Wm, geometry: ET.Element):
        stacking_group = geometry.find('Stacking')
        for stacking_element in stacking_group.iter():
            stacking_name = stacking_element.tag
            if hasattr(tk.Tk, stacking_name):
                stack_method = getattr(tk.Tk, stacking_name)
                stack_window = self.resolve(str(stacking_element.text))
                stack_method(stack_window)
        pass

    def set_window_geometry(self, window: tk.Wm, geometry: ET.Element):
        geometry = window_settings.find('Geometry')
        if geometry is not None:
            self.set_window_dimensions(self, window, geometry)
            self.stacking_adjustment(self, window, geometry)
        else:
            self.set_fullscreen(window, geometry)
        pass

    def set_icon_state(self, window: tk.Wm, settings: ET.Element):
        newstate = window_def.findtext(r'.//state')
        if newstate:
            widget.state(newstate)
        pass

    def configure_window(self, window_def):
        name = window_def.attrib['name']
        window = self.lookup_item('Window', name)
        window_settings = window_def.find('Settings')
        if window_settings is not None:
            title_text = window_settings.findtext('title')
            if title_text:
                window.title = title_text
            self.set_appearance(window, window_settings)
            self.grid_config(window, window_settings)
            self.set_window_geometry(window, window_settings)
            self.set_icon_state(window, window_settings)
        self.configure_item(window, window_def)

    def set_widget_geometry(self, widget: tk.Widget, settings: ET.Element):
        geometry = settings.find('Geometry')
        if geometry is not None:
            options = dict()
            padding = geometry.find('Padding')
            if padding is not None:
                options.update(self.resolve(padding.attrib))
            placement = geometry.find('./1')
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
            widget_settings = widget_def.find('Settings')
            if widget_settings is not None:
                self.set_appearance(widget, widget_settings)
                self.grid_config(widget, widget_settings)
                self.set_widget_geometry(widget, widget_settings)
            self.configure_item(widget, widget_settings)


# Done To Here




gui_def_file = Path(r'.\FileSelectGUI.xml')
gui_def_file = Path(r'.\TestGUI.xml')
gui = GuiManager(gui_def_file)
gui.execute()




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
