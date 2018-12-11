'''
Created on Dec 7 2018
@author: Greg Salomons
Testing of methods in file_checking

File_checking tests
    One file type
        Initialize with txt type
        'Text File':('*.txt',)
        Confirm that txt tuple is returned
        Confirm the txt is in the extensions list
                type_list
               Confirm that all files is false
            all_types
        Confirm that is directory is false
            is_dir
    two file types
        Initialize with txt and excel types
        'Text File':('*.txt',)
        'Excel Files':('*.xls', '*.xlsx', '*.xlsm'),
        Confirm that Text  and Excel  tuples are returned
        Confirm the extensions list contents
                type_list
    Directory
        Initialize with directory type
            'directory'
               Confirm that all files is false
            all_types
        Confirm that is directory is True
            is_dir
    all files
        Initialize with All and txt type
            'All Files':('*.*',),
            'Text Files':('*.txt', '*.csv', '*.tab',
        Confirm that All and test tuples are returned
            'All Files':('*.*',),
            'Text Files':('*.txt', '*.csv', '*.tab',
               Confirm that all files is True
            all_types
        Confirm that is directory is false
            is_dir
    Check file type
        Make txt and xls files
        Initialize with txt type
        'Text File':('*.txt',)
        Confirm that check_type is true for txt file
        Confirm that check_type is false for xls file
        Confirm that check_type is false for dir
    Check file type with multiple types
        Initialize with txt and excel types
        'Text File':('*.txt',)
        'Excel Files':('*.xls', '*.xlsx', '*.xlsm'),
        Confirm that check_type is true for txt file
        Confirm that check_type is true for xls file
        Confirm that check_type is false for dir
    Check file type with dir
        Initialize with directory type
            'directory'
        Confirm that check_type is false for txt file
        Confirm that check_type is true for dir
    Check file type with all files
        Confirm that All and test tuples are returned
            'All Files':('*.*',),
            'Text Files':('*.txt', '*.csv', '*.tab',
        Confirm that check_type is true for txt file
        Confirm that check_type is true for xls file
        Confirm that check_type is false for dir

    insert_base_path
        Make Testing as based path
        Initialize with directory type
            'directory'
        Confirm that insert_base_path returns full path for full path in
        Confirm that insert_base_path returns full path for full path in as str
        Confirm that insert_base_path returns full path for full path in as str and no base_dir
        Confirm that insert_base_path returns full path for directory name only
        Confirm that insert_base_path returns full path for directory name / txt file
        Confirm that insert_base_path raises ValueError  for directory name / txt file and no base_dir
        Confirm that insert_base_path raises TypeError for number input
    make_full_path dir test
        Make Testing as based path
        Initialize with directory type
            'directory'
        Confirm that make_full_path returns full path for directory name only
        Confirm that make_full_path raises FileTypeError for full path txt file
    make_full_path file test
        Make Testing/test_dir  as base path
        Initialize with txt type
            'Text File':('*.txt',)
        Confirm that make_full_path returns full path for txt file name only
        Confirm that make_full_path raises FileTypeError for xls file name only
        Confirm that make_full_path raises FileTypeError for full path xls file
    make_full_path all files test
        Make Testing/test_dir  as base path
        Initialize with All and txt type
            'All Files':('*.*',),
            'Text Files':('*.txt', '*.csv', '*.tab',
        Confirm that make_full_path returns full path for txt file name only
        Confirm that make_full_path  returns full path  for xls file name only
        Confirm that make_full_path  returns full path  for full path xls file
        Confirm that make_full_path returns full path for file with no extension
        Confirm that make_full_path raises FileTypeError for directory full path
    make_full_path dir exists test
        Make Testing as based path
        Initialize with directory type
            'directory'
        Confirm that make_full_path returns full path for directory name only
        Confirm that make_full_path raises FileNotFoundError for fake directory name only
        Confirm that make_full_path raises FileNotFoundError for fake full directory path
        Confirm that make_full_path returns full path for fake directory name only with exists false
    make_full_path file exists test
        Make Testing/test_dir  as base path
        Initialize with txt type
            'Text File':('*.txt',)
        Confirm that make_full_path returns full path for txt file name only
        Confirm that make_full_path raises FileNotFoundError for fake file name only
        Confirm that make_full_path returns full path for full txt file path
        Confirm that make_full_path raises FileNotFoundError for full txt file path
        Confirm that make_full_path returns full path for fake file name only with exists false
    make_full_path all files test
        Make Testing/test_dir  as base path
        Initialize with All and txt type
            'All Files':('*.*',),
            'Text Files':('*.txt', '*.csv', '*.tab',
        Confirm that make_full_path returns full path for fake file name with no extension and with exists false
        Confirm that make_full_path returns full path for real file name with no extension and with exists true

    replace_top_dir tests
        Make Testing as top path
        Make 'Top Test' as replacement
        Confirm that replace_top_dir returns modified path string for full txt file path
        Confirm that replace_top_dir returns modified path string for full directory path
        Confirm that replace_top_dir returns modified path string for fake full directory path
        Make '' as replacement
        Confirm that replace_top_dir returns abbreviated path for full txt file path
        Confirm that replace_top_dir returns abbreviated path string for full directory path
        Confirm that replace_top_dir returns abbreviated path string for fake full txt path

'''

