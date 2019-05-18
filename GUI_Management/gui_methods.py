'''
Created on Apr 25 2019

@author: Greg Salomons
Misc GUI methods
'''

# Question Do I need the gui_methods module or should this go into other modules>

from typing import Union, List
import tkinter as tk
from tkinter import messagebox
from file_select_window import FileSelectGUI, SelectFile
from tree_view import TreeSelector

StringValue = Union[tk.StringVar, str]


def message_window(parent_window: tk.Widget, window_text: StringValue = '',
                   variable: StringValue = 'Nothing to say', **options):
    '''Display the sting message or variable content.'''
    if isinstance(variable, tk.StringVar):
        str_message = variable.get()
    else:
        str_message = str(variable)
    messagebox.showinfo(title=window_text, message=str_message,
                        parent=parent_window, **options)


def event_message(event, parent_window: tk.Wm,
                  window_text: StringValue = '', **options):
    selected = str(event.widget.focus())
    message_window(parent_window, window_text, selected, **options)


def select_list_2_str(select_list: List[str])-> str:
    return '\n'.join(select_list)


def quick_browse(master=None, path_variable=None, **file_params):
    if path_variable:
        file_params['starting_path'] = path_variable.get()
    select = SelectFile(**file_params)
    selected_path = select.get_path(master)
    if path_variable:
        path_variable.set(str(selected_path))
    return selected_path


