'''
Created on Feb 23 2019

@author: Greg Salomons
Configuration data for Structure templates GUI
'''


from typing import List, Union, Callable
from pathlib import Path
from pickle import dump, load
import tkinter as tk
from tkinter import messagebox
import pandas as pd
from CustomVariableSet.custom_variable_sets import CustomVariableSet
from CustomVariableSet.custom_variable_sets import PathV, StringV, StrPathV
from file_utilities import set_base_dir
from spreadsheet_tools import open_book, append_data_sheet
from template_gui.StructureData import load_structure_references
from template_gui.WriteStructureTemplate import build_template
from template_gui.StructureData import build_structures_lookup
from template_gui.manage_template_lists import scan_template_workbook
from template_gui.manage_template_lists import find_template_files


StringValue = Union[tk.StringVar, str]


class TemplateSelectionsSet(CustomVariableSet):
    '''The file paths etc. required to manage the templates.
    Parent Class: {CustomVariableSet}
    Variables Defined:
        spreadsheet_directory {StrPathV[directory]} -- Directory where the
            Template spreadsheets are located.
            default = Work\Structure Dictionary\Template Spreadsheets
        output_directory {StrPathV[directory]} -- Directory where the
            Template XML files are to be saved.
            default = Work\Structure Dictionary\Template XML Files'
        structures_file {PathV[Excel Files]} -- Path to the Structures Lookup
            spreadsheet.
            default = Work\Structure Dictionary\Template Spreadsheets\Structure Lookup.xlsx
        structures_pickle {PathV[Pickle File]} -- Path to the Structures
            Lookup pickle file.
            default = Work\Structure Dictionary\Template Spreadsheets\StructureData.pkl
        template_list_file {PathV[Excel Files]} -- Path to the Template List
            spreadsheet.
            default = Work\Structure Dictionary\Template Spreadsheets\Template List.xlsx
        template_pickle {PathV[Pickle File]} -- Path to the Template List
            pickle file.
            default = Work\Structure Dictionary\Template Spreadsheets\TemplateData.pkl
        selected_templates {StringV} -- List of selected templates.
        status {StringV} -- Status string.
    '''
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