import unittest
import os
from pathlib import Path
from operator import itemgetter
from file_checking import *
from typing import Optional, List, Dict, Tuple, Set, Any, Union


def build_test_directory()->Dict[str, Path]:
    '''Create a test directory tree.
    Returns:
        List[Path] -- A list of the files in the test tree
    '''
    base_path = Path.cwd() / 'Testing'
    files = [('text_file', 'test_file.txt'),
             ('excel_file', 'test_excel.xls'),
             ('log_file', 'test.log')]
    test_dir = base_path / 'test folder'
    test_dir.mkdir(exist_ok=True)
    test_files = {'test_dir': test_dir}
    for file, file_name in files:
        test_file = test_dir / file_name
        test_file.touch()
        test_files[file] = test_file
    return test_files

def remove_test_dir(test_files: Dict[str, Path]):
    '''Remove all files and directories in the test_files list.
    Arguments:
        test_files {List[Path]} -- A list of all files and directories to be
        removed.
    '''
    dir_list = [(len(str(file)), file)
                for file in test_files.values()
                if file.is_dir()]
    dir_list = sorted(dir_list, key=itemgetter(1), reverse=True)
    file_list = [file for file in test_files.values()  if not file.is_dir()]
    for file in file_list:
        os.remove(file)
    for dir in dir_list:
        dir[1].rmdir()


class TestOneFileType(unittest.TestCase):
    '''Test FileTypes with a single file type.'''
    def setUp(self):
        '''Initialize with txt type.'''
        self.test_type = FileTypes('Text File')

    def test_one_type_tuple(self):
        '''Confirm that txt tuple is returned'''
        text_tuple = ('Text File','*.txt')
        self.assertTupleEqual(self.test_type[0], text_tuple)

    def test_one_type_ext_list(self):
        '''Confirm the txt is in the extensions list'''
        self.assertIn('.txt', self.test_type.type_select)

    def test_one_type_not_all(self):
        '''Confirm that all files is false'''
        self.assertFalse(self.test_type.all_types)

    def test_one_type_not_dir(self):
        '''Confirm that is directory is false'''
        self.assertFalse(self.test_type.is_dir)

class TestTwoFileTypes(unittest.TestCase):
    '''Test FileTypes with a two file types.'''
    def setUp(self):
        '''Initialize with txt type.
        '''
        self.test_type = FileTypes(['Text File', 'Excel Files'])

    def test_two_type_list(self):
        '''Confirm that Text  and Excel  tuples are returned'''
        file_type_list = [('Text File','*.txt'),
                          ('Excel Files', '*.xls;*.xlsx;*.xlsm')]
        self.assertListEqual(self.test_type, file_type_list)

    def test_multi_type_ext_list(self):
        '''Confirm the extensions list contents'''
        file_types = {'.txt', '.xls', '.xlsx', '.xlsm'}
        self.assertSetEqual(file_types, self.test_type.type_select)

class TestSpecialTypes(unittest.TestCase):
    '''Test Directory and All files types.'''
    def test_directory_type(self):
        '''Initialize with directory type.
        Confirm that all files is false.
        Confirm that is directory is True.
        Confirm that type_select is empty.
        '''
        test_type = FileTypes('directory')
        self.assertTrue(test_type.is_dir)
        self.assertTrue(len(test_type.type_select) == 0)
        self.assertFalse(test_type.all_types)

    def test_all_types(self):
        '''Initialize with All and Excel type.
        Confirm that All and Excel tuples are returned.
        Confirm that all files is True.
        Confirm that is directory is false.
        '''
        test_type = FileTypes(['All Files', 'Excel Files'])
        self.assertTrue(test_type.all_types)
        self.assertFalse(test_type.is_dir)
        file_type_list = [('All Files','*.*'),
                          ('Excel Files', '*.xls;*.xlsx;*.xlsm')]
        self.assertListEqual(test_type, file_type_list)

