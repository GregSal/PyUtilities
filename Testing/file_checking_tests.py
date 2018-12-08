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


def build_test_directory()->List[Path]:
    '''Create a test directory tree.
    Returns:
        List[Path] -- A list of the files in the test tree
    '''
    base_path = Path.cwd() / 'Testing'
    test_dir = base_path / 'test folder'
    test_file1 = test_dir / 'test_file.txt'
    test_file2 = test_dir / 'test_excel.xls'
    test_files = [test_dir, test_file1, test_file2]

    test_dir.mkdir(exist_ok=True)
    test_file1.touch()
    test_file2.touch()

    return test_files

def remove_test_dir(test_files: List[Path]):
    '''Remove all files and directories in the test_files list.
    Arguments:
        test_files {List[Path]} -- A list of all files and directories to be
        removed.
    '''
    dir_list = [(len(str(file)), file) for file in test_files if file.is_dir()]
    dir_list = sorted(dir_list, key=itemgetter(1), reverse=True)
    file_list = [file for file in test_files if not file.is_dir()]
    for file in file_list:
        os.remove(file)
    for dir in dir_list:
        dir[1].rmdir()



class TestOneFileType(unittest.TestCase):
    '''Initialize with txt type
        'Text File':('*.txt',)
        Confirm that txt tuple is returned
        Confirm the txt is in the extensions list
                type_list
               Confirm that all files is false
            all_types
        Confirm that is directory is false
            is_dir
    '''
    def setUp(self):
        '''Initialize with txt type.
        '''
        self.test_type = FileTypes('Text File')
        

    def test_one_type_tuple(self):
        '''Confirm that txt tuple is returned'''
        text_tuple = ('Text File','*.txt')
        self.assertTupleEqual(self.test_type[0], text_tuple)

    def test_one_type_ext_list(self):
        '''Confirm the txt is in the extensions list'''
        self.assertIn('.txt', self.test_type.type_list)

    def test_one_type_not_all(self):
        '''Confirm that all files is false'''
        self.assertFalse(self.test_type.all_types)

    def test_one_type_not_dir(self):
        '''Confirm that is directory is false'''
        self.assertFalse(self.test_type.is_dir)
