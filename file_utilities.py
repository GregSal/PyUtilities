'''
Created on Oct 19 2018
@author: Greg Salomons
A collection of file utility functions.
    set_base_dir(sub_dir)- > Path:
        Returns the Path to the  Queen's OneDrive directory
    get_file_path(file_name, sub_dir)
        Returns the full Path to the file
    true_iterable(variable)
        Indicate if the variable is a non-string type iterable
    make_full_path(file_name, valid_types, must_exist, base_path)
        Build the full path to a file from the supplied parts.
    replace_top_dir(dir_path, file_path, new_name)
        Replace the first portion of the file path.
Classes
    FileTypes:
        A user select-able list of file type options
        Definition of file type groups
    FileTypeError:
        The file extension is not the appropriate type.
'''
import time
from pathlib import Path
from collections.abc import Iterable
from typing import Dict, List, Union, Iterator
import pandas as pd


Data = pd.DataFrame
PathInput = Union[Path, str]


def set_base_dir(sub_dir: str = None,
                 base_options: Dict[str, str] = None)-> Path:
    '''Determine the base directory.
    The base directory is the Queen's OneDrive, but the path to it changes
    with PC location.
    Arguments:
        base_options {Dict[str, str]} -- A dictionary describing conditions
            for setting the base directory. The key contains text to be
            searched for in the current working directory path.  The value is
            the base directory path to be set if the key is found.
        sub_dir {str} -- A string containing the directory path from the
            top directory to the desired base directory.
            A string containing the directory path from the base_dir to
            the file location.
    Raises:
        FileNotFoundError
    Returns:
        Path to the base directory.
    '''
    if not base_options:
        # Use Queen's OneDrive as the starting point for the base directory
        base_options = {'Greg': r"C:\Users\Greg\OneDrive - Queen's University", # Home laptop
                        'gsalomon': r"C:\Users\gsalomon\OneDrive - Queen's University"} # work PC
    cwd = str(Path.cwd())
    if 'Greg' in cwd:  # Home laptop
        base_dir = Path(r"C:\Users\Greg\OneDrive - Queen's University")
    elif 'gsalomon' in cwd: # Work PC
        base_dir = Path(r"C:\Users\gsalomon\OneDrive - Queen's University")
    else:
        raise FileNotFoundError('Unknown Base Path')
    if sub_dir:
        base_dir = base_dir / sub_dir
    return base_dir


class FileTypeError(FileNotFoundError):
    '''The file extension is not the appropriate type.
    '''
    pass


