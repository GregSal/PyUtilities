'''
Created on Oct 19 2018
@author: Greg Salomons
A collection of utility functions for manipulating DataFrame and List data.

get_profile_limit(profile_curves, step_size)
    Returns the maximum distance from the profile curve with the smallest
        range rounded down to the next smallest step size.
value_parse(value_string)
    Convert a string number with units to a tuple of (number, unit).
value2num(value_string: str)->float
    Convert a string type value to a number by removing the unit
    portion of the string.
    The number portion of the string is identified by a space between the
    number and the unit. If there is no space, in value_string, it will try
    converting value_string to a float.
    Args:
        value_string: A string containing a number or a number a space and a
            unit.
    Raises:
        ValueError
    Returns:
        A tuple:
            The number as float,
            The unit as string
select_data(data: pd.DataFrame,
                criteria_selection: Dict[str, Any] = None,
                unique_scans: List[str] = None,
                select_columns: List[str] = None,
                index_columns: List[str] = None)->Data
    Select the desired data columns.
    Selection is based on column names and on column specific conditions.
    Args:
        data: A Pandas DataFrame containing one or more columns.
        unique_scans: A list of names of the columns to be used to define
            unique data elements.  If supplied, duplicates will be removed.
        select_columns: A list of names of the columns to be selected.
        criteria_selection: A dictionary where the key is a column name and the
            value is a condition to select for on that column.
        index_columns: A list of names of the columns to be set as the index.
    Raises:
        KeyError
    Return
        A copy of the supplied DataFrame or a Series containing the selected
        rows and columns.
process_curve(curve: pd.DataFrame, data_names: Dict[str,str],
                  min_range: float = None, max_range: float = None,
                  step_size: float = 1.0, norm_point: float = None,
                  kind='cubic')
    Interpolate and normalize a curve.
    Uses scipy.interpolate.interp1d.
    The X values in curve must extend to or beyond min_range norm_point, and
        max_range.
    If min_range or max_range is not given the minimum/maximum X values will
        be used as endpoints for the interpolation.
    If norm_point is not given no normalization will be done.
    Args:
        curve: A Pandas DataFrame containing at least 2 columns.
        data_names: A dictionary containing the names of the X and Y columns
            to be used.
                Must contain keys 'X' and 'Y'.
        min_range (optional): The minimum X value to use in the interpolation.
        max_range (optional): The maximum X value to use in the interpolation.
        step_size (optional): The X step size for the interpolation.
            Default is 1.0.
        norm_point (optional): The X point to be set to 100% normalization.
        kind (optional): The interpolation method to use.  Can be one of:
            'cubic', 'linear', 'nearest', 'zero', 'slinear', 'quadratic',
            ‘previous’ or ‘next’. Default is ‘cubic’.
    Returns:
        Two np.Arrays corresponding to the X and Y data columns.
merge_columns(data_table: pd.DataFrame, columns: List[str],
                  data_column: str, index_column: str)->Data
    Convert multiple columns to a single data column and a new
            index column.
        Any column in data_dable not listed in columns or data_column will remain
            unchanged.
        Args:
            data_table: A Pandas DataFrame containing multiple columns.
            columns: A list of strings with the names of the columns to be merged.
            data_column: The name of the column containing the data.
            index_column: The name of the new index column to be created by the
                merge.
        Returns:
            A Pandas DataFrame or Series with the merged columns and data.
'''
# TODO Move some of the functions to the BeamData Tools Module
from collections.abc import Iterable
from typing import List, Dict, Tuple, Any, Union
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d


Data = Union[pd.DataFrame, pd.Series]
Value = Tuple[float, str]


def true_iterable(variable)-> bool:
    '''Indicate if the variable is a non-string type iterable.
    Arguments:
        variable {Iterable[Any]} -- The variable to test.
    Returns:
        True if variable uis a non-string iterable.
    '''
    return not isinstance(variable, str) and isinstance(variable, Iterable) 


