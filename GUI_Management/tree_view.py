"""
Created on Mon Apr 19 2019

tree_view widget methods

@author: Greg Salomons
"""
from typing import List, Union, Any
import tkinter as tk
from tkinter import ttk
import xml.etree.ElementTree as ET
import pandas as pd
from GUI_Management.object_reference_management import ReferenceTracker
from data_utilities import true_iterable


StringValue = Union[tk.StringVar, str]


# TODO add frame widget that can include scroll bars for tree

class TreeLevel():
    value_list: List[str]

    def __init__(self, level: ET.Element):
        self.name = level.attrib['name']
        self.group_by = level.findtext('GroupBy')
        tag_set = level.findtext('Tags').split()
        if true_iterable(tag_set):
            self.tags = tuple(tag_set)
        else:
            self.tags = (tag_set,)
        display_set = level.findtext('DisplayValues').split()
        if true_iterable(display_set):
            self.group_values = tuple(display_set)
        else:
            self.group_values = (display_set,)

    def value_filter(self, values: List[Any])->List[Any]:
        filtered_values = [
            value if value_name in self.group_values else ''
            for value, value_name in zip(values, self.value_list)]
        return filtered_values


class TreeSelector(ttk.Treeview):
    def __init__(self, name: str, master: tk.Tk, **options):
        super().__init__(name=name, master=master, **options)
        self.reference: ReferenceTracker = None
        self.groups: List[TreeLevel] = None

    def build(self, tree_def: ET.Element, reference_set: ReferenceTracker):
        self.reference = reference_set
        column_set = tree_def.find('ColumnSet')
        self.initialize_columns(column_set)
        self.set_columns(column_set)
        level_set = tree_def.find('LevelSet')
        self.set_column_levels(level_set)
        item_set = self.reference.lookup_references(
                    column_set.findtext('ItemData'))
        self.insert_tree_items(item_set)
        tag_set = tree_def.find('TagSet')
        self.set_tags(tag_set)

    def insert_tree_items(self, item_set: pd.DataFrame,
                          parent_item: str = '',
                          groups: List[TreeLevel] = None):
        '''Add the template items to the workbook.
        '''
        def add_group_item(name: str, this_group: TreeLevel, item_group):
            group_item = item_group.iloc[0]
            item_values = group_item[this_group.value_list]
            filtered_values = this_group.value_filter(item_values)
            item_tags = list(this_group.tags)
            item_tags.append(name)
            item_id = self.insert(parent_item, 'end', name, open=True,
                                  text=name, values=filtered_values,
                                  tags=item_tags)
            return item_id

        if not groups:
            groups = self.groups
        this_group = groups[0]
        remining_groups = groups[1:] if len(groups) > 1 else None
        group_by = this_group.group_by
        item_group = item_set.groupby(group_by)
        for name, new_group in item_group:
            item_id = add_group_item(name, this_group, new_group)
            if remining_groups:
                self.insert_tree_items(new_group, item_id, remining_groups)
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
            if 'y' in show:
                displaycolumns.append(column_name)
            elif 'tree' in show:
                column_name = '#0'
            columns.append(column_name)
        self['columns'] = columns
        self['displaycolumns'] = displaycolumns
        TreeLevel.value_list = value_list

    def set_columns(self, column_set: ET.Element):
        '''
        Set formatting for values and headers
        '''
        for column_def in column_set.findall('Column'):
            column_name = column_def.attrib['name']
            column_data = column_def.find('ColumnDef')
            show = column_def.attrib['show']
            if 'tree' in show:
                column_name = '#0'
            if column_data is not None:
                self.column(column_name, **column_data.attrib)
            header_data = column_def.find('HeaderDef')
            if header_data is not None:
                self.heading(column_name, **header_data.attrib)
        pass

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
        for tag_def in tag_set.findall('tag'):
            tag_name = self.reference.lookup_references(tag_def.attrib['name'])
            tag_appearance = tag_def.find('Appearance')
            if tag_appearance is not None:
                options = self.reference.lookup_references(
                    tag_appearance.attrib)
                self.tag_configure(tag_name, **options)
            for binding in tag_def.findall(r'.//Bind'):
                event = self.reference.lookup_references(
                    binding.findtext('event'))
                callback = self.reference.lookup_references(
                    binding.findtext('callback'))
                self.tag_bind(tag_name, event, callback)
                # add option is not available for tag_bind
        pass


