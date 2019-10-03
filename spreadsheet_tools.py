'''
Created on Aug 22 2018
@author: Greg Salomons
A collection of tools for reading writing and manipulating spreadsheet data.
Built on XLWings and pandas.
Data Types
    TableInfo (dict): A dictionary referencing an excel table.
        It contains the following items:
            worksheet (xl.Sheet): The excel worksheet containing the table.
            starting_cell (str, optional): the top right cell in the excel
                table.
            columns (TableSpan, optional): The number of columns in the table.
                If 'expand', the table will include all columns left of
                starting_cell until the first empty cell is encountered.
            rows (TableSpan, optional): The number of rows in the table.
                If 'expand', the table will include all rows below the
                starting_cell until the first empty cell is encountered.

    WorksheetInfo (dict): A dictionary referencing an excel worksheet.
        It contains the following items:
            file_name (FileName): A full Path or a string file name of an
                excel file.
            sub_dir (str): A string containing a sub directory path to the
                excel file relative to the base path or the current working
                directory.
            base_path (Path): A full path to the starting directory.
            sheet_name (str): The name of the desired worksheet.
            new_file (bool, optional): True if a new book is to be created.
                Default is False.
            new_sheet (bool, optional): If True, a new sheet will be created
                in the specified workbook if it does not already exist.
                Default is True.
            replace (bool, optional): If the specified worksheet already
                exists and new_sheet is True, return the existing worksheet.
                Default is True.
'''


from pathlib import Path
# from typing import TypeVar, Dict, List, Any, NoReturn

from typing import TypeVar, Dict, List, Any
from typing import NamedTuple

import xlwings as xw
import pandas as pd
from data_utilities import value2num
from file_utilities import get_file_path
from data_utilities import select_data

# pylint: disable=invalid-name
Data = TypeVar('Data', pd.DataFrame, pd.Series, List[Any])
FileName = TypeVar('FileName', Path, str)
TableInfo = Dict[str, str]
WorksheetInfo = Dict[str, str] # TODO Create a named tuple that defines WorksheetInfo
Variables = TypeVar('Variables', List[str], str)
TableSpan = TypeVar('TableSpan', int, str)

class TableDef(NamedTuple):
    '''Table reference info.
    Attributes
        data_sheet: {xw.sheet} -- The excel worksheet containing the table.
        starting_cell: {optional, str} -- The top right cell of the table in
            excel, in "A1" format. Default is "A1".
        columns: {optional, int, str} -- The number of columns in the table.
            If 'expand', the table will include all columns left of
            the starting_cell until the first empty cell is encountered.
            Default is 'expand'.
        rows: {optional, int, str} -- The number of rows in the table.  If
            'expand', the table will include all rows below the starting_cell
            until the first empty cell is encountered. Default is 'expand'.
        header: {optional, int} -- The number of variable header rows.
            Default is 1. To include the top row in the range selection set
                header to 0.
    '''
    data_sheet: xw.Sheet
    starting_cell: str ='A1'
    columns: TableSpan ='expand'
    rows: TableSpan ='expand'
    header: int = 1
    def __repr__(self) -> str:
        format_str = 'Sheet {data_sheet.name},\n\t'
        format_str += 'Starting Cell={starting_cell},\n\t'
        format_str += 'Number of Columns={columns},\t'
        format_str += 'Number of Rows={rows},\n\t'
        format_str += 'Number of Header Rows={header}'
        return format_str.format(self.dir())

def open_book(file_name: Path, new_file=False)->xw.Book:
    '''Opens a workbook and returns the requested sheet.
    Args:
        file_name: The full path to an excel file.
        new_file: True if a new book is to be created. Default is False.
    Raises:
        FileNotFoundError
    Returns:
        An XLWings Book object pointing to the requested Excel workbook.
    '''
    exel_app = xw.apps.active
    if not exel_app:
        exel_app = xw.App(visible=None, add_book=False)
    if file_name.exists():
        data_book = exel_app.books.open(str(file_name))
    elif new_file:
        data_book = exel_app.books.add()
        data_book.save(str(file_name))
    else:
        raise FileNotFoundError('The file %s does not exist', file_name)
    return data_book


