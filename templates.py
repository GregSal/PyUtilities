'''
Created on Feb 23 2019

@author: Greg Salomons
Test ground for constructing GUI
'''
from typing import Union, List, Dict, Tuple, Any
from GUI_Construction import TemplateData
from GUI_Construction import GuiManager
from GUI_Construction import build_top
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


def template_test():
    '''Test entry in top level window.
    '''
    projects_path = set_base_dir(sub_dir=r'Python\Projects')
    test_file_path = projects_path / r"Utilities\Testing\Test Data\Test table.xlsx"
    path_data = FileSelectionSet(template_file=test_file_path)
    variable_set = [
        VariableDef('TemplateListFilename', tk.StringVar, 'template_file'),
        VariableDef('TemplateExcelDirectory', tk.StringVar, 'spreadsheet_directory'),
        VariableDef('SelectedTemplates', tk.StringVar, 'selected_templates'),
        VariableDef('XmlOutputDirectory', tk.StringVar, 'output_directory')
        ]
    widget_set = [
        WidgetDef('template_selector_group', ttk.Frame, 'top'),
        WidgetDef('template_selector', ttk.Treeview, 'template_selector_group'),
        WidgetDef('selector_scrollbar_h', ttk.Scrollbar, 'template_selector_group'),
        WidgetDef('selector_scrollbar_v', ttk.Scrollbar, 'template_selector_group'),
        WidgetDef('fle_selector_group', ttk.Frame, 'top'),
        WidgetDef('output_directory', FileSelectGUI, 'fle_selector_group'),
        WidgetDef('template_directory', FileSelectGUI, 'fle_selector_group'),
        WidgetDef('template_list_excel_file', FileSelectGUI, 'fle_selector_group'),
        WidgetDef('exit_button', ttk.Button, 'fle_selector_group'),
        WidgetDef('build_templates', ttk.Button, 'fle_selector_group'),
        WidgetDef('refresh_template_list', ttk.Button, 'fle_selector_group')
        ]
    command_set = [
        CommandDef('Template xview', ttk.Treeview.xview,
                   ('W::template_selector',), {}),
        CommandDef('Template yview', ttk.Treeview.yview,
                   ('W::template_selector',), {}),
        CommandDef('Template H Scroll', ttk.Scrollbar.set,
                   ('W::selector_scrollbar_h',), {}),
        CommandDef('Template V Scroll', ttk.Scrollbar.set,
                   ('W::selector_scrollbar_v',), {}),
        CommandDef('UpdateSelected', update_selection, (),
                   {'variable': 'V::SelectedTemplates'}),
        CommandDef('Exit',  tk.Tk.destroy, ('W::top',),{}),
        CommandDef('BuildTemplates', build_xml, (),
                   {'variable': 'V::SelectedTemplates'}),
        CommandDef('RefreshTemplateList', update_template_data, (),
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
        'template_selector_group': dict(
            borderwidth=10,
            relief='groove',
            ),
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

    root = make_root()
    root.iconify()
    #root.withdraw()
    main_gui = build_top(root)
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


    root.mainloop()


def main():
    '''run current GUI test.
    '''
    template_test()

if __name__ == '__main__':
    main()
