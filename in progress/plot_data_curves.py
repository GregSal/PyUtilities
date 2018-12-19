# -*- coding: utf-8 -*-
"""
Created on Sat Jul 14 20:36:33 2018

@author: Greg
"""

from data_groups import SubGroup
from data_groups import DataGroups

from typing import Dict, List, Any, Callable
Handle = Any
GraphList = List[Dict[str, Any]]
CurveList = List[Dict[str, Any]]
SelectorList = List[Dict[str, Any]]
Updater = Callable[str]

from functools import partial
import pandas as pd
import numpy as np
from typing import TypeVar, Dict, List, TextIO
Data = TypeVar('Data', pd.DataFrame, pd.Series, np.ndarray)

import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons

class CurvePlot(object):
    '''Plot parameters for individual data set.
    '''
    default_style = dict(label='', color='b',
                         linestyle='solid', linewidth=2,
                         marker='None', markersize=8)

    def __init__(self, ax_handle: Handle, column_names: Dict[str, str],
                 name: str, label: str = None,
                 style: Dict[str, int] = None):
        '''Set plot parameters
        column_names is dict two items: ['X','Y']; their values are the names
        of the corresponding columns in the Data group.
        '''
        self.handle = None
        self.data = None
        self.name = name
        self.ax_handle = ax_handle
        self.column_names = column_names
        if style:
            self.parameters = self.default_style.update(style)
        if label:
            self.parameters['label'] = label
        else:
            self.parameters['label'] = name

    def plot_curve(self, data: SubGroup):
        '''Plot data in a figure axis.
        Current data is updated if already present
        '''
        self.data = data.get_data_set(self.name, self.column_names)
        plt.sca(self.ax_handle)
        if self.handle:
            self.handle.set_xdata(self.data.x())
            self.handle.set_ydata(self.data.y())
        else:
            self.handle = plt.plot(self.data.x(), self.data.y(),
                                   **self.parameters)[0]


    def range(self, axis='X'):
        '''Return the maximum and minimum x values for the curve.
        '''
        return self.data.range(self, axis)


class Graph(object):
    '''Parameters for a particular graph
    Args:
        curve_list(CurveList): Parameters for each curve to be plotted.
            Contains the following items:
                name(str): The name if the curve.
                label(str): A label for the curve legend, if not given name will be
                    used.
                column_names(Dict[str, str]): The names of the 'X' and 'Y'
                    columns in data.
                style(Dict(str, int):  The plot style parameters.
                      The defaults are:
                          color='b',
                          linestyle='solid', linewidth=2,
                          marker='None', markersize=8
    '''
    default_labels = {'Title': 'Graph', 'X': 'X', 'Y': 'Y'}
    def __init__(self, handle: Handle, name: str, curve_list: CurveList,
                 data: SubGroup = None,
                 title: str = None, xlabel: str = None, ylabel: str = None):
        self.handle = handle
        self.name = name
        self.data = data
        self.curves = dict()

        self.labels = self.default_labels
        if title:
            self.labels['Title'] = title
        if xlabel:
            self.labels['X'] = xlabel
        if ylabel:
            self.labels['Y'] = ylabel

        self.build_graph(curve_list)

    def axes_settings(self):
        '''Set axes scales etc.
        '''
        self.handle.set_autoscaley_on(True)

    def build_graph(self, curve_list: CurveList):
        '''Setup the graph.
        '''
        plt.xlabel(self.labels['X'])
        plt.ylabel(self.labels['Y'])
        plt.title(self.labels['Title'])
        self.axes_settings()
        for curve_param in curve_list:
            curve_name = curve_param['name']
            self.curves[curve_name] = CurvePlot(self.handle, **curve_param)

    def plot_curves(self, plot_data: SubGroup):
        '''Plot data in a figure axis.
        Current data is updated if already present
        '''
        ax_handle = self.handle
        plt.sca(ax_handle)
        for curve in self.curves.values():
            curve.plot_curve(plot_data)
        plt.autoscale()
        ax_handle.relim()
        ax_handle.autoscale_view()

    def set_x_range(self):
        '''set the x range based on the max and min of the data.
        '''
        x_min = None
        x_max = None
        for curve in self.curves.values():
            (curve_x_min, curve_x_max) = curve.range()
            if (not x_min) or (curve_x_min < x_min):
                x_min = curve_x_min
            if (not x_max) or (curve_x_max > x_max):
                x_max = curve_x_max
        self.handle.set_xlim(x_min, x_max)