def get_data_sheet(workbook: xw.Book, sheet_name: str,
                   new_sheet=True, replace=True)->xw.Sheet:
    '''Returns the specified excel sheet from the given workbook.
    Args:
        workbook: An XLWings Book object pointing to the Excel workbook that
            the desired worksheet is in.
        sheet_name: The name of the desired worksheet.
        new_sheet: If True, a new sheet will be created in the specified
            workbook if it does not already exist. Default is True.
        replace: If the specified worksheet already exists
            and new_sheet is True, return the existing worksheet.
            Default is True.
    Raises:
        ValueError
    Returns:
        An XLWings Sheet object pointing to the requested sheet.
    '''
    sheet_names = [sheet.name for sheet in workbook.sheets]
    if sheet_name in sheet_names:
        if new_sheet and not replace:
            print('WARNING:\tSheet {} already exists'.format(sheet_name))
        sheet_index = sheet_names.index(sheet_name)
        data_sheet = workbook.sheets[sheet_index]
    elif new_sheet:
        data_sheet = workbook.sheets.add(sheet_name)
    else:
        raise ValueError('Sheet {} does not exist'.format(sheet_name))
    return data_sheet


def select_sheet(file_name: FileName, sub_dir: str = None,
                 base_path: Path = None, new_file=False,
                 **sheet_info)->xw.Sheet:
    '''Open the excel file specified by file_name and returns the requested
    sheet.
    Args:
        file_name: Either the full path to the file name or the name of the
            file.
        sub_dir (str): A string path relative to the base path or current
            working directory.
        base_path (Path): A full path of type Pathto the starting directory.
        new_file: True if a new book is to be created. Default is False.
        sheet_name (str): The name of the desired worksheet.
        new_sheet (bool): If True, a new sheet will be created in the
            specified workbook if it does not already exist. Default is True.
        replace (bool): If the specified worksheet already exists
            and new_sheet is True, return the existing worksheet.
            Default is True.
    Returns:
        An XLWings Sheet object pointing to the requested sheet.
    '''
    data_file_path = get_file_path(file_name, sub_dir, base_path)
    data_book = open_book(data_file_path, new_file)
    data_sheet = get_data_sheet(data_book, **sheet_info)
    return data_sheet


def create_output_file(file_name: FileName, sub_dir: str = None,
                       base_path: Path = None, new_file=True)->xw.Book:
    '''Create an output spreadsheet.
    Args:
        file_name {FileName} --  A full Path or a string file name of an
            excel file.
        sub_dir {str} --  A string containing a sub directory path from
            base_path to the excel file.
        base_path {Path} -- A full path of type Path to the top directory.
        new_file {bool} -- True if a new book is to be created. Default is False.
    Raises:
        FileNotFoundError
    Returns:
        An XLWings Book object pointing to the requested Excel workbook.
    '''
    file_path = get_file_path(file_name, sub_dir, base_path)
    workbook = open_book(file_path, new_file)
    workbook.save(str(file_path))
    return workbook


def save_data_to_sheet(data_table: pd.DataFrame, workbook: xw.Book,
                       sheet_name: str = 'Sheet A', starting_cell: str = 'A1',
                       add_index=False, new_sheet=True, replace=True)->xw.Sheet:
    '''Adds the given data to a new data sheet.
    Args:
        data_table {pd.DataFrame} -- The Pandas DataFrame data to be added.
        starting_cell {str} -- The top right cell in the excel table.
        add_index {bool} -- Whether to include the DataFrame index in the
            spreadsheet table.  Default is False.
        workbook {xw.Book} -- An XLWings Book object pointing to an open Excel 
            workbook.
        sheet_name (str): The name of the desired worksheet.
        starting_cell: {optional, str} -- The top right cell of the table in
            excel, in "A1" format. Default is "A1".
        add_index (bool): Include the DataFrame index in the spreadsheet. Default is True.
        new_sheet (bool): If True, a new sheet will be created in the
            specified workbook if it does not already exist. Default is True.
        replace (bool): If the specified worksheet already exists
            and new_sheet is True, return the existing worksheet. Default is True.
    '''
    worksheet = get_data_sheet(workbook, sheet_name, new_sheet, replace)
    worksheet.range(starting_cell).options(index=add_index).value = data_table
    return worksheet


