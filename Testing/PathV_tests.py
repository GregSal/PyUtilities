'''
Created on Dec 13 2018
@author: Greg Salomons
Testing of class PathP

PathP tests
	From string
	From partial path
	Specific file type
	Group of file types
	Not Path
	Not exists
	Not Dir
	Wrong  type
	Change types
	Change  must exist
	disp
	Copy

'''

import unittest
from pathlib import Path
from custom_variable_sets import PathV
from custom_variable_sets import NotValidError, UpdateError
from file_utilities import FileTypeError
from Testing.test_files_setup import build_test_directory, remove_test_dir


class TestPathVCreation(unittest.TestCase):
    '''Test instance creation.
    '''

    def setUp(self):
        '''Make txt and xls files.'''
        self.files = build_test_directory()


    def tearDown(self):
        '''Remove the test directory.
        '''
        remove_test_dir(self.files)

    def test_init_path(self):
        '''Verify that PathV initializes with a Path value.
        '''
        text_file = self.files['text_file']
        path_param = PathV(text_file)
        self.assertEqual(path_param, text_file)

    def test_init_str(self):
        '''Verify that PathV initializes with a string value.
        '''
        text_file = self.files['text_file']
        path_param = PathV(str(text_file))
        self.assertEqual(path_param, text_file)

    def test_default_path(self):
        '''Verify that PathV initializes to the default path with a blank value.
        '''
        default_path = Path.cwd()
        path_param = PathV()
        self.assertEqual(path_param.value, default_path)

    def test_partial(self):
        '''Verify that PathV initializes with a partial path value.
        '''
        base_path = Path.cwd()
        file_name = 'Testing\\\\test folder\\test_file.txt'
        text_file = base_path / file_name
        path_param = PathV(str(text_file))
        self.assertEqual(path_param.value, text_file)


class TestChangeSetings(unittest.TestCase):
    '''Test Type Checking.
    '''
    def setUp(self):
        '''Make txt and xls files.'''
        self.files = build_test_directory()
        self.path_param = PathV(file_types='Text File')

    def tearDown(self):
        '''Remove the test directory.
        '''
        remove_test_dir(self.files)

    def test_type_add(self):
        '''Verify PathV file type add.
        '''
        xls_file = self.files['excel_file']
        self.path_param.add_type('Excel Files')
        self.path_param.value = xls_file
        self.assertEqual(self.path_param, xls_file)

    def test_type_change(self):
        '''Verify PathV file type change.
        '''
        xls_file = self.files['excel_file']
        self.path_param.file_types = ['Excel Files']
        self.path_param.value = xls_file
        self.assertEqual(self.path_param, xls_file)
        text_file = self.files['text_file']
        with self.assertRaises(FileTypeError):
            self.path_param.value = text_file
        self.assertTrue(True)  # This is currently required for Test Discovery parsing

    def test_exists_change(self):
        '''Verify PathV must exists change.'''
        text_file = self.files['text_file']
        missing_file = Path.cwd() / 'Testing' / 'does_not_exist.txt'
        self.path_param.value = text_file
        with self.assertRaises(FileNotFoundError):
            self.path_param.value = missing_file
        self.path_param.must_exist = False
        self.path_param.value = missing_file
        self.assertEqual(self.path_param, missing_file)


class TestPathVTypeCheck(unittest.TestCase):
    '''Test Type Checking.'''
    def setUp(self):
        '''Make txt and xls files.'''
        self.files = build_test_directory()
        self.path_param = PathV(file_types='Text File')

    def tearDown(self):
        '''Remove the test directory.'''
        remove_test_dir(self.files)

    def test_type_check_error(self):
        '''Verify that PathV raises an error with a directory.'''
        dir_path = self.files['test_dir']
        with self.assertRaises(FileTypeError):
            self.path_param.value = dir_path
        self.assertTrue(True)  # This is currently required for Test Discovery parsing

    def test_type_check(self):
        '''Verify that PathV accepts a Text type file.'''
        text_file = self.files['text_file']
        self.path_param.value = text_file
        self.assertEqual(self.path_param, text_file)