class FileTypes(list):
    '''A list of possible file types and their extensions.
    Contains a list of tuples with name of the file type as the first element
    of the tuple and the second a ";" delimited string containing the related
    file suffixes in the form "*.???".
    '''
    file_types = dict({'All Files':('*.*', ),
                       'Text Files':('*.txt', '*.csv', '*.tab',
                                     '*.rtf', '*.text'),
                       'Excel Files':('*.xls', '*.xlsx', '*.xlsm'),
                       'Image Files':('*.jpg', '*.jpeg', '*.gif',
                                      '*.gif', '*.png',
                                      '*.tif', '*.tiff', '*.psd'),
                       'Comma Separated Variable File':('*.csv', ),
                       'Text File':('*.txt', ),
                       'Pickle File':('*.pkl', ),
                       'Excel 2003 File':('*.xls', ),
                       'Excel 2010 File':('*.xlsx', '*.xlsm'),
                       'Word 2003 File':('*.doc', ),
                       'Word 2010 File':('*.docx', '*.docm')})


    def __init__(self, type_selection=None):
        '''Create a user select-able list of file type options.
        If type_selection is none, then all file types are allowed included.
        "directory" is a special file type that can be used to  trigger tests
        for a directory instead of a file type.
        Arguments:
            type_selection {List[str]} -- A list of the desired file types.
        '''
        super().__init__()
        self.type_select = set()
        self.all_types = False
        self.is_dir = False
        if type_selection is None:
            self.selection_list = list(self.file_types.keys())
        elif isinstance(type_selection, str):
            self.selection_list = (type_selection, )
        elif isinstance(type_selection, Iterable):
            self.selection_list = type_selection
        else:
            raise TypeError('type_selection must be a list of strings')
        for item in self.selection_list:
            type_name = str(item)
            if 'directory' in type_name:
                self.type_select = set()
                self.is_dir = True
            elif type_name in self.file_types:
                self.append((type_name, ';'.join(self.file_types[type_name])))
                for suffix in self.file_types[type_name]:
                    self.type_select.add(suffix.replace('*.', '.'))
            else:
                msg = '{} is not a valid file type group.'.format(type_name)
                raise FileTypeError(msg)
        if '.*' in self.type_select:
            self.all_types = True

    def valid_extension(self, extension: str)->bool:
        '''True if the supplied extention is in the list of valid exstensions.
        The extension string must be in the format ".???".
        Arguments:
            extension {str} -- The exstension to be tested.
        Returns:
            bool -- True if the supplied extention is valid.
        '''
        if self.is_dir:
            return False
        if self.all_types:
            return True
        if extension in self.type_select:
            return True
        else:
            return False

    def check_type(self, file_name: Path, must_exist = True)-> bool:
        '''Indicate whether the file has one of the suffixes.
        Arguments:
            file_name {Path} -- The full path to a file or directory.
            file_name {bool} -- Indicates whether the file must exist.
        Returns:
            True if file_name matches one of the suffixes otherwise False.
        '''
        is_match = False
        if self.is_dir:
            if must_exist:
                is_match = file_name.is_dir()
            else:
                is_match = not bool(file_name.suffix)
        elif self.all_types:
            if must_exist:
                is_match = file_name.is_file()
            else:
                is_match = not file_name.is_dir()
        else:
            is_match = file_name.suffix in self.type_select
        return is_match

    def disp(self)-> str:
        '''Generate a string describing the file types.
        Returns:
            str -- a formatted multi-line string listing the available file
                types.
        '''
        pass


def get_file_path(file_name: PathInput, sub_dir: str = None,
                  base_path: Path = None)-> Path:
    '''Build full file path from base directory and sub directories.
    Add the base path to a filename or relative string path.
    Check for presence of ':' or './' as indications that file_name is
        a full or relative path. Otherwise assume that file_name is a
        name or partial path to a file or directory.
     Arguments:
        file_name {str, Path} -- a name or partial path to a file or directory.
        sub_dir {str} -- A string containing the directory path from the base path to
            the file location.
        base_path {Path} -- A path to the top directory where files may be located.
    Returns:
        A full path to the file or directory
    Raises
        TypeError -- if file_name is not type Path or type str.
    '''
    if isinstance(file_name, Path): # Already full path
        return file_name.resolve()
    file_name = str(file_name)
    if any(a in file_name for a in[':', './/']):  #Full path of type str
        return Path(file_name).resolve()
    if base_path:
        base_dir = base_path.resolve()
    else:
        base_dir = set_base_dir()
    if sub_dir:
        base_dir = base_dir / sub_dir
    full_path = base_dir / file_name
    return full_path.resolve()


def make_full_path(file_name: PathInput, valid_types: FileTypes,
                   must_exist=True, base_path: Path = None)-> Path:
    ''' If file_path is a string convert it to type Path.
        Resolve any relative path parts.
        Check that the supplied path exists and is a file.
    Arguments:
        file_name {PathInput} -- The full path to a file or directory.
        valid_types {FileTypes} -- The expected file or directory types.
        must_exist {bool} -- Indicates whether the file or directory must exist
    Returns:
        A full path to the file or directory
    Raises:
        FileTypeError -- if the file or directory is not of the right type.
        FileNotFoundError -- if the file or directory does not exist.
    '''
    full_file_path = get_file_path(file_name = file_name, base_path = base_path)
    if must_exist:
        if not full_file_path.exists():
            msg = 'The file path must refer to an existing file'
            raise FileNotFoundError(msg)
    if not valid_types.check_type(full_file_path, must_exist):
        msg = '{} is not a valid file type.'.format(full_file_path)
        raise FileTypeError(msg)
    return full_file_path