def get_table_range(data_sheet: xw.Sheet, starting_cell: str = 'A1',
                columns: TableSpan = 'expand',
                rows: TableSpan = 'expand',
                header: int = 1)->xw.Range:
    '''Returns an excel range for the specified table.
    columns='expand' assumes no break in the variable names.
    Args:
        data_sheet: The excel worksheet containing the table
        starting_cell: the top right cell in the excel table.
        columns: The number of columns in the table.  If 'expand', the table
            will include all columns left of starting_cell until the first
            empty cell is encountered.
        rows: The number of rows in the table.  If 'expand', the table
            will include all rows below the starting_cell until the first
            empty cell is encountered.
        header: The number of variable header rows. Default is 1.
            To include the top row in the range selection set header to 0.
      Returns:
        An XLWings Range spanning the table data.
     '''
    start_range = data_sheet.range(starting_cell).offset(row_offset=header)
    if 'expand' in str(rows):
        data_bottom = start_range.end('down')
    else:
        data_bottom = start_range.offset(row_offset=int(rows)-1)
    num_rows = data_bottom.row - start_range.row

    if 'expand' in str(columns):
        end_range = start_range.end('right')
    else:
        end_range = start_range.offset(column_offset=int(columns)-1)
    end_range = end_range.offset(row_offset=num_rows)
    selection_range = xw.Range(start_range, end_range)
    return selection_range
    

def get_variable_list(header: int = 1, **table: TableInfo)->List[str]:
    '''Returns a list of header variables in the row of starting cell.
    columns='expand' assumes no break in the variable names.
    Args:
        header: The number of variable header rows. Default is 1.
        data_sheet: The excel worksheet containing the table
        starting_cell: the top right cell in the excel table.
        columns: The number of columns in the table.  If 'expand', the table
            will include all columns left of starting_cell until the first
            empty cell is encountered.
    Returns:
        A list containing the names of the variables in the header row.
    '''
    variable_selection = table.copy()
    variable_selection.update({'rows': header, 'header': 0})
    variable_range = get_table_range(**variable_selection)
    variables = variable_range.value
    return variables


def get_column_range(variable: str, **table: TableInfo)->xw.Range:
    '''Returns an excel range for the specified column.
    columns='expand' assumes no break in the variable names.
    Args:
        variable: The name of the column as given in the header row.
        data_sheet: The excel worksheet containing the table
        starting_cell: the top right cell in the excel table.
        columns: The number of columns in the table.  If 'expand', the table
            will include all columns left of starting_cell until the first
            empty cell is encountered.
        rows: The number of rows in the table.  If 'expand', the table
            will include all rows below the starting_cell until the first
            empty cell is encountered.
        header: The number of variable header rows. Default is 1.
      Returns:
        An XLWings Range spanning the column data.
     '''
    variables = get_variable_list(**table)
    table_range = get_table_range(**table)
    table_start = table_range[0]
    num_rows = table_range.shape[0]
    column_index = variables.index(variable)
    data_start = table_start.offset(column_offset=column_index)
    data_end = table_start.offset(row_offset=num_rows-1,
                                  column_offset=column_index)
    data_range = xw.Range(data_start, data_end)
    return data_range


def load_data_table(index_variables: List[str] = None, sort: bool = True,
                    header: int = 1, **table: TableInfo)->pd.DataFrame:
    '''Extract the requested data table from the worksheet.
     Args:
        index_variables: The name of the columns to be used as the DataFrame
            Index. Default is None (no index).
        sort: If True the DataFrame will be sorted on the index.  If false do
            sorting is done.  Default is True.
        header: the number of header rows at the top of the excel table.
            Default is 1.
        table: The table reference info supplied to get_table_range.
            Must contain:
                data_sheet: The excel worksheet containing the table.
            Optionally contains:
                starting_cell: the top right cell in the excel table.
                columns: The number of columns in the table.  If 'expand',
                    the table will include all columns left of starting_cell
                    until the first empty cell is encountered.
                rows: The number of rows in the table.  If 'expand', the
                    table will include all rows below the starting_cell until
                    the first empty cell is encountered.
                header: The number of variable header rows. Default is 1.
                    To include the top row in the range selection set header
                    to 0.
    Returns:
        A Pandas DataFrame containing the data from the Excel table.
    '''
    table['header'] = 0
    table_range = get_table_range(**table)
    data_table = table_range.options(pd.DataFrame, header=header).value
    data_table.reset_index(inplace=True)
    if index_variables:
        data_table.set_index(index_variables, inplace=True)
        if sort:
            data_table.sort_index(inplace=True)
    return data_table


