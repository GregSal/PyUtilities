# -*- coding: utf-8 -*-
"""
Created on Wed Oct  2 22:38:15 2019

@author: Greg
Read Eclipse Text Print
"""

# %% Imports etc
from pathlib import Path
import pandas as pd
import numpy as np

from typing import TypeVar, Dict, List, TextIO, Any
HeaderValue = TypeVar('HeaderValue', str, float, int)
Data = TypeVar('Data', pd.DataFrame, pd.Series, np.ndarray)


from text_file_utilities import read_file_header, next_line



base_path = Path.cwd()
data_path = base_path / r'Testing\Test Data'
printout_file_path = data_path / 'AG30N6XF20.txt'

text_data = dict()
file = printout_file_path.open()
data = read_file_header(file, text_data, stop_marker='FieldId')
field_data = dict()
field_data = read_file_header(file, field_data, stop_marker='RefPointId')
point_data = dict()
point_data = read_file_header(file, point_data, stop_marker='FieldRefPointEffectiveDepth')


print(point_data)