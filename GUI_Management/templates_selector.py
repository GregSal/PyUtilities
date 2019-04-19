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
import tkinter.scrolledtext as tkst
import tkinter.ttk as ttk
from tkinter import messagebox



import sys
# utilities_path = r"C:\Users\Greg\OneDrive - Queen's University\Python\Projects\Utilities"
templates_path = Path.cwd() / r'..\EclipseRelated\EclipseTemplates\ManageStructuresTemplates'
templates_path_str = str(templates_path.resolve())
sys.path.append(templates_path_str)

from file_utilities import set_base_dir, FileTypes, PathInput
from data_utilities import select_data
from spreadsheet_tools import load_reference_table
from custom_variable_sets import PathV, StrPathV, StringV, CustomVariableSet


from GUI_Construction import *
from file_select_window import *
from StructureData import *
from WriteStructureTemplate import *
from manage_template_lists import *


class TemplateData():
    data_fields = ['TemplateID', 'TemplateCategory', 'TreatmentSite',
                   'workbook_name', 'sheet_name', 'modification_date',
                   'Number_of_Structures', 'Description', 'Diagnosis',
                   'Author', 'Columns', 'TemplateFileName', 'Status',
                   'TemplateType', 'ApprovalStatus']

    default_references = dict(
        file_name='Template List.xlsx',
        pickle_file_name='TemplateData.pkl',
        sub_dir=r'Work\Structure Dictionary\Template Spreadsheets',
        unique_scans=['TemplateID'],
        select_columns=data_fields,
        criteria_selection={
            'Status': 'Active'
            }
        )

    file_info_args = ('pickle_file_name', 'sub_dir')
    selections_args = ('unique_scans', 'select_columns', 'criteria_selection')

    def __init__(self, **kwargs):
        self.template_file_info = {}
        self.template_selections = {}
        self.template_file_info = self.set_args(self.file_info_args, kwargs)
        self.template_selections = self.set_args(self.selections_args, kwargs)
        self.template_data = self.get_template_data()


    def set_defaults(self, arg_list: Tuple[str],
                 arguments: Dict[str, Any])->Dict[str, Any]:
        def set_arg(self, arg: str, arguments: Dict[str, Any])->Any:
            '''Return the passed argument value or the default value.
            '''
            return arguments.get(arg, self.default_references[arg])

        args_dict = dict()
        for arg in arg_list:
            args_dict[arg] = self.set_arg(arg, arguments)
        return args_dict

    def set_args(self, arg_list: Tuple[str],
                 arguments: Dict[str, Any])->Dict[str, Any]:
        def set_arg(self, arg: str, arguments: Dict[str, Any])->Any:
            '''Return the passed argument value or the default value.
            '''
            return arguments.get(arg, self.default_references[arg])

        args_dict = dict()
        for arg in arg_list:
            args_dict[arg] = self.set_arg(arg, arguments)
        return args_dict

    def get_template_data(self):
        template_data = load_template_references(**self.template_file_info)
        template_data = select_data(template_data, **self.template_selections)
        return template_data

    def get_workbook_data(self, group_list='workbook_name'):
        return self.template_data.groupby(group_list)


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


variable_set = [
    VariableDef('TemplateListFilename', tk.StringVar, 'template_list_file'),
    VariableDef('TemplateExcelDirectory', tk.StringVar, 'spreadsheet_directory'),
    VariableDef('XmlOutputDirectory', tk.StringVar, 'output_directory'),
    VariableDef('SelectedTemplates', tk.StringVar, 'selected_templates')
    ]
widget_set = [
    WidgetDef('template_selector_group', ttk.Frame, 'top'),
    WidgetDef('template_selector', ttk.Treeview, 'template_selector_group'),
    WidgetDef('selector_scrollbar_h', ttk.Scrollbar, 'template_selector_group'),
    WidgetDef('selector_scrollbar_v', ttk.Scrollbar, 'template_selector_group')
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
                {'variable': 'V::SelectedTemplates'})
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
        )
    }