def load_definitions(data_sheet: xw.Sheet, starting_cell='A1',
                     rows: TableSpan = 'expand')->Dict[Any, Any]:
    '''Extract the requested data definitions from the worksheet.
     Args:
         data_sheet: {xw.sheet} -- The excel worksheet containing the table.
         starting_cell: {optional, str} -- The top right cell in the excel
             table.
         rows: {optional, TableSpan} -- The number of rows in the table.
             If 'expand', the table will include all rows below the
             starting_cell until the first empty cell is encountered.
    Returns:
        A dictionary, where the keys are the objects in the first column and
        the values are the objects in the second column.
    '''
    table_range = get_table_range(data_sheet=data_sheet,
                                  starting_cell=starting_cell,
                                  rows=rows, header=0, columns=2)
    definitions = table_range.options(dict).value
    return definitions


def load_reference_table(reference_sheet_info, reference_table_info,
                         **selections)->Data:
    '''Read in a reference table.
     Args:
        reference_sheet_info: The file reference info supplied to
            select_sheet. Must contain the following items:
                file_name: Either the full path to the file name or the name
                    of the file.
                sub_dir: A string path relative to the current working
                    directory.
                sub_dir (str): A string path relative to the base path or
                    current working directory.
                base_path (Path): A full path of type Pathto the starting
                    directory.
                sheet_name (str): The name of the worksheet the table is in.
        reference_table_info: The table reference info supplied to
            get_table_range.  It may contain:
                starting_cell: the top right cell in the excel table.
                columns: The number of columns in the table.  If 'expand',
                    the table will include all columns left of starting_cell
                    until the first empty cell is encountered.
                rows: The number of rows in the table.  If 'expand', the
                    table will include all rows below the starting_cell until
                    the first empty cell is encountered.
                header: The number of variable header rows. Default is 1.
                    To include the top row in the range selection set header
                    to 0.
        selections: Selection info passed to Tools.data_utilities.select_data
            It may contain:
                criteria_selection: A dictionary where the key is a column
                    name and the value is a condition to select for on that
                    column.
                unique_scans: A list of names of the columns to be used to
                    define unique data elements.  If supplied, duplicates
                    will be removed.
                select_columns: A list of names of the columns to be selected.
                index_columns: A list of names of the columns to be set as
                    the index.
    Returns:
        A Pandas DataFrame containing the data from the Excel table.
    '''
    table_sheet = select_sheet(**reference_sheet_info)
    reference_table_info['data_sheet'] = table_sheet
    reference_table = load_data_table(**reference_table_info)
    reference_table = select_data(reference_table, **selections)
    return reference_table


def get_data_column(variable: str, **table: TableInfo)->List[Any]:
    '''Return data for a selected column.
    Args:
        variable: The name of the desired column.
        table: The table reference info supplied to get_table_range.
            Must contain:
                data_sheet: The excel worksheet containing the table.
            Optionally contains:
                starting_cell: the top right cell in the excel table.
                columns: The number of columns in the table.  If 'expand',
                    the table will include all columns left of starting_cell
                    until the first empty cell is encountered.
                rows: The number of rows in the table.  If 'expand', the
                    table will include all rows below the starting_cell until
                    the first empty cell is encountered.
                header: The number of variable header rows. Default is 1.
                    To include the top row in the range selection set header
                    to 0.
    Returns:
        A list containing the data from the specified Excel column.
    '''
    data_range = get_column_range(variable, **table)
    column_data = data_range.value
    return column_data


def append_data_column(variable_name: str, data_column: List[Any],
                       end_range: xw.Range = None,
                       **table: TableInfo)->xw.Range:
    '''Adds the given data_column to the end of the designated excel table.
    Args:
        variable_name: The name for the new column.
        data_column: A list containing the data to be placed into the new
            column.
        end_range: Optional range of last column in current table.
        table: The table reference info supplied to get_table_range.
            Must contain:
                data_sheet: The excel worksheet containing the table.
            Optionally contains:
                starting_cell: the top right cell in the excel table.
                columns: The number of columns in the table.  If 'expand',
                    the table will include all columns left of starting_cell
                    until the first empty cell is encountered.
                rows: The number of rows in the table.  If 'expand', the
                    table will include all rows below the starting_cell until
                    the first empty cell is encountered.
                header: The number of variable header rows. Default is 1.
                    To include the top row in the range selection set header
                    to 0.
    Returns:
        An XLWings Range object for the new column.
    '''
    if end_range is None:
        variables = get_variable_list(**table)
        end_variable = variables[-1]
        end_range = get_column_range(end_variable, **table)
    new_range = end_range.offset(column_offset=1)
    header_range = new_range[0].offset(row_offset=-1)
    header_range.value = variable_name
    new_range.options(transpose=True).value = data_column
    return new_range


