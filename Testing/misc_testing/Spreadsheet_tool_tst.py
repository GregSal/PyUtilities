import unittest
import xlwings as xw
from file_utilities import get_file_path
from spreadsheet_tools import *

TEST_DATA_PATH = r'Python\Projects\EclipseRelated\BeamDataTools'
TEST_DATA_PATH += '\\Testing\\Test Data'


def load_worksheet(test_worksheet_info: dict)->xw.Sheet:
    '''Load the test worksheet
    '''
    test_data_sheet = select_sheet(**test_worksheet_info)
    table = dict(data_sheet=test_data_sheet, starting_cell='B3',
                columns='expand', rows='expand', header=1)
    return table


def close_without_saving(data_sheet: xw.Sheet, **table):
    '''Closes the workbook containing data_sheet without saving it.
    Args:
        data_sheet: The excel worksheet containing the table
        **table: Place holder for additional unused arguments.
    '''
    exel_app = data_sheet.api
    workbook = data_sheet.book
    workbook.close()


class Test_open_book(unittest.TestCase):
    '''Test the functions in spreadsheet_tools.py
    '''
    def setUp(self):
        '''Define the file path.'''
        test_book_info = dict(file_name='Test Parameter table.xlsx',
                              sub_dir=TEST_DATA_PATH)
        self.data_file_path = get_file_path(**test_book_info)
        self.book = None
        self.app = None

    def tearDown(self):
        if self.book:
            self.book.close()
        if self.app:
            self.app.kill()
        #FIXME app cleaning is still not working right but not test errors
        # are being raised.
        pass   #  Test Parsing appears to require this.

    def test_open_closed_book(self):
        '''Test that a closed workbook can be opened by name.
        '''
        test_data_book = open_book(self.data_file_path)
        self.assertIsInstance(test_data_book, xw.Book)
        self.book = test_data_book

    def test_open_in_existing_app(self):
        '''Test that a workbook can be opened into an existing app.
        '''
        self.app = xw.App()
        test_data_book = open_book(self.data_file_path)
        self.book = test_data_book
        self.assertEqual(test_data_book.app, self.app)

    def test_no__book(self):
        '''Test that a non-existent workbook raises an error.
        '''
        no_file = self.data_file_path.parent / 'No File.xlsx'
        with self.assertRaises(FileNotFoundError):
            test_data_book = open_book(no_file)
        pass

class Test_Select_worksheet(unittest.TestCase):
    '''Test the functions in spreadsheet_tools.py
    '''
    def test_select_sheet(self):
        '''Test that select_sheet returns a worksheet'''
        test_worksheet_info = dict(
            file_name='Test Parameter table.xlsx',
            sub_dir=TEST_DATA_PATH,
            sheet_name='Test Profile Parameters'
            )
        test_data_sheet = select_sheet(**test_worksheet_info)
        self.assertIsInstance(test_data_sheet, xw.Sheet)
        close_without_saving(test_data_sheet)


class Test_Spreadsheet_tool_tests(unittest.TestCase):
    '''Test the functions in spreadsheet_tools.py
    '''
    table = dict()
    @classmethod
    def setUpClass(cls):
        test_worksheet_info = dict(
            file_name='Test Parameter table.xlsx',
            sub_dir=TEST_DATA_PATH,
            sheet_name='Test Profile Parameters'
            )
        cls.table = load_worksheet(test_worksheet_info)
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        close_without_saving(**cls.table)
        return super().tearDownClass()

    def test_get_variable_list(self):
        '''Test that get_variable_list returns the correct list of column
        names.
        '''
        column_names = ['Radiation device', 'Date', 'Time', 'SSD', 'Energy',
                        'Applicator', 'Scan type', 'Start position [De]',
                        'Field size inline', 'Field size crossline',
                        'Gantry angle', 'Scan direction', 'Flatness',
                        'FieldWidth', 'Penumbra']
        variable_list = get_variable_list(**self.table)
        self.assertListEqual(column_names, variable_list)

    def test_get_data_column(self):
        '''Test that the correct column of data can be selected.
        '''
        value_column = get_data_column(variable='Scan type', **self.table)
        self.assertEqual(len(value_column),27)
        expected_value = {'Crossline'}
        self.assertSetEqual(set(value_column), expected_value)

    def test_replace_data_column(self):
        '''Test that a column of data can be replaced.
        '''
        replacement_column = ['First'] + ['Up']*25 + ['Last']
        replace_data_column('Scan direction', replacement_column,
                            **self.table)
        value_column = get_data_column(variable='Scan direction',
                                       **self.table)
        self.assertListEqual(replacement_column, value_column)

    def test_strip_units_one(self):
        '''Test that a single column of data can have it's units stripped.
        '''
        strip_units(value_names='SSD', **self.table)
        value_column = get_data_column(variable='SSD', **self.table)
        for row_item in value_column:
            with self.subTest(row_item=row_item):
                self.assertIsInstance(row_item, float)
        pass

    def test_strip_units_two(self):
        '''Test that columns of data can have their units stripped.
        '''
        value_list = ['Field size inline', 'Field size crossline']
        strip_units(value_names=value_list, **self.table)
        for column in value_list:
            with self.subTest(column=column):
                value_column = get_data_column(variable=column, **self.table)
                for row_item in value_column:
                    with self.subTest(row_item=row_item):
                        self.assertIsInstance(row_item, float)
        pass

    def test_strip_units_one(self):
        '''Test that a column of data that is already a number will return a
            number after unit_strip.
        '''
        strip_units(value_names='SSD', **self.table)
        value_column = get_data_column(variable='SSD', **self.table)
        strip_units(value_names='SSD', **self.table)
        new_value_column = get_data_column(variable='SSD', **self.table)
        self.assertListEqual(value_column, new_value_column)

    def test_strip_units_multi_space(self):
        '''Test that strip_units works with multiple spaces.
        '''
        strip_units(value_names='Penumbra', **self.table)
        value_column = get_data_column(variable='Penumbra', **self.table)
        for row_item in value_column:
            with self.subTest(row_item=row_item):
                self.assertIsInstance(row_item, float)
        pass

    def test_strip_units_multi_space(self):
        '''Test that strip_units works with % values.
        '''
        strip_units(value_names='Flatness', **self.table)
        value_column = get_data_column(variable='Flatness', **self.table)
        for row_item in value_column:
            with self.subTest(row_item=row_item):
                self.assertIsInstance(row_item, float)
        pass
    pass

if __name__ == '__main__':
    unittest.main()
