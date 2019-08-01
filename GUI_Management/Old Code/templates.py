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

def build_xml(selected_templates, template_directory, xml_directory,
              structures_pickle_file_path, template_list_pickle_file_path):
    structures_lookup = load_structure_references(structures_pickle_file_path)
    template_list = select_templates(template_list_pickle_file_path,
                                     selected_templates)
    build_templates(template_list, template_directory, xml_directory,
                    structures_lookup)


def update_template_data(template_directory: Path,
                         template_list_file: Path,
                         template_list_pickle_file_path: Path,
                         structures_file_path: Path,
                         structures_pickle_file_path: Path):
    '''Update the templates list spreadsheet and the corresponding pickle file.
    '''
    template_table_info = dict(file_name=template_list_file,
                               sheet_name='templates',
                               new_file=True, new_sheet=True, replace=True)
    structure_table_info = template_table_info.copy()
    structure_table_info['sheet_name'] = 'structures'

    update_template_list(template_directory, template_table_info,
                         template_list_pickle_file_path,
                         structures_pickle_file_path, structure_table_info,
                         structures_file_path)


class TemplateData():
    data_fields = ['TemplateID', 'TemplateCategory', 'TreatmentSite',
                   'workbook_name', 'sheet_name', 'modification_date',
                   'Number_of_Structures', 'Description', 'Diagnosis',
                   'Author', 'Columns', 'TemplateFileName', 'Status',
                   'TemplateType', 'ApprovalStatus']
    file_info_args = ('pickle_file_name', 'sub_dir')
    selections_args = ('unique_scans', 'select_columns', 'criteria_selection')

    default_references = dict(
        file_name='Template List.xlsx',
        pickle_file_name='TemplateData.pkl',
        sub_dir=r'Work\Structure Dictionary\Template Spreadsheets',
        sheet_name='templates',
        unique_scans=['TemplateID'],
        select_columns=data_fields,
        criteria_selection={
            'Status': 'Active'
            }
        )
    def __init__(self, **kwargs):
        self.template_file_info = self.set_args(self.file_info_args, kwargs)
        self.template_table_info = self.set_args(self.table_info_args, kwargs)
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


class TemplateSelectionsSet(CustomVariableSet):
    '''A CustomVariable set with two path variables:
            "test_string1"
            "test_integer"
    '''
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
    WidgetDef('selector_scrollbar_v', ttk.Scrollbar, 'template_selector_group'),
    WidgetDef('Selected_templates', ttk.LabelFrame, 'top'),
    WidgetDef('SelectedTemplatesList', ttk.Label, 'Selected_templates'),
    WidgetDef('file_selector_group', ttk.Frame, 'top'),
    WidgetDef('output_directory', FileSelectGUI, 'file_selector_group'),
    WidgetDef('template_directory', FileSelectGUI, 'file_selector_group'),
    WidgetDef('template_list_excel_file', FileSelectGUI, 'file_selector_group'),
    WidgetDef('exit_button', ttk.Button, 'file_selector_group'),
    WidgetDef('build_templates', ttk.Button, 'file_selector_group'),
    WidgetDef('refresh_template_list', ttk.Button, 'file_selector_group')
    ]
CommandDef = namedtuple('CommandDef', ['name', 'function', 'args', 'kwargs'])
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
                {'selected_templates': 'V::SelectedTemplates',
                 'template_directory': 'V::TemplateExcelDirectory',
                 'xml_directory': 'V::XmlOutputDirectory',
                 'structures_pickle_file_path': 'D::structures_pickle',
                 'template_list_pickle_file_path': 'D::template_pickle'}),
    CommandDef('RefreshTemplateList', update_template_data, (),
                {'template_directory': 'V::TemplateExcelDirectory',
                 'template_list_file': 'V::TemplateListFilename',
                 'template_list_pickle_file_path': 'D::template_pickle',
                 'structures_file_path': 'D::structures_file',
                 'structures_pickle_file_path': 'D::structures_pickle'
                 })
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
    'Selected_templates': dict(
        text='Selected Templates:'
        ),
    'SelectedTemplatesList': dict(
        textvariable='V::SelectedTemplates'
        ),
    'template_list_excel_file': dict(
        text='Template File Selection',
        title='Select File',
        path_variable='V::TemplateListFilename',
        type_selection=FileTypes('Excel Files'),
        starting_path=Path.cwd(),
        action='open',
        button_text='Browse'
        ),
    'template_directory': dict(
        text='Template Directory',
        title='Select the Directory Containing the Excel Template Files',
        path_variable='V::TemplateExcelDirectory',
        type_selection=FileTypes('directory'),
        starting_path=Path.cwd(),
        action='open',
        button_text='Browse'
        ),
    'output_directory': dict(
        text='XML Directory Selection',
        title='Select the directory to place the .xml files in.',
        path_variable='V::XmlOutputDirectory',
        type_selection=FileTypes('directory'),
        starting_path=Path.cwd(),
        action='open',
        button_text='Browse'
        ),
    'exit_button': dict(
        text='Exit',
        command='C::Exit'
        ),
    'build_templates': dict(
        text='Build the XML Template Files',
        command='C::BuildTemplates'
        ),
    'refresh_template_list': dict(
        text='Refresh Template List',
        command='C::RefreshTemplateList'
        )
    }

