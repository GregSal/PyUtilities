'''
Created on Feb 23 2019

@author: Greg Salomons
Test ground for constructing GUI
'''
from typing import Union, List, Dict, Tuple, Any
from pathlib import Path
from collections import OrderedDict, namedtuple
from functools import partial

import tkinter as tk
import tkinter.font as tkFont
import tkinter.ttk as ttk
from tkinter import messagebox

import sys
# utilities_path = r"C:\Users\Greg\OneDrive - Queen's University\Python\Projects\Utilities"
templates_path = Path.cwd() / r'..\EclipseRelated\EclipseTemplates\ManageStructuresTemplates'
templates_path_str = str(templates_path.resolve())
sys.path.append(templates_path_str)


from file_select_window import SelectFile
from file_utilities import set_base_dir, FileTypes, PathInput
from data_utilities import select_data
from spreadsheet_tools import load_reference_table
from custom_variable_sets import StrPathV, CustomVariableSet
from manage_template_lists import load_template_references


VariableDef = namedtuple('VariableDef', ['name', 'variable_type', 'data_ref'])
CommandDef = namedtuple('CommandDef', ['name', 'function', 'args', 'kwargs'])
WidgetDef = namedtuple('WidgetDef', ['name', 'widget_type', 'parent'])
StringValue = Union[tk.StringVar, str]
Definition = Dict[str, Dict[str, Any]]
Widgets = Union[List[WidgetDef], tk.Toplevel]

class FileSelectGUI(ttk.LabelFrame):
    entry_layout=dict(layout_method='grid', padx=10, pady=10, row=0, column=0)
    button_layout=dict(layout_method='grid', padx=10, pady=10, row=0, column=1)

    def __init__(self, master: tk.Tk, **options):
        super().__init__(master=master)
        self.browse_window = SelectFile(master=master)
        self.file_entry = ttk.Entry(master=self)
        self.browse_button = ttk.Button(text='Browse', master=self)

    def config(self, **options):
        reduced_options = self.entry_config(**options)
        reduced_options = self.browse_window.configure(**reduced_options)
        reduced_options = self.button_config(**reduced_options)
        super().config(**reduced_options)

    def entry_config(self, path_variable: tk.StringVar = None,
                     **options)->Dict[str, Any]:
        option_prefix = 'entry_'
        if not path_variable:
            path_variable = tk.StringVar()
        self.path_variable = path_variable
        entry_options = dict(textvariable=path_variable)
        unused_parameters = dict()
        for option_name, value in options.items():
            if option_name.startswith(option_prefix):
                option = option_name[len(option_prefix):]
                entry_options[option] = value
            else:
                unused_parameters[option_name] = value
        self.file_entry.configure(**entry_options)
        return unused_parameters

    def browse_command(self):
        '''Command for Browse Buttons.'''
        self.path_variable.set(self.browse_window.call_dialog())

    def button_config(self, **options)->Dict[str, Any]:
        option_prefix = 'button_'
        browse_command = self.browse_command
        browse_options = dict(text='Browse', width=10, command=browse_command)
        unused_parameters = dict()
        for option_name, value in options.items():
            if option_name.startswith(option_prefix):
                option = option_name[len(option_prefix):]
                browse_options[option] = value
            else:
                unused_parameters[option_name] = value
        self.browse_button.configure(**browse_options)
        return unused_parameters

    def build(self, **build_instructions):
        reduced_instructions = self.build_entry(**build_instructions)
        unused_parameters = self.build_button(**reduced_instructions)
        self.columnconfigure(0, weight=1)
        layout_method = unused_parameters.pop('layout_method', None)
        if 'pack' in layout_method:
            self.pack(**unused_parameters)
        else:
            self.grid(**unused_parameters)

    def build_entry(self, **build_instructions):
        option_prefix = 'entry_'
        entry_layout = self.entry_layout.copy()
        unused_parameters = dict()
        for option_name, value in build_instructions.items():
            if option_name.startswith(option_prefix):
                option = option_name[len(option_prefix):]
                entry_layout[option] = value
            else:
                unused_parameters[option_name] = value
        layout_method = entry_layout.pop('layout_method', None)
        if 'pack' in layout_method:
            self.file_entry.pack(**entry_layout)
        else:
            self.file_entry.grid(**entry_layout)
        return unused_parameters

    def build_button(self, **build_instructions):
        option_prefix = 'button_'
        button_layout = self.button_layout.copy()
        unused_parameters = dict()
        for option_name, value in build_instructions.items():
            if option_name.startswith(option_prefix):
                option = option_name[len(option_prefix):]
                button_layout[option] = value
            else:
                unused_parameters[option_name] = value
        layout_method = button_layout.pop('layout_method', None)
        if 'pack' in layout_method:
            self.browse_button.pack(**button_layout)
        else:
            self.browse_button.grid(**button_layout)
        return unused_parameters

    def get(self):
        return self.path_variable.get()

    def set(self, file_path: PathInput):
        return self.path_variable.set(str(file_path))