widget_appearance = {
    'template_selector_group': dict(
        borderwidth=10,
        relief='groove',
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
        )
    }

data_files = ['TemplateID', 'TemplateCategory', 'TreatmentSite',
              'workbook_name', 'sheet_name', 'modification_date',
              'Number_of_Structures', 'Description', 'Diagnosis',
              'Author', 'Columns', 'TemplateFileName', 'Status',
              'TemplateType', 'ApprovalStatus']

default_show_fields = ['workbook_name', 'TemplateID', 'TemplateCategory',
                       'TreatmentSite', 'modification_date', 'Description',
                       'Status']

vars = ['workbook_name', 'sheet_name', 'TemplateID', 'TemplateCategory',
        'TreatmentSite', 'modification_date', 'Diagnosis', 'Author',
        'TemplateFileName', 'Status']

columns = ['TemplateID', 'TemplateCategory', 'TreatmentSite', 'Diagnosis',
            'modification_date', 'Author', 'Status',
            'Number_of_Structures', 'sheet_name', 'Description',
            'TemplateType', 'ApprovalStatus', 'Columns',
            'TemplateFileName']

displaycolumns = ['TemplateID', 'TemplateCategory', 'TreatmentSite',
                    'Diagnosis', 'modification_date', 'Status']


column_def = [dict(
    workbook_name = {
        'column': 'workbook_name', 'text': 'Structure Templates ',
        'anchor': 'w', 'minwidth': 95, 'stretch':'TRUE', 'width': 234},
    TemplateID = {
        'column': 'TemplateID', 'text': 'Template ', 'show': True,
        'anchor': 'w', 'minwidth': 11, 'stretch':'TRUE', 'width': 102},
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
    TemplateFileName = {'anchor': 'w', 'minwidth': 0, 'stretch':'TRUE', 'width': 156}
    )]

heading_def = dict(
    workbook_name = { 'text': 'Structure Templates '},
    sheet_name = { 'text': 'Worksheet '},
    TemplateID = { 'text': 'Template '},
    TemplateCategory = { 'text': 'Category '},
    TreatmentSite = { 'text': 'Site '},
    modification_date = { 'text': 'Modification Date '},
    Diagnosis = { 'text': 'Diagnosis '},
    Author = { 'text': 'Author '},
    TemplateFileName = { 'text': 'Template file name '},
    Status = { 'text': 'Status '},
    Number_of_Structures = { 'text': '# Structures '},
    Description = { 'text': 'Description '},
    TemplateType = { 'text': 'Template Type '},
    ApprovalStatus = { 'text': 'Approval Status '},
    Columns = { 'text': 'Columns '}
    )

def main():
    '''run current GUI test.
    '''
    path_data = TemplateSelectionsSet()

    test_window = GuiManager(main_gui, data_set=path_data)
    test_window.add_widgets(widget_set, variable_set, command_set)
    test_window.define_widgets(widget_definitions, widget_appearance)

    template_selector_group = test_window.widget_lookup['template_selector_group']
    template_selector_group.columnconfigure(0, weight=1)
    template_selector_group.rowconfigure(0, weight=1)

    projects_path = set_base_dir(sub_dir=r'Python\Projects')
    icon_folder = r'EclipseRelated\EclipseTemplates\ManageStructuresTemplates\icons'
    icon_path = projects_path / icon_folder
    file_icon = icon_path / 'Box2.png'
    template_icon = icon_path / 'Blueprint2.png'
    file_image = tk.PhotoImage(file=file_icon)
    template_image = tk.PhotoImage(file=template_icon)


    test_data = TemplateData()
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

    template_selector.tag_bind('File', '<Double-ButtonRelease-1>', callback=file_select)


    template_update = test_window.command_lookup['UpdateSelected']
    template_selector.bind('<<TreeviewSelect>>', template_update, add='+')


    test_window.construct_gui(widget_placement)


if __name__ == '__main__':
    main()
