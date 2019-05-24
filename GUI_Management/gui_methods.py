'''
Created on Apr 25 2019

@author: Greg Salomons
Misc GUI methods
'''

from typing import Union, List
import tkinter as tk
from tkinter import messagebox
from file_select_window import FileSelectGUI, SelectFile
from tree_view import TreeSelector

StringValue = Union[tk.StringVar, str]


def test_message(message_text):
    '''Display the sting message or variable content.'''
    messagebox.showinfo(title='Testing', message=message_text)
    

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


def status_update(status_widget: tk.Widget, status_text: str):
    status_text = '\n' + status_text
    status_widget.insert('end', status_text)


def init_progress(progress_widget: tk.Widget, progress_variable: tk.IntVar,
                  max_level: int):
    #test_message('Initialize Progress bar Max: %d' %max_level)
    progress_widget.configure(maximum=max_level)
    progress_widget["value"]=1
    progress_variable.set(1)


def progress_update(progress_variable: tk.IntVar, progress_level):
    progress_variable.set(progress_level)

def progress_step(progress_widget: tk.Widget, increment: int = 1):
    #test_message('Step Progress bar by: %d' %increment)
    progress_widget.step(increment)
