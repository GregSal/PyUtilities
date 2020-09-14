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
from collections.abc import Iterable
from typing import List, Dict, Tuple, Any, Union, Set, NamedTuple
import pandas as pd
import re

Data = Union[pd.DataFrame, pd.Series]
Value = Tuple[float, str]


class DataElement(NamedTuple):
    '''A number containing a corresponding unit.
    Attributes:
        Value {float} -- The number
        Unit {str} -- The corresponding unit.
    '''
    Value: float
    Unit: str

    def __init___(self, *data):
        if len(data) == 1:
            try:
                value = float(data[0])
            except ValueError:
                data = self.str2data(data[0])
            else:
                data = (value, '')

        super().__init__(*data)


    @classmethod
    def set_units(cls):
        cls.unit_symbols = ['%', 'CU', 'cGy', 'Gy', 'deg', 'cm', 'deg',
                            'MU', 'min', 'cc', 'cm3', 'MU/Gy', 'MU/min',
                            'cm3', 'cc']
        # Match on one of the unit symbol strings
        unit_pattern = '(?P<unit>' + '|'.join(cls.unit_symbols) + ')'
        # Match a float or int value with optional sign
        number_pattern = '(?P<value>[-+]?\d+[.]?\d*)'
        # Optional Space between value and unit
        optional_space = '\s*'
        number_value_pattern = ''.join([
            number_pattern,
            optional_space,
            unit_pattern
            ])
        cls.data_pattern = re.compile(number_value_pattern)


    def str2data(self, data_string:str):
        match = self.data_pattern.search(data_string)
        if match:
            value, unit = find_num[0]
            return value, unit
        return data_string

    def convert_units(self, target_units: str):
        '''Take value in starting_units and convert to target_units.
        Arguments:
            target_units {str} -- The unit to convert starting_value to. Must
                be of the same unit type as starting_units.
        Returns:
            DataElement -- The initial value converted to the new units.
        '''
        conversion_table = {'cGy': {'cGy': 1.0,
                                    'Gy': 0.01
                                    },
                            'Gy':  {'Gy': 1.0,
                                    'cGy': 100},
                            'cc':  {'cc': 1.0,
                                    'ml': 1.0,
                                    'l': 0.01,
                                    },
                            'cm':  {'cm': 1.0,
                                    'mm': 10,
                                    'm': 0.01,
                                    },
                            'mm':  {'cm': 0.1,
                                    'mm': 1.0,
                                    'm': 0.001,
                                    }
                           }
        try:
            conversion_factor = conversion_table[self.Unit][target_units]
        except KeyError as err:
            raise ValueError('Unknown units') from err
        new_value = float(self.Value)*conversion_factor
        return DataElement(new_value, target_units)


def drop_units(text: str)->float:
    number_value_pattern = (
        '^'                # beginning of string
        '\s*'              # Skip leading whitespace
        '(?P<value>'       # beginning of value integer group
        '[-+]?'            # initial sign
        '\d+'              # float value before decimal
        '[.]?'             # decimal Place
        '\d*'              # float value after decimal
        ')'                # end of value string group
        '\s*'              # skip whitespace
        '(?P<unit>'        # beginning of value integer group
        '[^\s]*'           # units do not contain spaces
        ')'                # end of unit string group
        '\s*'              # drop trailing whitespace
        '$'                # end of string
        )
    #find_num = re.compile(number_value_pattern)
    find_num = re.findall(number_value_pattern, text)
    if find_num:
        value, unit = find_num[0]
        return value
    return text


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
    # TODO allow value_parse to identify units even when no space is present.
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




def sort_dict(dict_data: Dict[str, Any],# FIXME Use Generic typing for Dict Value
              sort_list: List[str] = None
              )->List[Any]:
    '''Generate a sorted list of from dictionary values.
    Arguments:
        dict_data {Dict[str, Any]} -- A dictionary containing values with
            multiple sortable attributes.
        sort_list {List[str]} -- A list of attribute names to sort by.
    Returns:
        List[Any] -- Sorted list of values.
        '''
    data_list = list(dict_data.values())
    if sort_list:
        data_set = sorted(data_list, key=attrgetter(*sort_list))
    else:
        data_set = data_list
    return data_set


def logic_match(value: Any,
                truth_values: Set[str] = None,
                false_values: Set[str] = None)->bool:
    '''Convert input value to a boolean True or False.
    Treats: 'YES', 'Y', 'TRUE', 'T', 1 as True
    Treats: 'NO', 'N', 'FALSE', 'F', 0, -1 as False
    For all other values, attempts to apply the bool conversion.
    Arguments:
        value {Any} -- the value to convert
        truth_values {Optional, Any} -- Set of string values to be recognized as true.
            default {'YES', 'Y', 'TRUE', 'T', '1'}
        false_values {Optional, Any} -- Set of string values to be recognized as false.
            default {'NO', 'N', 'FALSE', 'F', '0', '-1'}
    Returns:
        bool -- [description]
    '''
    if not truth_values:
        truth_values = {'YES', 'Y', 'TRUE', 'T', '1'}
    if not false_values:
        false_values = {'NO', 'N', 'FALSE', 'F', '0', '-1'}
    value_str = str(value).upper()
    if value_str in truth_values:
        return True
    elif value_str in false_values:
        return False
    return bool(value)


def true_iterable(variable)-> bool:
    '''Indicate if the variable is a non-string type iterable.
    Arguments:
        variable {Iterable[Any]} -- The variable to test.
    Returns:
        True if variable is a non-string iterable.
    '''
    return not isinstance(variable, str) and isinstance(variable, Iterable)


def drop_empty_items(dictionary: Dict[Any, Any])->Dict[Any, Any]:
    '''Remove dictionary items containing None values.
    Arguments:
        dictionary {Dict[Any, Any]} -- The dictionary to be cleaned.
    Returns:
        A copy of the dictionary, dropping all items with a value of None.
    '''
    cleaned_dict = {key: value for (key, value) in dictionary.items()
                    if value is not None}
    return cleaned_dict


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
            if isinstance(condition, str):
                selected_data = selected_data[selected_data[name].str.contains(condition)]
            else:
                selected_data = selected_data[selected_data[name] == condition]
    if unique_scans:
        selected_data.drop_duplicates(unique_scans, inplace=True)
    if select_columns:
        selected_data = selected_data[select_columns]
    if index_columns:
        selected_data = selected_data.set_index(index_columns)
    return selected_data


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
