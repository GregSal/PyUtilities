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
from GUI_Management.object_reference_management import ReferenceTracker
import pandas as pd

class TreeLevel():
    value_list: List[str]
    def __init__(self, level: ET.Element):
        self.name = level_def.attrib['name']
        self.group_by = list(level.findtext('GroupBy'))
        self.tags = list(level.findtext('Tags'))
        self.group_values = list(level.findtext('DisplayValues'))

    def value_filter(self, values: List[Any])->List[Any]:
        filtered_values = [
            value if value_name in  self.group_values else None
            for value, value_name in zip(values, self.value_list)]
        return filtered_values


# TODO generalize initialize_tree
class TreeSelector(ttk.Treeview):
    def __init__(self, name: str, master: tk.Tk, **options):
        super().__init__(name=name, master=master, **options)

    def build(self, reference_set: ReferenceTracker, tree_def: ET.Element,):
        self.reference = reference_set
        self.reference.lookup_references(ref_set)
        self.item_set = dict()
        self.groups: List[TreeLevel] = None
        column_set = tree_def.find('ColumnSet')
        self.initialize_columns(column_set)
        self.set_columns(column_set)
        level_set = tree_def.find('LevelSet')
        self.set_column_levels(level_set)

    def insert_tree_items(self, item_set: pd.DataFrame,
                          groups: List[TreeLevel] = None,
                          parent_item: str = ''):
        '''Add the template items to the workbook.
        '''

        def add_group_item(name: str, this_group: TreeLevel, item_group):
            group_item = item_group.first().iloc[0]
            item_values = group_item[this_group.value_list]
            filtered_values = this_group.value_filter(item_values)
            item_tags=list(group_item.tags).append(name)
            item_id = self.insert(parent_item, 'end', name, open=True,
                                  text=name, values=filtered_values,
                                  tags=item_tags)
            return item_id

        if not groups:
            groups = self.groups
        this_group = groups[0]
        remining_groups = groups[1:] if len(groups)>1 else None
        item_group = item_set.groupby(group_by)
        group_by = this_group.group_by
        for name, new_group in item_group:
            item_id = add_group_item(name, this_group, new_group)
            self.item_set[name] = item_id
            if remining_groups:
                insert_tree_items(self, item_set=new_group,
                                  groups=remining_groups,
                                  parent_item=item_id)
        pass

    def initialize_columns(self, column_set: ET.Element):
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
        self['columns'] = columns
        self['displaycolumns'] = displaycolumns
        TreeLevel.value_list = value_list

    def set_columns(self, column_set: ET.Element):
        '''
        Set formatting for values and headers
        '''
        for column_def in column_set.findall('Column'):
            column_name = column_def.attrib['name']
            column_dict = column_def.find('ColumnDef').attrib
            header_dict = column_def.find('HeaderDef').attrib
            self.column(column_name, **column_dict)
            self.heading(column_name, **header_dict)

    def set_column_levels(self, level_set: ET.Element):
        '''
        Generate list of groups
        '''
        self.groups = [TreeLevel(level_def)
                  for level_def in level_set.findall('Level')]

    def set_tags(self, tag_set: ET.Element):
        '''
        Set formatting for values and headers
        '''
        for tag_def in column_set.findall('tag'):
            tag_name = tag_def.attrib['name']
            options = tag_def.find('Appearance').attrib
            self.tag_configure(tag_name, **options)
            for binding in tag_def.findall('Bind'):
                event = binding.attrib['event']
                callback = binding.attrib['callback']
                template_selector.tag_bind(tag_name, event, callback)


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