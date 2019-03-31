"""
Created on Mon Jan 7 2018

@author: Greg Salomons
"""
from typing import Union, Callable, List, Dict, Tuple, Any
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import utilities_path
from file_utilities import set_base_dir
from SelectTemplates import import_template_list
from spreadsheet_tools import load_reference_table

data_folder = r'Work\Structure Dictionary\Template Spreadsheets'
template_list_file_name='Template List.xlsx'

projects_path = set_base_dir(sub_dir=r'Python\Projects')
icon_folder = r'EclipseRelated\EclipseTemplates\ManageStructuresTemplates\icons'
icon_path = projects_path / icon_folder
file_icon = icon_path / 'Box2.png'
template_icon = icon_path / 'Blueprint2.png'

class TemplateData():
    '''
    '''
    data_fields = ['TemplateID', 'TemplateCategory', 'TreatmentSite',
                   'workbook_name', 'sheet_name', 'modification_date',
                   'Number_of_Structures', 'Description', 'Diagnosis',
                   'Author', 'Columns', 'template_file_name', 'Status',
                   'TemplateType', 'ApprovalStatus']

    default_show_fields = ['workbook_name', 'TemplateID', 'TemplateCategory',
                           'TreatmentSite', 'modification_date',
                           'Description', 'Status']

    file_info_args = ('file_name', 'sub_dir', 'sheet_name')
    table_info_args = ('starting_cell', 'header')
    selections_args = ('unique_scans', 'select_columns', 'criteria_selection')

    default_references = dict(
        file_name='Template List.xlsx',
        sub_dir=r'Work\Structure Dictionary\Template Spreadsheets',
        sheet_name='templates',
        starting_cell='A1',
        header=1,
        unique_scans=['TemplateID'],
        select_columns=data_fields,
        criteria_selection={
            'workbook_name': 'Basic Templates.xlsx',
            'Status': 'Active'
            }
        )
    def __init__(self, **kwargs):
        '''
        '''
        self.template_file_info = self.set_args(self.file_info_args, kwargs)
        self.template_table_info = self.set_args(self.table_info_args, kwargs)
        self.template_selections = self.set_args(self.selections_args, kwargs)
        self.template_data = self.get_template_data()

    def set_args(self, arg_list: Tuple[str],
                 arguments: Dict[str, Any])->Dict[str, Any]:
        '''
        '''
        args_dict = dict()
        for arg in arg_list:
            args_dict[arg] = arguments.get(arg, self.default_references[arg])
        return args_dict

    def get_template_data(self):
        '''
        '''
        template_data = load_reference_table(
            self.template_file_info,
            self.template_table_info,
            **self.template_selections)
        return template_data

    def get_workbook_data(self):
        '''
        '''
        return self.template_data.groupby('workbook_name')


def print_selection():
        select_list = [str(item) for item in template_selector.selection()]
        select_str = '\n'.join(select_list)
        messagebox.showinfo('Selected Templates', select_str)


def print_select(event):
        selected = str(event.widget.focus())
        messagebox.showinfo('Selected File', selected)


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
                               for item in test_show_vars]
            id = template_selector.insert(file_ref, 'end', name, text=name,
                                          values=template_values,
                                          tags=('Template',))
            template_ref[name] = id

icon_path = Path(r'.\icons')
file_icon = icon_path / 'Box2.png'
template_icon = icon_path / 'Blueprint2.png'


root = tk.Tk()
root.title("Template Selection")
style = ttk.Style()
style.theme_use('vista')
master = tk.Frame(root)
file_image = tk.PhotoImage(file=file_icon)
template_image = tk.PhotoImage(file=template_icon)

template_selector = ttk.Treeview(master)
scrollbar_horizontal = ttk.Scrollbar(master, orient="horizontal",
                                     command=template_selector.xview)
scrollbar_vertical = ttk.Scrollbar(master, orient="vertical",
                                   command=template_selector.yview)
template_selector.configure(
    xscrollcommand=scrollbar_horizontal.set,
    yscrollcommand=scrollbar_vertical.set)

# resize = ttk.Sizegrip(template_selector)

test_vars = ['workbook_name', 'TemplateID', 'TemplateCategory']
test_show_vars = ['TemplateID', 'TemplateCategory']
test_data = TemplateData()
active_templates = test_data.get_template_data()
workbooks = test_data.get_workbook_data()

template_selector['columns'] = test_show_vars
#template_selector['displaycolumns'] = test_show_vars
#template_selector.column('TemplateID', width=100, anchor='center')
#template_selector.heading('workbook_name', text='File')
template_selector.heading('#0', text='Structure Templates')
template_selector.heading('TemplateID', text='ID')
template_selector.heading('TemplateCategory', text='Category')

insert_template_items(template_selector, workbooks, test_vars)
template_selector.tag_configure('File', foreground='blue',
                                background='light grey', image=file_image)
template_selector.tag_configure('Template', image=template_image)
template_selector.tag_bind('File', '<Double-ButtonRelease-1>', callback=file_select)  # the item clicked can be found via tree.focus()
#template_selector.tag_bind('Template', '<<TreeviewSelect>>', callback=template_select)  # the item clicked can be found via tree.focus()


template_selector.grid(row=0, column=0, sticky='nsew')  #  , ipady=50, ipadx=200
scrollbar_horizontal.grid(row=1, column=0, sticky="we")
scrollbar_vertical.grid(row=0, column=1, sticky="ns")
master.grid(row=0, column=0, columnspan=3, sticky='nsew')
selection_button = ttk.Button(root, text='Show Selected', command=print_selection)
selection_button.grid(row=2, column=1, columnspan=1)



root.mainloop()



#values = template_selector.selection()
#showinfo(title, message, options)
#whatever_you_do = "Whatever you do will be insignificant, but it is very important that you do it.\n(Mahatma Gandhi)"
#msg = tk.Message(master, text = whatever_you_do)
#msg.config(bg='lightgreen', font=('times', 24, 'italic'))
#msg.pack()


# root.geometry('350x200')

# Same thing, but inserted as first child:
# template_selector.insert('', 0, 'gallery', text='Applications')
# Treeview chooses the id:
# id = template_selector.insert('', 'end', text='Tutorial')
# tree.move('widgets', 'gallery', 'end')  # move widgets under gallery
# tree.detach('widgets')
# tree.delete('widgets')
# tree.item('widgets', open=True)
# isopen = tree.item('widgets', 'open')
# template_selector['columns'] = ('size', 'modified', 'owner')
# template_selector.column('size', width=100, anchor='center')
# template_selector.heading('size', text='Size')
# template_selector.set('widgets', 'size', '12KB')
# size = template_selector.set('widgets', 'size')
# template_selector.insert('', 'end', text='Listbox', values=('15KB Yesterday mark'))
# template_selector.insert('', 'end', text='button', tags=('ttk', 'simple'))
# template_selector.tag_configure('ttk', background='yellow')
# template_selector.tag_bind('ttk', '<1>', itemClicked)  # the item clicked can be found via tree.focus()