def replace_top_dir(dir_path: Path, file_path: Path, new_name: str)-> str:
    ''' Replace the first portion of the file path.
    Arguments:
        dir_path {PathInput} -- The root portion of the file path to be removed.
        file_path {Path} -- The full path to a file.
        new_name {str} -- The string to substitute for the root directory.
    Returns:
        A string with the root directory portion replaced.
    Raises:
        TypeError exception
        FileNotFoundError exception
    '''
    # If directory_path is a string treat it as a partial and combine it
    # with the base path.
    if FileTypes('directory').check_type(dir_path):
        remove_str = str(dir_path)
    if remove_str not in str(file_path):
        msg_str = '{dir_str} is not a parent of {file_str}\n\t'
        msg_str = ' The top directory path will not be removed.'
        msg = msg_str.format(dir_str=str(dir_path),
                             file_str=str(file_path))
        # TODO output warning message
    file_str_sup = str(file_path).replace(remove_str, new_name)
    return file_str_sup


def clean_ascii_text(text: str, charater_map: Dict[str, str] = None)-> str:
    '''Remove non ASCII characters from a string.
    This is intended to deal with encoding incompatibilities.
    Special character strings in the test are replace with their ASCII
    equivalent All other non ASCII characters are removed.
    Arguments:
        text {str} -- The string to be cleaned.
        charater_map {optional, Dict[str, str]} -- A mapping of UTF-8 or other
        encoding strings to an alternate ASCII string.
    '''
    special_charaters = {'cm³': 'cc'}
    if charater_map:
        special_charaters.update(charater_map)
    for (special_char, replacement) in special_charaters.items():
        if special_char in text:
            patched_text = text.replace(special_char, replacement)
        else:
            patched_text = text
    bytes_text = patched_text.encode(encoding="ascii", errors="ignore")
    clean_text = bytes_text.decode()
    return clean_text


def get_file_mod_time(file:Path, date_format='%Y-%m-%d %H:%M:%S')->str:
    '''Return the file modification time as a formatted string.
    Arguments:
        file {Path} -- The path to the file.
        date_format {str} -- The string specifying the format for the
            returned time stamp.  Default is '%Y-%m-%d %H:%M:%S'
    Returns:
        The file modification date as a formatted string.
    '''
    modification_time = file.stat().st_mtime
    modification_date=time.strftime(date_format,
                                    time.localtime(modification_time))
    return modification_date


def dir_iter(directory_to_scan: Path, sub_dir: str = None,
             base_path: Path = None,
             file_type: Union[FileTypes, str, List[str]] = None             
             )->Iterator[Path]:
    '''Returns an iterator which scans a dictionary tree and returns files of
    a given type.
    Arguments:
        directory_to_scan {Path} -- The top directory to scan for files.
        sub_dir {str} -- A string containing the directory path from the base
            path to the file location.
        base_path {Path} -- A path to the top directory where files may be
            located.
        file_type {Optional, FileType} -- The suffix or list of suffixes of
         the file types to return.
    Returns {Iterator[Path]}:
        An iterator through the files of the specified types in
        directory_to_scan or a sub directory.
    '''
    scan_dir_path = get_file_path(directory_to_scan, sub_dir, base_path)
    for file_item in scan_dir_path.iterdir():
        # if the item is a file generate a FileStat object with it
        if file_item.is_file():
            if file_type is None:
                yield file_item
            elif isinstance(file_type, FileTypes):
                if file_type.valid_extension(file_item.suffix):
                    yield file_item
            elif file_item.suffix in file_type:
                yield file_item
        elif file_item.is_dir():
            # recursively scan sub-directories
            for sub_file_item in dir_iter(file_item, file_type):
                yield sub_file_item