def load_template_list(template_list_pickle_file_path: Path)->pd.DataFrame:
    '''Import the list of active templates.
    Arguments:
        template_list_pickle_file_path {Path} -- The full path to the
            Template List Pickle file.
    Returns:
        {pd.DataFrame} -- The reference data for all Structure template
            spreadsheets.
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


def update_selection(event: tk.Event, variable: tk.StringVar):
    '''Update the display string listing the selected templates.
    Arguments:
        event {tk.Event} -- A select/de-select event.
        variable {tk.StringVar} -- The variable used for displaying selected
            templates.
    '''
    select_list = [str(item) for item in event.widget.selection()]
    select_str = '\n'.join(select_list)
    variable.set(select_str)


def print_select(event: tk.Event):
    '''A test function to display the selected templates in a message window.
    Arguments:
        event {: tk.Event} -- A select/de-select or other event.
    '''
    selected = str(event.widget.focus())
    messagebox.showinfo('Selected File', selected)


def file_select(event: tk.Event, variable: StringValue):
    '''Convert the selected file into a selection/de-selection of all
        Templates within that file.
    Arguments:
        event {tk.Event} -- A select/de-select event triggered on a File.
        variable {StringValue} -- The variable used for displaying selected
            templates.
    '''
    selected_file = event.widget.focus()
    event.widget.item(selected_file, open=True)
    file_templates = event.widget.get_children(item=selected_file)
    event.widget.selection_remove(selected_file)
    select_list = event.widget.selection()
    is_selected = [file_template in select_list
                   for file_template in file_templates]
    if all(is_selected):
        event.widget.selection_remove(*file_templates)
    else:
        event.widget.selection_add(*file_templates)
    update_selection(event, variable)


def test_message_window(parent_window: tk.Widget, file_templates: List[str],
                        window_text: str):
    '''Display the list of file templates in a message box.
    Arguments:
        parent_window {tk.Wm} -- The parent window for the message box.
        file_templates {List[str]} -- The list of selected templates.
        window_text {str} -- The title of the message window.
    '''
    str_message = '\n'.join(file_templates)
    messagebox.showinfo(title=window_text, message=str_message,
                        parent=parent_window)


def test_message(message_text: str):
    '''Display the string as a test message.
    Arguments:
        message_text {str} -- The message to display
    '''
    messagebox.showinfo(title='Testing', message=message_text)


def build_xml(template_data: TemplateSelectionsSet,
              status_updater: Callable = None,
              init_progressbar: Callable = None,
              step_progressbar: Callable = None):
    '''build a list of templates from a list of template names.
    Arguments:
        template_data {TemplateSelectionsSet} -- The file paths etc. required
            to build the XML template files.
    Keyword Arguments:
        status_updater {Callable} -- A method that updates a status
            text widget. (default: {None})
        init_progressbar {Callable} -- A method that initializes a
            progress bar widget. (default: {None})
        step_progressbar {Callable} -- A method that updates a
            progress bar widget.
            (default: {None})
    '''
    selected_templates = template_data['selected_templates']
    selections_list = selected_templates.splitlines()
    if not selections_list:
        return None
    strc_pickle = template_data['structures_pickle'].value
    strc_lu = load_structure_references(strc_pickle)
    template_list = template_data['TemplateData']
    template_indxer = template_list['TemplateID'].isin(selections_list)
    column_selection = ['title', 'Columns', 'TemplateFileName',
                        'workbook_name', 'sheet_name']
    selected_templates = template_list.loc[template_indxer, column_selection]
    template_dir = Path(template_data['spreadsheet_directory'])
    output_path = Path(template_data['output_directory'])
    num_templates = len(selections_list)
    if status_updater is not None:
        status_updater('Building  %d Templates...' %num_templates)
    if init_progressbar is not None:
        init_progressbar(num_templates)
    for template_def in selected_templates.to_dict(orient='record'):
        if status_updater is not None:
            status_updater('Building Template: %s' %template_def['title'])
        build_template(template_def, template_dir, output_path,
                       strc_lu)
        if step_progressbar is not None:
            step_progressbar()
    if status_updater is not None:
        status_updater('Done!')
    pass

def update_template_data(template_data: TemplateSelectionsSet,
                         status_updater: Callable = None,
                         init_progressbar: Callable = None,
                         step_progressbar: Callable = None):
    '''Update the primary list of templates.
    Arguments:
        template_data {TemplateSelectionsSet} -- The file paths etc. required
            to update the primary list of templates.
    Keyword Arguments:
        status_updater {Callable} -- A method that updates a status
            text widget. (default: {None})
        init_progressbar {Callable} -- A method that initializes a
            progress bar widget. (default: {None})
        step_progressbar {Callable} -- A method that updates a
            progress bar widget.
            (default: {None})
    '''
    def update_status(status_text: str, progress_target: int = None):
        '''Update the current progress.
        Arguments:
            status_text {str} -- The text to append to a status text widget.
            progress_target {int} -- The end point for the progress bar.
                If None the progress bar is incremented (default: {None})
        '''
        if status_updater is not None:
            status_updater(status_text)
        if progress_target:
            if init_progressbar is not None:
                init_progressbar(progress_target)
        elif step_progressbar is not None:
            step_progressbar()

    # Initialize the required variables
    template_dir = Path(template_data['spreadsheet_directory'])
    template_file = template_data['template_list_file']
    template_pkl = template_data['template_pickle']
    strc_path = template_data['structures_file'].value
    strc_pickle = template_data['structures_pickle']
    tmpl_tbl_def = dict(file_name=template_file, sheet_name='templates',
                        new_file=True, new_sheet=True, replace=True)
    strc_tbl_def = tmpl_tbl_def.copy()
    strc_tbl_def['sheet_name'] = 'structures'
    # Rebuild the Structure Lookup Pickle file
    open_book(strc_path)
    update_status('Building Structures reference...', 10)
    strc_lu = build_structures_lookup(strc_path)
    file = open(str(strc_pickle), 'wb')
    dump(strc_lu, file)
    file.close()
    # Rebuild the Template List Pickle file
    update_status('Updating list of templates...')
    # Find all Template files
    template_files = find_template_files(template_dir)
    num_files = len(template_files)
    update_status('Found  %d template files...' %num_files, num_files)
    template_data = pd.DataFrame()
    structure_data = pd.DataFrame()
    # Scan each file for template and structure data
    for file in template_files:
        file_name = file.stem
        update_status('Scanning template file: %s' %file_name)
        structure_data, template_data = scan_template_workbook(
            file, structure_data, strc_lu, template_data)
    update_status('Saving updated list of templates')
    append_data_sheet(template_data, **tmpl_tbl_def)
    append_data_sheet(structure_data, **strc_tbl_def)
    file = open(str(template_pkl), 'wb')
    dump(template_data, file)
    file.close()
    update_status('Done')