widget_appearance = {
    'template_selector_group': dict(
        borderwidth=10,
        relief='groove',
        ),
    'Selected_templates': dict(
        borderwidth=10,
        relief='groove'
        ),
    'SelectedTemplatesList': dict(
        anchor='nw',
        justify='left',
        width=25
        ),
    'template_list_excel_file': dict(
        borderwidth=10,
        relief='groove',
        entry_cursor='xterm',
        entry_justify='left',
        entry_width=115,
        button_width=10
        ),
    'output_directory': dict(
        borderwidth=10,
        relief='groove',
        entry_cursor='xterm',
        entry_justify='left',
        entry_width=115,
        button_width=10
        ),
    'template_directory': dict(
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
    'build_templates': dict(
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
    'Selected_templates': dict(
        layout_method='grid',
        padx=5, pady=5,
        column=1, row=0, sticky='nsew'
        ),
    'SelectedTemplatesList': dict(
        layout_method='grid',
        ipadx=5, pady=5,
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
    'file_selector_group': dict(
        layout_method='grid',
        padx=5, pady=5,
        column=0, row=1, sticky='nsew'
        ),
    'template_list_excel_file': dict(
        layout_method='grid',
        padx=5, pady=5,
        column=0, row=0, sticky='nsew'
        ),
    'template_directory': dict(
        layout_method='grid',
        padx=5, pady=5,
        column=0, row=1, sticky='nsew'
        ),
    'output_directory': dict(
        layout_method='grid',
        padx=5, pady=5,
        column=0, row=2, sticky='nsew'
        ),
    'build_templates': dict(
        layout_method='grid',
        padx=5, pady=5,
        column=1, row=1
        ),
    'refresh_template_list': dict(
        layout_method='grid',
        padx=5, pady=5,
        column=1, row=2
        ),
    'exit_button': dict(
        layout_method='grid',
        padx=5, pady=5,
        column=1, row=0
        )
    }

column_set = [
    ['workbook_name', '', 'Structure Templates', 'tree', 95, 'w', 'TRUE', 234],
    ['TemplateID', 'TemplateID', 'Template', 'y', 11, 'w', 'TRUE', 102],
    ['TemplateCategory', 'TemplateCategory', 'Category', 'y', 16, '', 'TRUE', 42],
    ['TreatmentSite', 'TreatmentSite', 'Site ', 'y', 21, 'w', 'TRUE', 102],
    ['Diagnosis', 'Diagnosis', 'Diagnosis', 'y', 74, 'w', 'TRUE', 150],
    ['modification_date', 'modification_date', 'Modification Date', 'y', 69, 'w', 'TRUE', 96],
    ['Author', 'Author', 'Author', 'n', 21, '', 'TRUE', 24],
    ['Status', 'Status', 'Status', 'y', 32, '', 'TRUE', 48],
    ['Number_of_Structures', 'Number_of_Structures', '# Structures', 'n', 5, '', 'TRUE', 12],
    ['sheet_name', 'sheet_name', 'Worksheet', 'n', 11, 'w', 'TRUE', 132],
    ['Description', 'Description', 'Description', 'n', 16, 'w', 'TRUE', 1308],
    ['TemplateType', 'TemplateType', 'Template Type', 'n', 28, '', 'TRUE', 54],
    ['ApprovalStatus', 'ApprovalStatus', 'Approval Status', 'n', 42, '', 'TRUE', 60],
    ['Columns', 'Columns', 'Columns', 'n', 5, '', 'TRUE', 6],
    ['TemplateFileName', 'TemplateFileName', 'Template file name', 'n', 0, 'w', 'TRUE', 156]
    ]
columns=['data_column', 'tree_column_id', 'header_text', 'show', 'minwidth', 'anchor', 'stretch', 'width']


def main():
    '''run current GUI test.
    '''
    path_data = TemplateSelectionsSet()
    root = make_root()
    root.iconify()
    #root.withdraw()
    main_gui = build_top(root)
    main_gui.title('Template Selection')
    test_window = GuiManager(main_gui, data_set=path_data)
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


    test_data = TemplateData(select_columns)
    active_templates = test_data.get_template_data()
    workbooks = test_data.get_workbook_data()


    template_selector = test_window.widget_lookup['template_selector']
    template_selector['columns'] = list(column_set.tree_column_id)
    index = column_set.show.str.contains('y')
    displaycolumns = list(column_set.loc[index, 'tree_column_id'])
    template_selector['displaycolumns'] = displaycolumns

###########
# Start here
############
    column_options = ['anchor', 'minwidth', 'stretch', 'width']
    header_options = ['text', 'image', 'anchor', 'command']
    for column_def in column_set:
        column = column_def.tree_column_id
        options = template_selector.column(column, **options)
    tree_opts = column_def.pop('workbook_name')
    column_def['#0'] = tree_opts
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
    root.deiconify()
    main_gui.lift(root)
    root.mainloop()


if __name__ == '__main__':
    main()
