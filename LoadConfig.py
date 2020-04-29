'''Fill an Excel SABR Spreadsheet with values from a DVH file.
'''


#%% imports etc.
# from typing import Any, Dict, List
# from copy import deepcopy
from pathlib import Path
# from functools import partial
# from itertools import product
# import re
import xml.etree.ElementTree as ET
# from pickle import dump, load

# import pandas as pd
# import xlwings as xw
# import PySimpleGUI as sg
# from data_utilities import true_iterable
# from spreadsheet_tools import get_data_sheet, load_table


def load_config(base_path: Path, config_file_name: str)->ET.Element:
    '''Load the XML configuration file
    Arguments:
        base_path {Path} -- The directory containing the config file.
        config_file_name {str} -- The name of configuration file.
    Returns:
        ET.Element -- The root element of the XML config data
    '''
    config_path = base_path / config_file_name
    config_tree = ET.parse(config_path)
    config = config_tree.getroot()
    return config


def get_path(default_paths, path_name):
    x_path = f'.//*[@name="{path_name}"]'
    path_elmt = default_paths.find(x_path)
    full_path_elm =  path_elmt.find('FullPath')
    if full_path_elm is not None:
        full_path = Path(full_path_elm).resolve()
        return full_path
    base_dir_txt = path_elmt.find('BaseDirectory').text
    base_dir = Path(base_dir_txt).resolve()
    sub_dir = path_elmt.find('Folder').text
    if sub_dir is not None:
        dir_path = base_dir / sub_dir
    else:
        dir_path = base_dir
    if 'File' in path_elmt.tag:
        file_name = path_elmt.find('FileName').text
        full_path = dir_path / file_name
        full_path = full_path.resolve()
        return full_path
    full_path = dir_path.resolve()
    return full_path


#%% Main
def main():
    '''Test
    '''
    # Load Config File Data
    base_path = Path.cwd()
    config_file = 'FilePaths.xml'
    config = load_config(base_path, config_file)
    default_paths = config.find('DefaultPaths')
    get_path(default_paths, "DataDir")




    SQL_PATH = Path.cwd() / r'..\SQL'
    SQL_PATH = SQL_PATH.resolve()
    source_path = Path.cwd() / r'..'
    source_path = source_path.resolve()
    reference_path = source_path / 'Reference Data'
    template_path = source_path / 'Templates'
    data_path = Path(r'L:\temp\Plan Checking Temp')
    file_paths = dict(
        starting_path = data_path,
        sql_path = source_path / 'SQL',
        template_file_path = template_path / 'DVH Check Template.xlsx',
        save_data_file_name = data_path / 'plan_check_data.xlsx',
        save_form_file_name = data_path / 'DVHCheck.xlsx'
        )


    window = make_window()
    file_frame_list = file_selection_frame(**file_paths)
    window.extend_layout(window['File Selection'], file_frame_list)




class StructSelector(dict):
    def __missing__(self, key):
        new_list = list()
        self[key] = new_list
        return self[key]


class IconPaths(dict):
    '''Match Parameters for a PlanReference.
        Report Item name, match status, plan item type, Plan Item name
    Attributes:
        match_icon {Path} -- Green Check mark
        not_matched_icon {str} -- The type of PlanElement.  Can be one of:
            ('Plan Property', Structure', 'Reference Point', 'Ratio')
        match_status: {str} -- How a plan value was obtained.  One of:
            One of Auto, Manual, Direct Entry, or None
        plan_Item: {str} -- The name of the matched element from the Plan.
    '''
    def __init__(self, icon_path):
        '''Initialize the icon paths.
        Attributes:
            icon_path {Path} -- The path to the Icon Directory
        Contains the following Icon references:
            match_icon {Path} -- Green Check mark
            not_matched_icon {Path} -- Red X
            changed_icon {Path} -- Yellow Sun
        '''
        super().__init__()
        # Icons
        self['match_icon'] = icon_path / 'Checkmark.png'
        self['not_matched_icon'] = icon_path / 'Error_Symbol.png'
        self['changed_icon'] = icon_path / 'emblem-new'

    def path(self, icon_name):
        '''Return a string path to the icon.
        Attributes:
            icon_name {str} -- The name of an icon in the dictionary
        '''
        icon_path = self.get(icon_name)
        if icon_path:
            return str(icon_path)
        return None


#%% Initialization Methods
# Question use file utilities functions for path and file name checking/completion?
def save_config(updated_config: ET.Element,
                base_path: Path, config_file_name: str):
    '''Saves the XML configuration file
    Arguments:
        base_path {Path} -- The directory containing the config file.
        config_file_name {str} -- The name of configuration file.
    Returns:
        ET.Element -- The root element of the XML config data
    '''
    config_path = base_path / config_file_name
    config_tree = ET.ElementTree(element=updated_config)
    config_tree.write(config_path)


