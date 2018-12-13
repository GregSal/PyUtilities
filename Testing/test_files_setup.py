'''
Created on Dec 13 2018
@author: Greg Salomons
Functions to create test files and folders.

Functions:
    build_test_directory(base_path)
        create the test directory
    remove_test_dir(test_files: Dict[str, Path])
'''
import os
from pathlib import Path
from operator import itemgetter
from typing import Dict

def build_test_directory()->Dict[str, Path]:
    '''Create a test directory tree.
    Returns:
        Dict[str, Path] -- A dictionary of the files in the test tree
    '''
    # TODO Add arguments to build_test_directory for a custom test file set.
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
        test_files {Dict[str, Path]} -- A dictionary of all files and directories to be
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
