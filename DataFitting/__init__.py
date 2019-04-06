'''
Created on Aug 22 2018
@author: Greg Salomons
A collection of tools for reading writing and manipulating data.
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

FileName = TypeVar('FileName', Path, str)
Data = TypeVar('Data', pd.DataFrame, pd.Series, List[Any])
TableInfo = Dict[str, str]
WorksheetInfo = Dict[str, str]
Variables = TypeVar('Variables', List[str], str)
TableSpan = TypeVar('TableSpan', int, str)
Data = TypeVar('Data', pd.DataFrame, pd.Series, List[Any])
Value = Tuple[float, str]
'''

