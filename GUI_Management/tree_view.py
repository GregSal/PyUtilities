"""
Created on Mon Apr 19 2019

tree_view widget methods

@author: Greg Salomons
"""
from typing import Union, Callable, List, Dict, NamedTuple, Tuple, Any
from collections import OrderedDict, namedtuple
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import xml.etree.ElementTree as ET
from file_utilities import set_base_dir
import pandas as pd

class TreeLevel():
    value_list: List[str]
    def __init__(self, group_name: str, tags: Tuple[str] = None,
                 add_group_item: bool = False, group_values: List[str] = None):
        self.group_name = group_name
        self.tags = tags
        self.add_group_item = add_group_item
        self.group_values = group_values

    def value_filter(self, values: List[Any])->List[Any]:
        filtered_values = [
            value if value_name in  self.group_values else None
            for value, value_name in zip(values, self.value_list)]
        return filtered_values


# TODO generalize initialize_tree
class TreeSelector(ttk.Treeview):
    def __init__(self, tree_def: ET.Element, name: str, master: tk.Tk, **options):
        super().__init__(master=master, **kw)



def insert_tree_items(tree, item_set: pd.DataFrame, groups: List[TreeLevel],
                      parent_item: str = '',
                      reference_set: Dict[str, str] = None)->Dict[str, str]:
    '''Add the template items to the workbook.
    '''
    if not reference_set:
        reference_set = dict()
    this_group = groups[0]
    remining_groups = groups[1:] if len(groups)>1 else None
    group_name = this_group.group_name
    value_selector = this_group.group_values
    item_group = item_set.groupby(group_name)
    # FIXME finish adding option to make a group level item
    group_item = item_group.first().iloc[0]
    group_values = group_item[this_group.value_list]
    filtered_values = this_group.value_filter(group_values)
    name = group_item.name
    item_id = tree.insert(parent_item, 'end', name, open=True, text=name,
                        values=filtered_values, tags=group_item.tags)

    for name, items in item_group:
        value_list = items[this_group.value_list]
        filtered_values = this_group.value_filter(value_list)
        item_id = tree.insert(parent_item, 'end', name, open=True, text=name,
                                values=filtered_values, tags=(group_name,))  # FIXME Add group_name as default tag
        reference_set[name] = item_id
        if remining_groups:
            reference_set = insert_tree_items(tree, items, remining_groups,
                                              item_id, reference_set)
    return reference_set


def initialize_columns(column_set):
    '''
    Set order of values and columns (tuple of data_reference)
    Set Columns to display (tuple of column IDs)
    '''
    value_list = list()
    columns = list()
    displaycolumns = list()
    for column_def in column_set.findall('Column'):
        column_dict = column_def.attrib
        value_name = column_dict['data_reference']
        column_name = column_dict['name']
        show = column_dict['show']
        value_list.append(value_name)
        columns.append(column_name)
        if 'y' in show:
            displaycolumns.append(name)
    template_selector['columns'] = columns
    template_selector['displaycolumns'] = displaycolumns
    return value_list

def set_columns(tree: ttk.Treeview, column_set: ET.Element):
    '''
    Set formatting for values and headers
    '''
    for column_def in column_set.findall('Column'):
        column_name = column_dict.attrib['name']
        column_dict = column_def.find('ColumnDef').attrib
        header_dict = column_def.find('HeaderDef').attrib
        tree.column(column_name, **column_dict)
        tree.heading(column_name, **header_dict)





    # TODO Need rules to generate tags
    template_selector.tag_configure('File', foreground='blue',
                                background='light grey', image=file_image)
    template_selector.tag_configure('Template', image=template_image)
    template_selector.tag_bind('File', '<Double-ButtonRelease-1>', callback=file_select)  # the item clicked can be found via tree.focus()
    template_selector.tag_bind('Template', '<<TreeviewSelect>>', callback=template_select)  # the item clicked can be found via tree.focus()




# TODO add option to include scroll bars in tree


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