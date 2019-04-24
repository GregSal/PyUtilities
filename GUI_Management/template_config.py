'''
Created on Feb 23 2019

@author: Greg Salomons
Configuration data for Structure templates GUI
'''

# Set the path to the Utilities Package.
from __init__ import add_path
add_path('utilities_path')
add_path('variable_path')

from CustomVariableSet.custom_variable_sets import CustomVariableSet
from CustomVariableSet.custom_variable_sets import PathV, StringV, StrPathV
from file_utilities import set_base_dir


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