#%% Widget Defaults
def widget_defaults()->Dict[str, Any]:
    '''A dictionary containing default values for the GUI widgets.
    '''
    default_values = {
        'Protocol Name': '',
        'EditingProtocol': '',
        'Protocol Region': '',
        'Treatment Technique': '',
        'Protocol Description': '',
        'Prescribed Dose': '',
        'Prescribed Dose Units': 'Gy',
        'Prescribed Fractions': '',
        'TemplateCategory': '',
        'TreatmentSite': '',
        'StructureTemplateID': '',
        'Volume Type': '',
        'StructureID': '',
        'StructureLabel': '',
        'Reference Label': '',
        'Structure Laterality': '',
        'Level': '',
        'Laterality Relation': '',
        'Condition': '',
        'Criteria Type': '',
        'Search Value': '',
        'Search Unit': '',
        'Relation': '',
        'Criteria Value': '',
        'Criteria Unit': '',
        'Criteria Description': ''
        }
    return default_values
#%%  Select File
def file_selection_frame(**file_paths):

    def make_file_selection_list(starting_path, template_file_path, sql_path,
                                 save_data_file_name='plan_check_data.xlsx',
                                 save_form_file_name='PlanCheck.xlsx'):
        file_selection_list = [
            dict(frame_title='Select DVH File to Load',
                 file_k='dvh_file',
                 check_k='read_dvh',
                 selection='read file',
                 starting_path=starting_path,
                 file_type=(('DVH Files', '*.dvh'),),
                 check_dflt=True,
                 check_disabled=False
                 ),
            dict(frame_title='DVH Template File',
                 file_k='template_file',
                 check_k='use_template',
                 starting_path=template_file_path,
                 selection='read file',
                 file_type=(('Excel Files', '*.xlsx'),),
                 check_dflt=True,
                 check_disabled=True
                 ),
            dict(frame_title='Save DVH Results As:',
                 file_k='save_form_file',
                 check_k='save_results',
                 starting_path=save_form_file_name,
                 selection='save file',
                 file_type=(('Excel Files', '*.xlsx'),),
                 check_dflt=True,
                 check_disabled=False
                 ),
            dict(frame_title='Save DVH Data As:',
                 file_k='save_data_file',
                 check_k='save_data',
                 starting_path=save_data_file_name,
                 selection='save file',
                 file_type=(('Excel Files', '*.xlsx'),),
                 check_dflt=False,
                 check_disabled=False
                 )
            ]
        return file_selection_list


    def file_selector(selection, file_k, check_k, frame_title,
                      starting_path=Path.cwd(), file_type=None,
                      check_dflt=True, check_disabled=False):
        if isinstance(starting_path, str):
            initial_dir = Path.cwd()
            initial_dir = starting_path
        elif starting_path.is_dir():
            initial_dir = str(starting_path)
            initial_file = ''
        else:
            initial_dir = str(starting_path.parent)
            initial_file = str(starting_path)

        if 'read file' in selection:
           browse = sg.FileBrowse(initial_folder=initial_dir,
                                  file_types=file_type)
        elif 'save file' in selection:
           browse = sg.FileSaveAs(initial_folder=initial_dir,
                                  file_types=file_type)
        elif 'read files' in selection:
           browse = sg.FilesBrowse(initial_folder=initial_dir,
                                   file_types=file_type)
        elif 'dir' in selection:
           browse = sg.FolderBrowse(initial_folder=initial_dir)
        else:
            raise ValueError(f'{selection} is not a valid browser type')
        file_selector_frame = sg.Frame(title=frame_title, layout=[
            [sg.Checkbox(text='', default=check_dflt, disabled=check_disabled,
                         key=check_k, pad=None, visible=True),
             sg.InputText(key=file_k, default_text=initial_file), browse]])
        return file_selector_frame

    file_selection_list = make_file_selection_list(**file_paths)
    file_frame_list = [[file_selector(**selection)]
                       for selection in file_selection_list]
    return file_frame_list


def make_window():
    status_widget = sg.Frame(title='Status',
                             title_location=sg.TITLE_LOCATION_TOP,
                             layout=[[sg.Multiline(key='Status',
                                                   size=(50,10),
                                                   pad=(10,10))]])
    window = sg.Window('Plan Checking',
                       finalize=True, resizable=True,
                       grab_anywhere=True, layout=[
        [sg.Column([
            [sg.Column([], key='File Selection')],
            [sg.Column([], key='Actions')],
            [status_widget]
            ])]])
    return window


def next_action(window, action_text='Submit'):
    window.Refresh()
    window['Submit'].Update(text=action_text)
    button, parameters = window.read()
    if button is None or 'Cancel' in button:
        sg.popup_error('Operation Canceled')
        return None
    return parameters

def print_to_window(window, status_element, text):
    status_element.print(text, text_color=None, background_color=None)
    window.refresh()


def get_actions_list():
    actions_list = [[sg.Submit(key='Submit', button_color=['black', 'green2']),
                     sg.Cancel(button_color=['black', 'red'])]]
    return actions_list


def drop_units(text: str)->float:
        number_value_pattern = (
            '(?P<value>'       # beginning of value integer group
            '[-+]?'            # initial sign
            '\d+'              # float value before decimal
            '[.]?'             # decimal Place
            '\d*'              # float value after decimal
            ')'                # end of value string group
            '.*'               # remainder of text
            '$'                # end of string
            )
        #find_num = re.compile(number_value_pattern)
        find_num = re.findall(number_value_pattern, text)
        if find_num:
            return float(find_num['value'])
        else:
            return text



if __name__ == '__main__':
    main()
