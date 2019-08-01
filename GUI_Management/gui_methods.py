'''
Created on Apr 25 2019

@author: Greg Salomons
Misc GUI methods
'''

from typing import Union, List
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from GUI_Management.file_select_window import FileSelectGUI, SelectFile
from GUI_Management.tree_view import TreeSelector

StringValue = Union[tk.StringVar, str]

def test_message(message_text):
    '''Display the string as a test message.
    Arguments:
        message_text {str} -- The message to display
    '''
    messagebox.showinfo(title='Testing', message=message_text)


def message_window(parent_window: tk.Wm, window_text: StringValue = '',
                   variable: StringValue = 'Nothing to say', **options):
    '''Display the string message or variable content.
    Arguments:
        parent_window {tk.Wm} -- The parent window for the message box.
    Keyword Arguments:
        window_text {StringValue} -- The title of the message window.
            (default = '')
        variable {StringValue} -- The message string or a TK variable instance.
            If a variable instance is given the variable value will be
            displayed as a string. (default = 'Nothing to say')
    '''
    if isinstance(variable, tk.StringVar):
        str_message = variable.get()
    else:
        str_message = str(variable)
    messagebox.showinfo(title=window_text, message=str_message,
                        parent=parent_window, **options)


def event_message(event: tk.Event, parent_window: tk.Wm,
                  window_text: StringValue = '', **options):
    '''Display a message from an event call.
    Arguments:
        event {tk.Event} -- The event that called the message.
        parent_window {tk.Wm} -- The parent window for the message box.
    Keyword Arguments:
        window_text {StringValue} -- The title of the message window.
            (default = '')
        **options arguments are passed to the message_window unmodified.
    '''
    selected = str(event.widget.focus())
    message_window(parent_window, window_text, selected, **options)


def select_list_2_str(select_list: List[str])-> str:
    '''Convert a list of strings to a string with "New Lines" between each item.
    Arguments:
        select_list {List[str]} -- The list of strings to be converted.
    Returns:
        str -- A string with "New Lines" between each item fropm the list.
    '''
    return '\n'.join(select_list)


def quick_browse(master: tk.Wm = None, path_variable: tk.StringVar = None,
                 **file_params)->Path:
    '''Call a "File Browser" with the specified parameters.
    Keyword Arguments:
        master {tk.Wm} -- The parent window for the file browser.
            (default: {None})
        path_variable {tk.StringVar} -- A Tk Variable containing a statring
            path for the file browser. (default: {None})
    Returns:
        {Path} -- The Path selected by the browser.
    '''
    if path_variable:
        file_params['starting_path'] = path_variable.get()
    select = SelectFile(**file_params)
    selected_path = select.get_path(master)
    # FIXME canceling the browser will overwrite the original value
    if path_variable:
        path_variable.set(str(selected_path))
    return selected_path


def status_update(status_widget: tk.Text, status_text: str):
    '''Append text to a status text widget.
    Arguments:
        status_widget {tk.Text} -- The status widget to send the text to.
        status_text {str} -- The text to append
    '''
    status_text = '\n' + status_text
    status_widget.insert('end', status_text)
    status_widget.update_idletasks()


def init_progress(progress_widget: ttk.Progressbar, max_level: int):
    '''Initialize a progress bar.
    Arguments:
        progress_widget {ttk.Progressbar} -- The progress bar to be
            initialized.
        max_level {int} -- The maximum level for the progress bar.
    '''
    progress_widget.configure(maximum=max_level)
    progress_widget["value"] = 0
    progress_widget.update_idletasks()


def progress_update(progress_variable: tk.IntVar, progress_level: int):
    '''Update a progress bar variable.
    Arguments:
        progress_variable {tk.IntVar} -- A TK variable linked to a
            progress bar.
        progress_level {int} -- The progress value to set.
    '''
    progress_variable.set(progress_level)


def progress_step(progress_widget: tk.Widget, increment: int = 1):
    '''Increment the progress bar.
    Arguments:
        progress_widget {ttk.Progressbar} -- The progress bar to be
            initialized.
    Keyword Arguments:
        increment {int} -- The incremental step size to use.
            (default: {1})
    '''
    progress_widget.step(increment)
    progress_widget.update_idletasks()
