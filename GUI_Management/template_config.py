'''
Created on Feb 23 2019

@author: Greg Salomons
Configuration data for Structure templates GUI
'''


from typing import Union, TypeVar, List, Dict, Tuple, Callable, Any
from tkinter import messagebox
from pathlib import Path

from CustomVariableSet.custom_variable_sets import CustomVariableSet
from CustomVariableSet.custom_variable_sets import PathV, StringV, StrPathV
from file_utilities import set_base_dir
from spreadsheet_tools import load_reference_table

from EclipseRelated.EclipseTemplates.ManageStructuresTemplates.template_manager import load_template_data, update_template_data, build_xml
#from StructureData import *
#from WriteStructureTemplate import *
#from manage_template_lists import *

class TemplateSelectionsSet(CustomVariableSet):
    template_directory = set_base_dir(
            r'Work\Structure Dictionary\Template Spreadsheets')
    variable_definitions = [
        {
            'name': 'spreadsheet_directory',
            'variable_type': StrPathV,
            'file_types': 'directory',
            'default': template_directory,
            'required': False
        },
        {
            'name': 'output_directory',
            'variable_type': StrPathV,
            'file_types': 'directory',
            'default': r'Work\Structure Dictionary\Template XML Files',
            'required': False
        },
        {
            'name': 'structures_file',
            'variable_type': PathV,
            'file_types': 'Excel Files',
            'default': template_directory / 'Structure Lookup.xlsx',
            'required': False
        },
        {
            'name': 'structures_pickle',
            'variable_type': PathV,
            'file_types': 'Pickle File',
            'default': template_directory / 'StructureData.pkl',
            'required': False
        },
        {
            'name': 'template_list_file',
            'variable_type': PathV,
            'file_types': 'Excel Files',
            'default': template_directory / 'Template List.xlsx',
            'required': False
        },
        {
            'name': 'template_pickle',
            'variable_type': PathV,
            'file_types': 'Pickle File',
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


class TemplateData():
    data_fields = ['TemplateID', 'TemplateCategory', 'TreatmentSite',
                   'workbook_name', 'sheet_name', 'modification_date',
                   'Number_of_Structures', 'Description', 'Diagnosis',
                   'Author', 'Columns', 'template_file_name', 'Status',
                   'TemplateType', 'ApprovalStatus']

    def __init__(self, **kwargs):
        self.template_file_info = dict(
            file_name='Template List.xlsx',
            sub_dir=r'Work\Structure Dictionary\Template Spreadsheets',
            sheet_name='templates'
            )
        self.template_table_info = dict(
            starting_cell='A1',
            header=1
            )
        self.template_selections = dict(
            unique_scans=['TemplateID'],
            select_columns=self.data_fields,
            criteria_selection = {'workbook_name': 'Basic Templates.xlsx',
                                  'Status': 'Active'}
            )
        self.set_args(kwargs, 'template_table_info')
        self.set_args(kwargs, 'template_selections')
        self.set_args(kwargs, 'template_data')
        self.template_data = self.get_template_data()

    def set_args(self, arguments: Dict[str, Any], dict_name: str):
        dict_to_update = self.__getattribute__(dict_name)
        field_names = tuple(dict_to_update.keys())
        args_dict = {key: value for key, value in arguments.items()
                     if key in field_names}
        dict_to_update.update(args_dict)

    def get_template_data(self):
        template_data = load_reference_table(
            self.template_file_info,
            self.template_table_info,
            **self.template_selections)
        # load_template_data(pickle_file_name: PathInput, sub_dir: str = None, base_path: Path = None)
        workbook_str = workbook.split('.', 1)[0]
        return template_data

    def get_workbook_data(self):
        return self.template_data.groupby('workbook_name')





# TODO  Asses which methods should stay here

def update_selection(event, variable):
    select_list = [str(item) for item in event.widget.selection()]
    select_str = '\n'.join(select_list)
    variable.set(select_str)


def select_list_2_str(select_list: List[str])-> str:
    return '\n'.join(select_list)


def print_select(event):
    selected = str(event.widget.focus())
    messagebox.showinfo('Selected File', selected)


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
            item_id = template_selector.insert(file_ref, 'end', name, text=name,
                                          values=template_values,
                                          tags=('Template',))
            template_ref[name] = item_id


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


