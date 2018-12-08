'''
Setup
    build test dir
        test folder
            test_file.txt
            test_excel.xls
'''

from pathlib import Path
import os
import file_checking

base_path = Path.cwd()
test_dir = base_path / 'test folder'
test_file1 = test_dir / 'test_file.txt'
test_file2 = test_dir / 'test_excel.xls'

test_dir.mkdir(exist_ok=True)
test_file1.touch()
test_file2.touch()

os.remove(test_file1)
os.remove(test_file2)
test_dir.rmdir()