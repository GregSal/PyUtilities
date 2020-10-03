'''
Created on Dec 7 2018
@author: Greg Salomons
Testing of methods in file_checking

File_checking tests
    Check file type definitions
    Check insert_base_path
    Check make_full_path
    Check replace_top_dir tests
'''

import unittest
import os
from pathlib import Path
from operator import itemgetter
from Testing.test_files_setup import build_test_directory, remove_test_dir
from file_utilities import FileTypes, get_file_path, make_full_path
from file_utilities import replace_top_dir, FileTypeError
from typing import Dict

class TestMakeFilePath_2(unittest.TestCase):
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