class DataSelector(object):
    '''references to radio button selectors for plot data selection'
    '''
    selector_bottom = 0.3
    item_spacing = 0.03
    axcolor = 'lightgoldenrodyellow'

    def __init__(self, name: str, updater: Updater, selection_items):
        self.name = name
        self.handle = None
        self.items_list = selection_items
        self.current = selection_items[0]
        self.updater = updater
        self.build()

    def build(self):
        '''Add radial button selector to the figure.
        '''
        num_items = len(self.items_list)
        bottom = self.selector_bottom
        height = num_items*0.03
        self.selector_bottom = bottom + height + 2 * self.item_spacing
        rax = plt.axes([0.05, bottom, 0.15, height], facecolor=self.axcolor)
        handle = RadioButtons(rax, self.items_list)
        selector_index = self.items_list.index(self.current)
        handle.set_active(selector_index)
        handle.on_clicked(self.updater)
        self.handle = handle

    def set(self, selection):
        '''Initialize Radio Buttons.
        '''
        selector_index = self.items_list.index(selection)
        self.handle.set_active(selector_index)


class Fig(object):
    '''Contains handles and parameters for the RDF figure.
    Usually there will be only one instance.
    '''

    def __init__(self, data_set: DataGroups,
                 graph_list: GraphList,
                 selector_list: SelectorList = None,
                 title_format='{}, {}'):
        '''Create a figure containing a set of graphs and selectors that will
        plot a data group.
        Attributes:
            data_set (DataGroups): the data groups to be plotted.
            graph_list (GraphList): A list of graph definitions each consisting
                of a dictionary with the following items:
                    'name' (str): The reference name of the graph.
                    'curve_list' (CurveList): A list of curve definitions.
                    'title' (str): The graph title
                    'xlabel' (str): The x axis title
                    'ylabel' (str): The y axis title
            selector_list (SelectorList): A list of selector definitions.
            title_format (str): A string compatible with str.format.
                        '{name}' items reference group names
        '''
        self.plot_groups = data_set
        self.title_format = title_format
        self.figure_size = (8, 8)
        self.graphs = dict()
        self.selectors = dict()
        self.x_range = None
        self.handle = plt.figure(figsize=self.figure_size)
        self.define_fig(graph_list, selector_list)
        self.plot_group()

    def add_graphs(self, graph_list):
        '''Add the defined graphs to the figure.
        '''
        num_graphs = len(graph_list)
        for (index, graph_param) in enumerate(graph_list):
            graph_name = graph_param['name']
            graph_handle = plt.subplot(num_graphs, 1, index)
            self.graphs[graph_name] = Graph(graph_handle, **graph_param)

    def add_selectors(self, selector_list: SelectorList):
        '''Add the defined selectors to the figure.
        '''
        plt.subplots_adjust(left=0.3)
        for selector_param in selector_list:
            selector_name = selector_param['name']
            updater = partial(self.update_plot, selector_name)
            selection_items = self.plot_groups[selector_name]
            self.selectors[selector_name] = DataSelector(selector_name, updater, selection_items)

    def define_fig(self, graph_list: GraphList,
                   selector_list: SelectorList = None):
        '''Create the Graph and data selector definitions for the Figure.
        '''
        self.add_graphs(graph_list)
        if selector_list:
            self.add_selectors(selector_list)

    def plot_group(self, selection: Dict[str, Any] = None):
        '''Plot data for a specific group selection.
        '''
        plot_data = self.plot_groups.select_subgroup(selection)
        for graph in self.graphs.values():
            graph.plot_curves(plot_data)
        title = self.title_format.format(self.plot_groups.current_selection)
        plt.suptitle(title, fontsize=16)
        # plt.draw()
        self.handle.canvas.draw_idle()

    def update_plot(self, selection_key: str, selection_value: str):
        '''Update plot data based on a selector change.
        '''
        selection = self.plot_groups.current_selection
        selection[selection_key] = selection_value
        self.plot_group(selection)
