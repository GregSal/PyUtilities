'''
Created on Feb 23 2019

@author: Greg Salomons
Configuration data for Structure templates GUI
'''


from typing import Union, Callable
from pathlib import Path
from pickle import dump, load
import tkinter as tk
from tkinter import messagebox
import pandas as pd

StringValue = Union[tk.StringVar, str]

from logging_tools import config_logger, log_dict
from CustomVariableSet.custom_variable_sets import CustomVariableSet
from CustomVariableSet.custom_variable_sets import PathV, StringV, StrPathV
from file_utilities import set_base_dir
from spreadsheet_tools import open_book, load_definitions, append_data_sheet
from template_gui.StructureData import load_structure_references
from template_gui.WriteStructureTemplate import build_template
from template_gui.StructureData import build_structures_lookup
from template_gui.manage_template_lists import scan_template_workbook
from template_gui.manage_template_lists import find_template_files

LOGGER = config_logger(level='ERROR')


class TemplateSelectionsSet(CustomVariableSet):
    base_dir = set_base_dir(r'Work\Structure Dictionary')
    template_dir = base_dir / 'Template Spreadsheets'
    variable_definitions = [
        {
            'name': 'spreadsheet_directory',
            'variable_type': StrPathV,
            'file_types': 'directory',
            'default': template_dir,
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
            'default': template_dir / 'Structure Lookup.xlsx',
            'required': False
        },
        {
            'name': 'structures_pickle',
            'variable_type': PathV,
            'file_types': 'Pickle File',
            'default': template_dir / 'StructureData.pkl',
            'required': False
        },
        {
            'name': 'template_list_file',
            'variable_type': PathV,
            'file_types': 'Excel Files',
            'default': template_dir / 'Template List.xlsx',
            'required': False
        },
        {
            'name': 'template_pickle',
            'variable_type': PathV,
            'file_types': 'Pickle File',
            'default': template_dir / 'TemplateData.pkl',
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
    active_templates['title'] = active_templates.TemplateID
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
    selections_list = selected_templates.splitlines()

    #LOGGER.setLevel(10)  # logging.DEBUG
    #test_message('Building Templates:\n%s' %selected_templates)
    #LOGGER.debug('Building Templates:\n%s:', selected_templates)
    #LOGGER.debug('Template List:\n%s:', selections_list)
    if not selections_list:
        return None

    strc_pickle = template_data['structures_pickle'].value

    #LOGGER.debug('Loading Structures From: %s', str(strc_pickle))

    strc_lu = load_structure_references(strc_pickle)

    #LOGGER.debug('Getting Template reference data')

    template_list = template_data['TemplateData']

    #LOGGER.debug(template_list.head())
    #LOGGER.debug(template_list.columns)

    template_indxer = template_list['TemplateID'].isin(selections_list)
    column_selection = ['title', 'Columns', 'TemplateFileName',
                        'workbook_name', 'sheet_name']
    selected_templates = template_list.loc[template_indxer, column_selection]

    #LOGGER.debug(selected_templates.head())
    #test_message('Ready to start building Templates')
    #LOGGER.debug('Ready to start building Templates')

    template_dir = Path(template_data['spreadsheet_directory'])
    output_path = Path(template_data['output_directory'])
    num_templates = len(selections_list)
    if status_updater is not None:
        status_updater('Building  %d Templates...' %num_templates)
    if init_progressbar is not None:
        init_progressbar(num_templates)
    for template_def in selected_templates.to_dict(orient='record'):

        #LOGGER.debug('Building Template: %s', template_def['title'])

        if status_updater is not None:
            status_updater('Building Template: %s' %template_def['title'])
        build_template(template_def, template_dir, output_path,
                       strc_lu)

        #LOGGER.debug('Done Building Template: %s', template_def['title'])

        if step_progressbar is not None:
            step_progressbar()
    if status_updater is not None:
        status_updater('Done!')
    pass

def update_template_data(template_data: TemplateSelectionsSet,
              status_updater: Callable = None,
              init_progressbar: Callable = None,
              step_progressbar: Callable = None):

    def show_types(var_names):
        for var in var_names:
            log_str = '{} is type {}'.format(var, type(globals()[var]))
            LOGGER.debug(log_str)

    #LOGGER.setLevel(10)  # logging.DEBUG
    LOGGER.debug('Updating Template Lists')
    #test_message('Updating Template Lists')
    template_dir = Path(template_data['spreadsheet_directory'])

    template_file = template_data['template_list_file']
    template_pkl = template_data['template_pickle']

    strc_path = template_data['structures_file'].value
    strc_pickle = template_data['structures_pickle']

    log_dict(LOGGER, globals())
    tmpl_tbl_def = dict(file_name=template_file,
                                sheet_name='templates',
                                new_file=True, new_sheet=True, replace=True)
    strc_tbl_def = tmpl_tbl_def.copy()
    strc_tbl_def['sheet_name'] = 'structures'

    LOGGER.debug('Opening Structures reference spreadsheet: %s', str(strc_path))
    #test_message('Opening Structures reference spreadsheet: %s' %str(strc_path))
    open_book(strc_path)

    LOGGER.debug('Building Structures reference')
    #test_message('Building Structures reference')
    if status_updater is not None:
        status_updater('Building Structures reference...')
    if init_progressbar is not None:
        init_progressbar(10)

    strc_lu = build_structures_lookup(strc_path)
    file = open(str(strc_pickle), 'wb')
    dump(strc_lu, file)
    file.close()

    LOGGER.debug('Updating list of templates')
    #test_message('Updating list of templates')
    if status_updater is not None:
        status_updater('Updating list of templates...')

    template_files = find_template_files(template_dir)
    num_files = len(template_files)
    LOGGER.debug('Found %d template files', num_files)
    #test_message('Found %d template files' %num_files)
    if status_updater is not None:
        status_updater('Found  %d template files...' %num_files)
    if init_progressbar is not None:
        init_progressbar(num_files)

    template_data = pd.DataFrame()
    structure_data = pd.DataFrame()

    for file in template_files:

        if status_updater is not None:
            file_name = file.stem
            status_updater('Scanning template file: %s' %file_name)

        structure_data, template_data = scan_template_workbook(
            file, structure_data, strc_lu, template_data)

        if step_progressbar is not None:
            step_progressbar()

    LOGGER.debug('Saving updated list of templates')
    #test_message('Saving updated list of templates')
    if status_updater is not None:
        status_updater('Saving updated list of templates')

    append_data_sheet(template_data, **tmpl_tbl_def)
    append_data_sheet(structure_data, **strc_tbl_def)
    file = open(str(template_pkl), 'wb')
    dump(template_data, file)
    file.close()

    if status_updater is not None:
        status_updater('Done!')