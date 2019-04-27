'''
Created on Feb 23 2019

@author: Greg Salomons
Configuration data for Structure templates GUI
'''


from typing import Union, TypeVar, List, Dict, Tuple, Callable, Any

from CustomVariableSet.custom_variable_sets import CustomVariableSet
from CustomVariableSet.custom_variable_sets import PathV, StringV, StrPathV
from file_utilities import set_base_dir
from EclipseRelated.EclipseTemplates.ManageStructuresTemplates.manage_template_lists import load_template_references


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
                               for item in show_vars] # FIXME do not use id as variable
            id = template_selector.insert(file_ref, 'end', name, text=name,
                                          values=template_values,
                                          tags=('Template',))
            template_ref[name] = id


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
