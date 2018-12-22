""" Module Scan for files"""
from pathlib import Path
        
def dir_xml_iter(directory_to_scan: Path):
    '''Returns an iterator which scans a dictionary tree and returns xml files'''
    for file_item in directory_to_scan.iterdir():
        # if the item is a file generate a FileStat object with it
        if file_item.is_file():
            if 'xml' in file_item.suffix:
                yield file_item
        elif file_item.is_dir():
            # recursively scan sub-directories
            for sub_file_item in dir_mod_iter(file_item):
                yield sub_file_item