class TestFileTypeCheck(unittest.TestCase):
    '''Check file type method.'''
    def setUp(self):
        '''Make txt and xls files.'''
        self.files = build_test_directory()

    def tearDown(self):
        '''Remove the test directory.
        '''
        remove_test_dir(self.files)

    def test_txt_type_check(self):
        '''Confirm that check_type is true for txt file.
        Initialize with txt typeself.
        Confirm that check_type is false for xls file.
        Confirm that check_type is false for dir.
        '''
        test_type = FileTypes('Text File')
        self.assertTrue(test_type.check_type(self.files['text_file']))
        self.assertFalse(test_type.check_type(self.files['excel_file']))
        self.assertFalse(test_type.check_type(self.files['test_dir']))

    def test_multi_type_check(self):
        '''Check file type with multiple types.
        Initialize with txt and excel types.
        Confirm that check_type is true for txt .
        Confirm that check_type is true for xls file.
        Confirm that check_type is false for dir.
        '''
        test_type = FileTypes(['Text File', 'Excel Files'])
        self.assertTrue(test_type.check_type(self.files['text_file']))
        self.assertTrue(test_type.check_type(self.files['excel_file']))
        self.assertFalse(test_type.check_type(self.files['test_dir']))

    def test_dir_type_check(self):
        '''Check file type with dir
        Initialize with directory type
        Confirm that check_type is false for txt file
        Confirm that check_type is true for dir.
        '''
        test_type = FileTypes('directory')
        self.assertFalse(test_type.check_type(self.files['text_file']))
        self.assertFalse(test_type.check_type(self.files['excel_file']))
        self.assertTrue(test_type.check_type(self.files['test_dir']))

    def test_all_files_type_check(self):
        '''Check file type with all files
        Confirm that check_type is true for txt file
        Confirm that check_type is true for xls file
        Confirm that check_type is false for dir
        '''
        test_type = FileTypes(['All Files', 'Excel Files'])
        self.assertTrue(test_type.check_type(self.files['text_file']))
        self.assertTrue(test_type.check_type(self.files['excel_file']))
        self.assertTrue(test_type.check_type(self.files['log_file']))
        self.assertFalse(test_type.check_type(self.files['test_dir']))

class TestInsertBasePath(unittest.TestCase):
    '''Check insert_base_path method.'''
    def setUp(self):
        '''Make txt and xls files.
        Make Testing as base path'''
        self.files = build_test_directory()
        self.base_path = Path.cwd() / 'Testing'

    def tearDown(self):
        '''Remove the test directory.
        '''
        remove_test_dir(self.files)

    def test_make_dir(self):
        '''Confirm that insert_base_path returns full path for directory name only.
        '''
        test_dir = insert_base_path('test folder', self.base_path)
        self.assertEqual(test_dir, self.files['test_dir'])

    def test_make_relative_dir(self):
        '''Confirm that insert_base_path returns full path for a relative path name.
        '''
        test_dir = insert_base_path('..', self.base_path)
        self.assertEqual(test_dir, self.base_path.parent)

    def test_already_full_dir_str(self):
        '''Confirm that insert_base_path returns full path for full path in as str.
        '''
        test_dir = insert_base_path(str(self.files['test_dir']), self.base_path)
        self.assertEqual(test_dir, self.files['test_dir'])

    def test_already_full_dir_str_no_base(self):
        '''Confirm that insert_base_path returns full path for full path in as str and no base_dir.
        '''
        test_dir = insert_base_path(str(self.files['test_dir']))
        self.assertEqual(test_dir, self.files['test_dir'])

    def test_make_file(self):
        '''Confirm that insert_base_path returns full path for directory name / txt file.
        '''
        test_dir = insert_base_path('test folder//test_file.txt', self.base_path)
        self.assertEqual(test_dir, self.files['text_file'])

    def test_make_relative_file(self):
        '''Confirm that insert_base_path returns full path for a relative path.
        '''
        relative_path = '..//parameters//Testing//test folder//test_file.txt'
        # This call ignores the base path
        test_dir = insert_base_path(relative_path, self.base_path)
        self.assertEqual(test_dir, self.files['text_file'])
        test_dir = insert_base_path(relative_path)
        self.assertEqual(test_dir, self.files['text_file'])

    def test_make_file_error_no_base(self):
        '''Confirm that insert_base_path raises ValueError  for directory name / txt file and no base_dir.
        '''
        with self.assertRaises(ValueError):
            insert_base_path('test folder//test_file.txt')

    def test_make_file_bad_input(self):
        '''Confirm that insert_base_path raises TypeError for number input.
        '''
        with self.assertRaises(TypeError):
            insert_base_path(1, self.base_path)

