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
    '''Used to define an item level within a TK tree hierarchy.
    Class Attributes:
        value_list {List[str]} -- A list of all columns used in the TK tree.
    Instance Attributes:
        name {str} -- The name of the level.
        group_by {str} -- the name of the column associated with the level.
        tags {Tuple[str]} -- Tag names to associate with the level.
        group_values {Tuple[str]} -- The names of columns to display values
            for at the level.
    Methods:
        value_filter(values: List[Any])->List[Any] -- Replace unwanted column
            values with blanks.
    '''
    value_list: List[str]

    def __init__(self, level: ET.Element):
        '''Defines an item level within a TK tree hierarchy.
        Arguments:
            level {ET.Element} -- Level definition element from the GUI XML.
        '''
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
        '''Replace unwanted column values with blanks.
        Arguments:
            values {List[Any]} -- The full list of column values.
        Returns:
            List[Any] -- The list of values with the values for unwanted
                columns replaced with empty strings.
        '''
        filtered_values = [
            value if value_name in self.group_values else ''
            for value, value_name in zip(values, self.value_list)]
        return filtered_values


class TreeSelector(ttk.Treeview):
    '''Used to configure a ttk.Treeview widget.
    SubClass of ttk.Treeview.
    Instance Attributes not in ttk.Treeview:
        reference {ReferenceTracker} -- Lookup for resolving items references
            in the XML Treeview definition.
        groups {List[TreeLevel]} -- A list of level definitions for the tree
            hierarchy.
    Methods:
        value_filter(values: List[Any])->List[Any] -- Replace unwanted column
            values with blanks.
    '''
    def __init__(self, name: str, master: tk.Widget, **options):
        '''Initialize a TreeSelector widget.
        Arguments:
            name {str} -- The name of the widget.
            master {tk.Widget} -- The  parent widget.
            **options are passed through to ttk.Treeview unmodified.
        '''
        super().__init__(name=name, master=master, **options)
        self.reference: ReferenceTracker = None
        self.groups: List[TreeLevel] = None

    def build(self, tree_def: ET.Element, reference_set: ReferenceTracker):
        '''Configure and populate a TreeSelector widget based on the XML
            definition.
        Arguments:
            tree_def {ET.Element} -- The XML element defining the Tree Widget.
            reference_set {ReferenceTracker} -- Lookup for resolving items
                references in the XML Treeview definition.
        '''
        self.reference = reference_set
        column_set = tree_def.find('ColumnSet')
        self.initialize_columns(column_set)
        self.set_columns(column_set)
        level_set = tree_def.find('LevelSet')
        self.set_column_levels(level_set)
        item_set = self.reference.resolve( column_set.findtext('ItemData'))
        self.insert_tree_items(item_set)
        tag_set = tree_def.find('TagSet')
        self.set_tags(tag_set)

    def insert_tree_items(self, item_set: pd.DataFrame,
                          parent_item: str = '',
                          groups: List[TreeLevel] = None):
        '''Add the items to the tree.
        Arguments:
            item_set {pd.DataFrame} -- The Tree items to be displayed.
            parent_item {str} -- Reference to the parent item of the current
                item.
            groups {List[TreeLevel]} -- A list of level definitions for the
                tree hierarchy.
        '''
        def add_group_item(name: str, this_group: TreeLevel,
                           item_group: pd.DataFrame):
            '''Add a single item to the tree.
            Arguments:
                name {str} -- The item name.
                this_group {TreeLevel} -- The level group the item belongs to.
                item_group {pd.DataFrame} -- The group of items at the current
                    level.
            '''
            group_item = item_group.iloc[0]
            item_values = group_item[this_group.value_list]
            filtered_values = this_group.value_filter(item_values)
            item_tags = list(this_group.tags)
            item_tags.append(name)
            item_id = self.insert(parent_item, 'end', name, open=True,
                                  text=name, values=filtered_values,
                                  tags=item_tags)
            return item_id

        # Divide the item_set into level groups
        if not groups:
            groups = self.groups
        this_group = groups[0]
        remining_groups = groups[1:] if len(groups) > 1 else None
        group_by = this_group.group_by
        item_group = item_set.groupby(group_by)
        # Insert items at this group level and iterate through sub-levels
        for name, new_group in item_group:
            item_id = add_group_item(name, this_group, new_group)
            if remining_groups:
                self.insert_tree_items(new_group, item_id, remining_groups)
        pass

    def initialize_columns(self, column_set: ET.Element):
        '''
        Set order of values and columns (tuple of data_reference)
        Set Columns to display (tuple of column IDs)
        Arguments:
            column_set {ET.Element} -- The XML element that defines all of the
                Tree columns.
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
        Arguments:
            column_set {ET.Element} -- The XML element that defines all of the
                Tree columns.
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
        '''Generate list of groups
        Arguments:
            level_set {ET.Element} -- The XML element that defines the levels
                within the Tree structure.
        '''
        self.groups = [TreeLevel(level_def)
                       for level_def in level_set.findall('Level')]

    def set_tags(self, tag_set: ET.Element):
        '''Link tags with display formatting and events.
        Arguments:
            tag_set {ET.Element} -- The XML element that defines the tag
                related formatting and events.
        '''
        for tag_def in tag_set.findall('tag'):
            tag_name = self.reference.resolve(tag_def.attrib['name'])
            tag_appearance = tag_def.find('Appearance')
            if tag_appearance is not None:
                options = self.reference.resolve(tag_appearance.attrib)
                self.tag_configure(tag_name, **options)
            for binding in tag_def.findall(r'.//Bind'):
                event = self.reference.resolve(binding.findtext('event'))
                callback = self.reference.resolve(binding.findtext('callback'))
                self.tag_bind(tag_name, event, callback)
                # add option is not available for tag_bind
        pass
