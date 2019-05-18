'''
Created on Feb 23 2019

@author: Greg Salomons
Configuration data for Structure templates GUI
'''


from typing import Union
from pathlib import Path
from pickle import load
import tkinter as tk
from tkinter import messagebox

StringValue = Union[tk.StringVar, str]

from CustomVariableSet.custom_variable_sets import CustomVariableSet
from CustomVariableSet.custom_variable_sets import PathV, StringV, StrPathV
from file_utilities import set_base_dir


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


def load_template_list(template_list_pickle_file_path: Path):
    '''Import the list of active templates.
    '''
    file = open(str(template_list_pickle_file_path), 'rb')
    template_list = load(file)
    file.close()
    active_templates = template_list[template_list.Status == 'Active']
    active_templates['Columns'] = active_templates['Columns'].astype('int64')
    split_names = active_templates['workbook_name'].str.split('.', 1)
    active_templates['workbook_name'] = [name[0] for name in split_names]
    return active_templates


def update_selection(event, variable):
    select_list = [str(item) for item in event.widget.selection()]
    select_str = '\n'.join(select_list)
    variable.set(select_str)


def print_select(event):
    selected = str(event.widget.focus())
    messagebox.showinfo('Selected File', selected)


def file_select(event, variable: StringValue):
    selected_file = event.widget.focus()
    event.widget.item(selected_file, open=True)
    #test_message_window(event.widget, (selected_file,), 'Selected File')

    file_templates = event.widget.get_children(item=selected_file)
    #test_message_window(event.widget, file_templates, 'Templates in Selected File')

    event.widget.selection_remove(selected_file)
    select_list = event.widget.selection()
    #test_message_window(event.widget, select_list, 'All Selected Templates')

    is_selected = [file_template in select_list
                   for file_template in file_templates]
    if all(is_selected):
        event.widget.selection_remove(*file_templates)
    else:
        event.widget.selection_add(*file_templates)
    update_selection(event, variable)

def test_message_window(parent_window: tk.Widget, file_templates, window_text):
    '''Display the sting message or variable content.'''
    str_message = '\n'.join(file_templates)
    messagebox.showinfo(title=window_text, message=str_message,
                        parent=parent_window)

