'''
Created on Apr 25 2019

@author: Greg Salomons
Misc GUI methods
'''

# Question Do I need the gui_methods module or should this go into other modules>

from typing import Union, List
import tkinter as tk
from tkinter import messagebox
from file_select_window import FileSelectGUI
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

def update_selection(event, variable: StringValue):
    select_list = [str(item) for item in event.widget.selection()]
    select_str = list_2_str(select_list)
    variable.set(select_str)


def list_2_str(str_list: List[str])-> str:
    return '\n'.join(str_list)


def event_message(event, parent_window: tk.Wm,
                  window_text: StringValue = '', **options):
    selected = str(event.widget.focus())
    message_window(parent_window, window_text, selected, **options)


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
                               for item in show_vars]
            item_id = template_selector.insert(file_ref, 'end', name, text=name,
                                          values=template_values,
                                          tags=('Template',))
            template_ref[name] = item_id


def file_select(event):
    selected_file = event.widget.focus()
    file_templates = event.widget.get_children(item=selected_file)
    select_list = event.widget.selection()
    #select_str = '\n'.join([str(item) for item in file_templates])
    #heading = '{} Selected:'.format(str(selected_file))
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
