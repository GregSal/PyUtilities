'''
Created on Feb 23 2019

@author: Greg Salomons
Configuration data for Structure templates GUI
'''


from typing import Union, Callable
from pathlib import Path
from pickle import load
import tkinter as tk
from tkinter import messagebox

StringValue = Union[tk.StringVar, str]

from logging_tools import config_logger
from CustomVariableSet.custom_variable_sets import CustomVariableSet
from CustomVariableSet.custom_variable_sets import PathV, StringV, StrPathV
from file_utilities import set_base_dir
from template_gui.StructureData import load_structure_references
from template_gui.WriteStructureTemplate import build_template

LOGGER = config_logger(level='DEBUG')


class TemplateSelectionsSet(CustomVariableSet):
    base_dir = set_base_dir(r'Work\Structure Dictionary')
    template_directory = base_dir / 'Template Spreadsheets'
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
            'default': base_dir / 'Template XML Files',
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
        },
        {
            'name': 'status',
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
    active_templates['spreadsheet_name'] = [name[0] for name in split_names]
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


def test_message(message_text):
    '''Display the sting message or variable content.'''
    messagebox.showinfo(title='Testing', message=message_text)


def build_xml(template_data: TemplateSelectionsSet,
              status_updater: Callable = None,
              init_progressbar: Callable = None,
              step_progressbar: Callable = None):
    '''build a list of templates from a list of template names.
    '''
    selected_templates = template_data['selected_templates']
    selections_list = selected_templates.split()
    test_message('Building Templates:\n %s' %selected_templates)
    LOGGER.debug('Building Templates:\n %s:', selected_templates)
    if not selections_list:
        return None

    structures_pickle_file_path = template_data['structures_pickle']
    LOGGER.debug('Loading Structures From: %s', str(structures_pickle_file_path))
    structures_lookup = load_structure_references(structures_pickle_file_path)

    LOGGER.debug('Getting Template reference data')
    template_list = template_data['TemplateData']
    template_list['title'] = template_list.TemplateID
    template_param = template_list.set_index('TemplateID') 
    LOGGER.debug(template_list.head())
    LOGGER.debug(template_list.columns)
    column_selection = ['title', 'Columns', 'TemplateFileName',
                        'workbook_name', 'sheet_name']
    selected_template_data = template_param.loc[selections_list, column_selection]
    selected_templates = selected_template_data.to_dict(orient='record')
    LOGGER.debug(selected_template_data.head())
    test_message('Ready to start building Templates')
    LOGGER.debug('Ready to start building Templates')
    template_directory = Path(template_data['spreadsheet_directory'])
    output_path = Path(template_data['output_directory'])
    num_templates = len(selections_list)
    if status_updater is not None:
        status_updater('Building  %d Templates...' %num_templates)
    if init_progressbar is not None:
        init_progressbar(num_templates)
    for template_def in selected_templates:
        LOGGER.debug('Building Template: %s', template_def['title'])
        if status_updater is not None:
            status_updater('Building Template: %s' %template_def['title'])
        build_template(template_def, template_directory, output_path,
                       structures_lookup)
        LOGGER.debug('Done Building Template: %s', template_def['title'])
        if step_progressbar is not None:
            step_progressbar()
    if status_updater is not None:
        status_updater('Done!')