class TestMakeDirPath(unittest.TestCase):
    '''Make_full_path dir test
        Make Testing as based path
    '''
    def setUp(self):
        '''Make test files.
        Make Testing as based path
        '''
        self.files = build_test_directory()
        self.base_path = Path.cwd() /'Testing'

    def tearDown(self):
        '''Remove the test directory.
        '''
        remove_test_dir(self.files)

    def test_make_dir(self):
        '''Confirm that make_full_path returns full path for directory name only.
        '''
        test_type = FileTypes('directory')
        test_dir = make_full_path(file_name='test folder',
                                  valid_types=test_type,
                                  base_path=self.base_path)
        self.assertEqual(test_dir, self.files['test_dir'])

    def test_make_dir_error(self):
        '''Confirm that make_full_path raises FileTypeError for full path txt file.
        '''
        test_type = FileTypes('Text File')
        with self.assertRaises(FileTypeError):
            make_full_path(file_name='test folder',
                           valid_types=test_type,
                           base_path=self.base_path)


class TestMakeFilePath(unittest.TestCase):
    '''Make_full_path file test
    '''
    def setUp(self):
        '''Make test files.
        Make Testing/test_dir as base path.
        Initialize FileTypes with text type
        '''
        self.files = build_test_directory()
        self.base_path = Path.cwd() / 'Testing' / 'test folder'
        self.test_type = FileTypes('Text File')

    def tearDown(self):
        '''Remove the test directory.
        '''
        remove_test_dir(self.files)

    def test_make_file(self):
        '''Confirm that make_full_path returns full path for txt file name only.
        '''
        test_dir = make_full_path(file_name='test_file.txt',
                                  valid_types=self.test_type,
                                  base_path=self.base_path)
        self.assertEqual(test_dir, self.files['text_file'])

    def test_wrong_file_type_error(self):
        '''Confirm that make_full_path raises FileTypeError for xls file name only.
        '''
        with self.assertRaises(FileTypeError):
            make_full_path(file_name='test_excel.xls',
                           valid_types=self.test_type,
                           base_path=self.base_path)

    def test_wrong_file_type_full_path_error(self):
        '''Confirm that make_full_path raises FileTypeError for full path xls file.
        '''
        with self.assertRaises(FileTypeError):
            make_full_path(file_name=self.files['excel_file'],
                           valid_types=self.test_type,
                           base_path=self.base_path)


class TestMakeAllFiles(unittest.TestCase):
    '''Make_full_path all files test
    '''
    def setUp(self):
        '''Make test files.
        Make Testing/test_dir as base path
        Initialize with All and txt type
        '''
        self.files = build_test_directory()
        self.base_path = Path.cwd() / 'Testing' / 'test folder'
        self.test_type = FileTypes(['All Files', 'Excel Files'])

    def tearDown(self):
        '''Remove the test directory.
        '''
        remove_test_dir(self.files)

    def test_make_txt_file(self):
        '''Confirm that make_full_path returns full path for txt file name only.
        '''
        test_full_path = make_full_path(file_name='test_file.txt',
                                  valid_types=self.test_type,
                                  base_path=self.base_path)
        self.assertEqual(test_full_path, self.files['text_file'])

    def test_make_xls_file(self):
        '''Confirm that make_full_path  returns full path for xls file name only.
        '''
        test_dir = make_full_path(file_name='test_excel.xls',
                                  valid_types=self.test_type,
                                  base_path=self.base_path)
        self.assertEqual(test_dir, self.files['excel_file'])

    def test_make_xls_file_from_full(self):
        '''Confirm that make_full_path returns full path for full path xls file.
        '''
        test_full_path = make_full_path(file_name=self.files['excel_file'],
                                  valid_types=self.test_type,
                                  base_path=self.base_path)
        self.assertEqual(test_full_path, self.files['excel_file'])

    def test_make_file_with_no_ext(self):
        '''Confirm that make_full_path returns full path for file with no extension.
        '''
        test_path = self.base_path / 'empty_file'
        test_full_path = make_full_path(file_name='empty_file',
                                        valid_types=self.test_type,
                                        base_path=self.base_path,
                                        must_exist=False)
        self.assertEqual(test_full_path, test_path)

    def test_make_dir_error(self):
        '''Confirm that make_full_path raises FileTypeError for directory full path.
        '''
        with self.assertRaises(FileTypeError):
            make_full_path(file_name='test folder',
                           valid_types=self.test_type,
                           base_path=self.base_path.parent)
