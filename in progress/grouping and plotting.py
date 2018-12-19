# -*- coding: utf-8 -*-
"""
Created on Thu Sep  6 10:18:58 2018

@author: gsalomon
"""
from pathlib import Path
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.widgets import RadioButtons

# %% 
data_index = ['Linac', 'SSD', 'Energy', 'Applicator', 'Shape', 'FieldSize', 'EquivSquare']

pdd_data = pd.concat([TR2_pdd_data, TR3_pdd_data])
pdd_data.loc[:,'SSD'] = pdd_data['SSD'].map(value2num)
grouped_data = pdd_data.groupby(data_index)
averaged_data = grouped_data.aggregate(np.mean)
data = averaged_data.unstack('Linac')

# %% 
dmax_data = data['R100']

dmax_data.reset_index(inplace=True)
group_names = ['SSD', 'Energy']
groups = dmax_data.groupby(group_names)
group_items = {}
for name in group_names:
    group_items[name] = tuple(dmax_data[name].unique())

# %% 
selection = {name: group_items[name][0] for name in group_names}
group_selection = tuple(selection[index_name] for index_name in group_names)
selected_data = groups.get_group(group_selection)

# %% 
plot_data = selected_data.sort_values(by='EquivSquare')

fig = plt.figure(figsize=(8, 8))
rdf_ax = plt.subplot(1, 1, 1)
plt.xlabel('Field Size')
plt.ylabel('d_max')
rdf_ax.set_autoscaley_on(True)
TR2_style = dict(color='b', linestyle='None', linewidth=2, marker='o', markersize=8)
TR3_style = dict(color='r', linestyle='None', linewidth=2, marker='v', markersize=8)
default_style = dict(color='b', linestyle='solid', linewidth=2, marker='None', markersize=8)
handle1 = plt.plot(plot_data['EquivSquare'], plot_data['TR2'], **TR2_style)[0]
handle2 = plt.plot(plot_data['EquivSquare'], plot_data['TR3'], **TR3_style)[0]

# %% 
a = plot_data[('EquivSquare', 'TR3')]