class GuiManager():
    def __init__(self, top_window: tk.Toplevel, top_name='top',
                 data_set: dict = None,
                 widget_set: Widgets = None,
                 variable_set: List[VariableDef] = None,
                 command_set: List[CommandDef] = None,
                 ):
        self.variable_lookup = OrderedDict()
        self.widget_lookup = OrderedDict()
        self.command_lookup = OrderedDict()
        self.update_list = OrderedDict()
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

    def initialize_commands(self, command_set: List[CommandDef]):
        for command_def in command_set:
            kwargs = self.update_kwargs(command_def.kwargs)
            args = self.update_args(command_def.args)
            command = partial(test_action, command_def.function, *args, **kwargs)
            self.command_lookup[command_def.name] = command
        pass

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

def test_action(action, *args, **kwargs):
    action.__call__(*args, **kwargs)


def make_exit_button(parent_window):
    exit_button = tk.Button(parent_window, text="Egress",
                            command=parent_window.destroy)
    exit_button.grid()


def show_message(button_parent: tk.Widget, parent_window: tk.Widget = None,
                 button_text='HIT ME', window_text='',
                 variable: StringValue = 'Nothing to say'):
    if not parent_window:
        parent_window = button_parent
    def show_file():
        '''An info widget that displays the selected file name.'''
        messagebox.showinfo(window_text, variable.get(), parent=parent_window)

    test_button = ttk.Button(master=button_parent, command=show_file,
                             text=button_text)
    test_button.grid()


def message_window(parent_window: tk.Widget, window_text: StringValue = '',
                   variable: StringValue = 'Nothing to say'):
    '''Display the sting message or variable content.'''
    if isinstance(variable, tk.StringVar):
        str_message = variable.get()
    else:
        str_message = str(variable)
    messagebox.showinfo(title=window_text, message=variable.get(),
                        parent=parent_window)

def exit(window: tk.Toplevel):
    messagebox.showinfo(title='Time to go', message='Goodbye', parent=window)
    tk.Tk.destroy, {'self': window}


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


class TemplateData():
    data_fields = ['TemplateID', 'TemplateCategory', 'TreatmentSite',
                   'workbook_name', 'sheet_name', 'modification_date',
                   'Number_of_Structures', 'Description', 'Diagnosis',
                   'Author', 'Columns', 'template_file_name', 'Status',
                   'TemplateType', 'ApprovalStatus']

    default_show_fields = ['workbook_name', 'TemplateID', 'TemplateCategory',
                           'TreatmentSite', 'modification_date',
                           'Description', 'Status']

    file_info_args = ('pickle_file_name', 'sub_dir')
    table_info_args = ('starting_cell', 'header')
    selections_args = ('unique_scans', 'select_columns', 'criteria_selection')

    default_references = dict(
        file_name='Template List.xlsx',
        pickle_file_name='TemplateData.pkl',
        sub_dir=r'Work\Structure Dictionary\Template Spreadsheets',
        sheet_name='templates',
        starting_cell='A1',
        header=1,
        unique_scans=['TemplateID'],
        select_columns=data_fields,
        criteria_selection={
#            'workbook_name': 'Basic Templates.xlsx',
            'Status': 'Active'
            }
        )
    def __init__(self, **kwargs):
        self.template_file_info = self.set_args(self.file_info_args, kwargs)
        self.template_table_info = self.set_args(self.table_info_args, kwargs)
        self.template_selections = self.set_args(self.selections_args, kwargs)
        self.template_data = self.get_template_data()

    def set_arg(self, arg: str, arguments: Dict[str, Any])->Any:
        '''Return the passed argument value or the default value.
        '''
        return arguments.get(arg, self.default_references[arg])

    def set_args(self, arg_list: Tuple[str],
                 arguments: Dict[str, Any])->Dict[str, Any]:
        args_dict = dict()
        for arg in arg_list:
            args_dict[arg] = self.set_arg(arg, arguments)
        return args_dict

    def get_template_data(self):
        template_data = load_template_references(**self.template_file_info)
        template_data = select_data(template_data, **self.template_selections)
        return template_data

    def get_workbook_data(self):
        return self.template_data.groupby('workbook_name')


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


class FileSelectionSet(CustomVariableSet):
    '''A CustomVariable set with two path variables:
            "test_string1"
            "test_integer"
    '''
    variable_definitions = [
        {
            'name': 'spreadsheet_directory',
            'variable_type': StrPathV,
            'file_types':'directory',
            'default': Path.cwd(),
            'required': False
            },
            {
            'name': 'template_file',
            'variable_type': StrPathV,
            'file_types':'Excel Files',
            'required': False
            }
         ]


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


def main():
    '''run current GUI test.
    '''
    #normal_font = tkFont.Font(family='Calibri', size=11, weight='normal')
    #button_font = tkFont.Font(family='Calibri', size=12, weight='bold')
    #title_font = tkFont.Font(family='Tacoma', size=36, weight='bold')
#    file_select_test()
    print('hi')
    template_select_test()

if __name__ == '__main__':
    main()