def nearest_step(value: float, step_size: float = 1.0,
                 towards_zero=True)->float:
    '''Round value up or down to the nearest step_size.
    Args:
        value: The number to be rounded.
        step_size: The size of the step to round to. Default is 1.0.
            e.g. 0.5 will round to the next smallest half integer value.
        towards_zero: Which direction to round.  True will round to the next
            smallest step (towards 0)  False will round to the next largest
            step (towards infinity). Default is True
    Returns:
        The rounded value.
    '''
    if towards_zero:
        sign = round(abs(value)//value)
        rounded = (abs(value)//step_size)*step_size   # rounded down
    else:
        sign = -round(abs(value)//value)
        rounded = (-abs(value)//step_size)*step_size  # rounded up
    rounded = sign*rounded
    return rounded


def get_profile_limit(profile_curves: Data, step_size: float = 1.0)->float:
    '''Find the largest profile distance that is included in all of the
    profile curves.
    The resulting distance is rounded down to the next smallest step size.
    Args:
        profile_curves: A Pandas DataFrame containing a 'Distance' column.
        step_size: The size of the distance steps being used. Default is 1.0.
    Returns:
        The largest profile distance that is included in all of the supplied
            profile curves.
    '''
    scan_range = profile_curves['Distance'].agg([np.min, np.max])
    minimum_range = scan_range.stack().abs().min()
    distance_limit = nearest_step(minimum_range, step_size)
    return distance_limit


def value_parse(value_string: str)->Value:
    '''Convert a string number with units to separate number and unit.
    Split based on a space between number and unit. If no space, in the
        value string, try converting value to a float and return unit as an
        empty string.
    Args:
        value_string: A string containing a number or a number a space and a
            unit.
    Raises:
        ValueError
    Returns:
        A tuple:
            The number as float,
            The unit as string
    '''
    try:
        (num, unit) = value_string.split(sep=' ', maxsplit=1)
    except (AttributeError, ValueError):
        number = float(value_string) # type: float
        unit = ''
    else:
        try:
            number = float(num) # type: ignore
            unit = unit.strip()
        except ValueError:
            number = float(value_string)
            unit = ''
    return (number, unit)


def value2num(value_string: str)->float:
    '''Convert a string type value to a number by removing the unit
    portion of the string.
    The number portion of the string is identified by a space between the
    number and the unit. If there is no space, in value_string, it will try
    converting value_string to a float.
    Args:
        value_string: A string containing a number or a number a space and a
            unit.
    Raises:
        ValueError
    Returns:
        A tuple:
            The number as float,
            The unit as string
    '''
    return value_parse(value_string)[0]


def select_data(data: pd.DataFrame,
                criteria_selection: Dict[str, Any] = None,
                unique_scans: List[str] = None,
                select_columns: List[str] = None,
                index_columns: List[str] = None)->Data:
    '''Select the desired data columns.
    Selection is based on column names and on column specific conditions.
    Args:
        data: A Pandas DataFrame containing one or more columns.
        unique_scans: A list of names of the columns to be used to define
            unique data elements.  If supplied, duplicates will be removed.
        select_columns: A list of names of the columns to be selected.
        criteria_selection: A dictionary where the key is a column name and the
            value is a condition to select for on that column.
        index_columns: A list of names of the columns to be set as the index.
    Raises:
        KeyError
    Return
        A copy of the supplied DataFrame or a Series containing the selected
        rows and columns.
    '''
    selected_data = data.copy()
    if criteria_selection:
        # Do criteria based row selections
        for name, condition in criteria_selection.items():
            selected_data = selected_data[selected_data[name] == condition]
    if unique_scans:
        selected_data.drop_duplicates(unique_scans, inplace=True)
    if select_columns:
        selected_data = selected_data[select_columns]
    if index_columns:
        selected_data = selected_data.set_index(index_columns)
    return selected_data


def process_curve(curve: pd.DataFrame, data_names: Dict[str, str],
                  min_range: float = None, max_range: float = None,
                  step_size: float = 1.0, norm_point: float = None,
                  norm_factor: float = 100.0, kind='cubic'):
    '''Interpolate and normalize a curve.
    Uses scipy.interpolate.interp1d.
    The X values in curve must extend to or beyond min_range norm_point, and
        max_range.
    If min_range or max_range is not given the minimum/maximum X values will
        be used as endpoints for the interpolation.
    If norm_point is not given no normalization will be done.
    Args:
        curve: A Pandas DataFrame containing at least 2 columns.
        data_names: A dictionary containing the names of the X and Y columns
            to be used.
                Must contain keys 'X' and 'Y'.
        min_range (optional): The minimum X value to use in the interpolation.
        max_range (optional): The maximum X value to use in the interpolation.
        step_size (optional): The X step size for the interpolation.
            Default is 1.0.
        norm_point (optional): The X point to be set to the normalization factor.
        norm_factor (optional): The normalization value to set to the
            normalization point to. Default is 100 (percentage).
        kind (optional): The interpolation method to use.  Can be one of:
            'cubic', 'linear', 'nearest', 'zero', 'slinear', 'quadratic',
            ‘previous’ or ‘next’. Default is ‘cubic’.
    Returns:
        Two np.Arrays corresponding to the X and Y data columns.
    '''
    x_name = data_names['X']
    y_name = data_names['Y']
    curve = curve.sort_values(by=x_name)
    curve = curve.drop_duplicates(subset=x_name)
    if min_range is None:
        min_range = nearest_step(min(curve[x_name]), step_size,
                                 towards_zero=False)
    if max_range is None:
        max_range = nearest_step(max(curve[x_name]), step_size,
                                 towards_zero=True)
    curve_interp = interp1d(curve[x_name], curve[y_name], kind=kind)
    max_range = max_range + step_size/1000
    x_data = np.arange(min_range, max_range, step_size)
    y_data = curve_interp(x_data)
    if norm_point is not None:
        norm_value = float(curve_interp(norm_point))
        y_data = y_data/norm_value*norm_factor
    return x_data, y_data


def merge_columns(data_table: pd.DataFrame, columns: List[str],
                  data_column: str, index_column: str)->Data:
    '''Convert multiple columns to a single data column and a new
        index column.
    Any column in data_dable not listed in columns or data_column will remain
        unchanged.
    Args:
        data_table: A Pandas DataFrame containing multiple columns.
        columns: A list of strings with the names of the columns to be merged.
        data_column: The name of the column containing the data.
        index_column: The name of the new index column to be created by the
            merge.
    Returns:
        A Pandas DataFrame or Series with the merged columns and data.
    '''
    keep_columns = tuple(set(data_table.columns) - set(columns))
    merged_data_table = data_table.melt(id_vars=keep_columns,
                                        value_vars=columns,
                                        var_name=index_column,
                                        value_name=data_column)
    return merged_data_table