class FutureTests(unittest.TestCase):
    '''Tests of future functionality.
    '''
    def setUp(self):
        '''Make txt and xls files.'''
        self.files = build_test_directory()
        self.path_param = PathV(file_types='Text File')

    def tearDown(self):
        '''Remove the test directory.
        '''
        remove_test_dir(self.files)

    @unittest.skip('Not implemented')
    def test_type_check_message(self):
        '''Verify that trying to set a invalid file type
        returns the appropriate error message.
        '''
        path_param = PathV(file_types=['Text File', 'Excel Files'])
        log_file = self.files['log_file']
        error_message = str(log_file) + ' is not a valid file type '
        error_message += 'Expected Text Files or Excel Files'
        try:
            path_param.value = log_file
        except FileTypeError as err:
            self.assertEqual(err.args[0], error_message)
        else:
            self.fail('FileTypeError not raised')
        self.assertTrue(True)  # This is currently required for Test Discovery parsing

    @unittest.skip('Not implemented')
    def test_dir_check_message(self):
        '''Verify that trying to set a file for a directory
        returns the appropriate error message.
        '''
        path_param = PathV(file_types='directory')
        log_file = self.files['log_file']
        error_message = str(log_file) + ' is not a directory'
        try:
            path_param.value = log_file
        except FileTypeError as err:
            self.assertEqual(err.args[0], error_message)
        else:
            self.fail('FileTypeError not raised')
        self.assertTrue(True)  # This is currently required for Test Discovery parsing


    @unittest.skip('Test Broken')
    def test_copy(self):
        '''Verify that copy() returns an exact copy of the instance.
        '''
        pass

    @unittest.skip('Not implemented')
    def test_display(self):
        '''Verify that disp() returns a formatted string summary of the
        current state.
        '''
        pass


class TestPathPAdditionalTypeCheck(unittest.TestCase):
    '''Test Type Checking for multiple types and for directory.
    '''
    def setUp(self):
        '''Make txt and xls files.'''
        self.files = build_test_directory()

    def tearDown(self):
        '''Remove the test directory.
        '''
        remove_test_dir(self.files)

    def test_type_check_multi(self):
        '''Verify that PathV accepts Text and excel type files.
        '''
        path_param = PathV(file_types=['Text File', 'Excel Files'])
        text_file = self.files['text_file']
        excel_file = self.files['excel_file']
        path_param.value = text_file
        self.assertEqual(path_param, text_file)
        path_param.value = excel_file
        self.assertEqual(path_param, excel_file)

    def test_type_check_multi_error(self):
        '''Verify that PathV accepts Text and excel type files.
        '''
        path_param = PathV(file_types=['Text File', 'Excel Files'])
        log_file = self.files['log_file']
        with self.assertRaises(FileTypeError):
            path_param.value = log_file

    def test_type_check_dir(self):
        '''Verify that PathV accepts directory.
        '''
        path_param = PathV(file_types='directory')
        dir_path = self.files['test_dir']
        path_param.value = dir_path
        self.assertEqual(path_param, dir_path)

    def test_type_check_dir_error(self):
        '''Verify that PathV accepts directory.
        '''
        path_param = PathV(file_types='directory')
        text_file = self.files['text_file']
        with self.assertRaises(FileTypeError):
            path_param.value = text_file

    def test_type_check_non_dir(self):
        '''Verify that PathV accepts non-existing directory.
        '''
        path_param = PathV(file_types='directory', must_exist=False)
        dir_path = Path.cwd() / 'Testing' / 'does_not_exist'
        path_param.value = dir_path
        self.assertEqual(path_param, dir_path)

    def test_type_check_missing_dir_error(self):
        '''Verify that PathV raises error for non-existing directory.
        '''
        path_param = PathV(file_types='directory')
        dir_path = Path.cwd() / 'Testing' / 'does_not_exist'
        with self.assertRaises(FileNotFoundError):
            path_param.value = dir_path



if __name__ == '__main__':
    unittest.main()