def replace_data_column(variable_name: str, data_column: List[Any],
                        **table: TableInfo):  # ->NoReturn
    '''Replace the data in the given data_column.
    If data_column is shorter than the original column, the remaining values
    will be blank.
    Args:
        variable_name: The name of the desired column.
        data_column: The data to be placed in this excel column.
        table: The table reference info supplied to get_table_range.
            Must contain:
                data_sheet: The excel worksheet containing the table.
            Optionally contains:
                starting_cell: the top right cell in the excel table.
                columns: The number of columns in the table.  If 'expand',
                    the table will include all columns left of starting_cell
                    until the first empty cell is encountered.
                rows: The number of rows in the table.  If 'expand', the
                    table will include all rows below the starting_cell until
                    the first empty cell is encountered.
                header: The number of variable header rows. Default is 1.
                    To include the top row in the range selection set header
                    to 0.
    '''
    data_range = get_column_range(variable_name, **table)
    data_range.clear()
    data_range.options(transpose=True).value = data_column


def format_data_column(variable_name: str, style: str = '0',
                       **table: TableInfo):  # ->NoReturn
    '''format the data in the specified column.
    The format style uses the standard Excel format style string.
    After formatting an "Auto-Fit Column Width" is applied
    Args:
        variable_name: The name of the column to format.
        style: An Excel format style string.  Default is "0"
        table: The table reference info supplied to get_table_range.
            Must contain:
                data_sheet: The excel worksheet containing the table.
            Optionally contains:
                starting_cell: the top right cell in the excel table.
                columns: The number of columns in the table.  If 'expand',
                    the table will include all columns left of starting_cell
                    until the first empty cell is encountered.
                rows: The number of rows in the table.  If 'expand', the
                    table will include all rows below the starting_cell until
                    the first empty cell is encountered.
                header: The number of variable header rows. Default is 1.
    '''
    data_range = get_column_range(variable_name, **table)
    data_range.number_format = style
    data_range.autofit()


def rename_variable(name_pairs, **table: TableInfo):  # ->NoReturn
    '''Rename the data_columns from old_name to new_name.
    Args:
        name_swap: A list of tuple pairs where the first is the current
            column name and the second is the new column name.
        variable_name: The name of the column to format.
        style: An Excel format style string.  Default is "0"
        table: The table reference info supplied to get_table_range.
            Must contain:
                data_sheet: The excel worksheet containing the table.
            Optionally contains:
                starting_cell: the top right cell in the excel table.
                columns: The number of columns in the table.  If 'expand',
                    the table will include all columns left of starting_cell
                    until the first empty cell is encountered.
                rows: The number of rows in the table.  If 'expand', the
                    table will include all rows below the starting_cell until
                    the first empty cell is encountered.
                header: The number of variable header rows. Default is 1.
                    To include the top row in the range selection set header
                    to 0.
    '''
    for (old_name, new_name) in name_pairs:
        column_range = get_column_range(old_name, **table)
        name_range = column_range[0].offset(row_offset=-1)
        name_range.value = new_name


def strip_units(value_names: Variables, format_style: str = '0.00',
                **table):  # ->NoReturn
    '''Replace string type column(s) with numeric column(s) by removing the
    unit portion of the string.
    Args:
        value_names: The name of the column(s) to convert.
        format_style: An excel type format style string for the columns
        being converted.
        table: The table reference info supplied to get_table_range.
            Must contain:
                data_sheet: The excel worksheet containing the table.
            Optionally contains:
                starting_cell: the top right cell in the excel table.
                columns: The number of columns in the table.  If 'expand',
                    the table will include all columns left of starting_cell
                    until the first empty cell is encountered.
                rows: The number of rows in the table.  If 'expand', the
                    table will include all rows below the starting_cell until
                    the first empty cell is encountered.
                header: The number of variable header rows. Default is 1.
                    To include the top row in the range selection set header
                    to 0.
    '''
    if isinstance(value_names, str):
        value_list = [value_names]
    else:
        value_list = list(value_names)
    for variable_name in value_list:
        value_column = get_data_column(variable=variable_name, **table)
        number_column = [value2num(value) for value in value_column]
        replace_data_column(variable_name, number_column, **table)
        format_data_column(variable_name, format_style, **table)


def append_data_sheet(data_table: pd.DataFrame, starting_cell: str = 'A1',
                      add_index=False, **worksheet: WorksheetInfo)->xw.Sheet:
    '''Adds the given data to a new data sheet.
    Args:
        data_table {pd.DataFrame} -- The Pandas DataFrame data to be added.
        starting_cell {str} -- The top right cell in the excel table.
        add_index {bool} -- Whether to include the DataFrame index in the
            spreadsheet table.  Default is False.
        worksheet {Dict[Any, Any] -- The excel worksheet reference info.
        It contains the following items:
            file_name {FileName} --  A full Path or a string file name of an
                excel file.
            sub_dir {str} --  A string containing a sub directory path from
                base_path to the excel file.
            sheet_name {str} --  THe name of the desired worksheet.
            new_file {bool, optional} --  True if a new book is to be created.
                Default is False.
            new_sheet {bool, optional} -- If True, a new sheet will be created
                in the specified workbook if it does not already exist.
                Default is True.
            replace {bool, optional} -- If the specified worksheet already
                exists and new_sheet is True, return the existing worksheet.
                Default is True.
    '''
    new_sheet = select_sheet(**worksheet)
    replace = worksheet.get('replace')
    if replace:
        new_sheet.clear()
    new_sheet.range(starting_cell).options(index=add_index).value = data_table
    new_sheet.autofit(axis='columns')
    return new_sheet

def insert_data_column(variable_name: str, data_column: List[Any],
                       starting_cell: str = 'A1',
                       **worksheet: WorksheetInfo)->xw.Range:
    '''Adds the given data_column to the end of the designated excel table.
    Args:
        variable_name: The name for the new column.
        data_column: A list containing the data to be placed into the new
            column.
        starting_cell: the top right cell in the excel table.
        worksheet: The excel worksheet reference info.
        It contains the following items:
            file_name (FileName): A full Path or a string file name of an
                excel file.
            sub_dir (str): A string containing a sub directory path from
                base_path to the excel file.
            sheet_name (str): THe name of the desired worksheet.
            new_file (bool, optional): True if a new book is to be created.
                Default is False.
            new_sheet (bool, optional): If True, a new sheet will be created
                in the specified workbook if it does not already exist.
                Default is True.
            replace (bool, optional): If the specified worksheet already
                exists and new_sheet is True, return the existing worksheet.
                Default is True.
    Returns:
        An XLWings Range object for the new column.
    '''
    new_sheet = select_sheet(**worksheet)
    replace = worksheet.get('replace')
    if replace:
        new_sheet.clear()
    new_range = new_sheet.range(starting_cell).offset(row_offset=1)
    header_range = new_range[0].offset(row_offset=-1)
    header_range.value = variable_name
    new_range.options(transpose=True).value = data_column
    new_sheet.autofit(axis='columns')
    return new_range


def save_and_close(data_sheet: xw.Sheet):
    '''Saves and closes the workbook containing data_sheet.
    Args:
        data_sheet: The excel worksheet containing the table
    '''
    exel_app = data_sheet.api
    workbook = data_sheet.book
    workbook.save()
    workbook.close()
    exel_app.quit()


def fill_gaps(variable_name: str, fill_value=None, **table):  # ->NoReturn
    '''Fill blank cells in a row with the previous column's value.
    Args:
        variable_name: The name of the column to format.
        fill_value: The value to place in the blank cells.
            If fill_value is None, use the previous row's value.
            Default is None.
        table: The table reference info supplied to get_table_range.
            Must contain:
                data_sheet: The excel worksheet containing the table.
            Optionally contains:
                starting_cell: the top right cell in the excel table.
                columns: The number of columns in the table.  If 'expand',
                    the table will include all columns left of starting_cell
                    until the first empty cell is encountered.
                    Default is 'expand'.
                rows: The number of rows in the table.  If 'expand', the
                    table will include all rows below the starting_cell until
                    the first empty cell is encountered.
                    Default is 'expand'.
                header: The number of variable header rows. Default is 1.
    '''
    data_range = get_column_range(variable_name, **table)
    row_values = data_range.value
    row_value_list = list()
    for value in row_values:
        if value:
            previous = value
        else:
            if fill_value is None:
                value = previous
            else:
                value = fill_value
        row_value_list.append(value)
    data_range.value = row_value_list
