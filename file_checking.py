'''
Created on Nov 27 2018
@author: Greg Salomons
Definition of file type groups

Classes
    FileTypes:
        A user select-able list of file type options
    FileTypeError:
        The file extension is not the appropriate type.
'''
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Set, Any, Union
from collections.abc import Iterable

PathInput = Union[Path, str]

base_path = Path.cwd()


def true_iterable(variable):
    '''Indicate if the variable is a non-string type iterable
    '''
    return not isinstance(variable, str) and isinstance(variable, Iterable)


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
    file_types = dict({'All Files':('*.*',),
                       'Text Files':('*.txt', '*.csv', '*.tab',
                                     '*.rtf', '*.text'),
                       'Excel Files':('*.xls', '*.xlsx', '*.xlsm'),
                       'Image Files':('*.jpg', '*.jpeg', '*.gif',
                                      '*.gif', '*.png',
                                      '*.tif', '*.tiff', '*.psd'),
                       'Comma Separated Variable File':('*.csv',),
                       'Text File':('*.txt',),
                       'Excel 2003 File':('*.xls',),
                       'Excel 2010 File':('*.xlsx', '*.xlsm'),
                       'Word 2003 File':('*.doc',),
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
            selection_list = list(self.file_types.keys())
        elif isinstance(type_selection, str):
            selection_list = (type_selection,)
        elif isinstance(type_selection, Iterable):
            selection_list = type_selection
        else:
            raise TypeError('type_selection must be a list of strings')
        for item in selection_list:
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

    def check_type(self, file_name: Path)->bool:
        '''Indicate whether the file has one of the suffixes.
        Arguments:
            file_name {Path} -- The full path to a file or directory.
        Returns:
            True if file_name matches one of the suffixes otherwise False.
        '''
        is_match = False
        if self.is_dir:
            is_match = file_name.is_dir()
        elif self.all_types:
            is_match = not file_name.is_dir()
        else:
            is_match = file_name.suffix in self.type_select
        return is_match
    
    def disp(self)->str:
        '''Generate a string describing the file types.
        Returns:
            str -- a formatted multiline string listing the available file types.
        '''
        pass


# Functions to check directories and files
def insert_base_path(file_name: PathInput, base_path: Path = None)->Path:
    '''Add the base path to a filename or relative string path.
    Check for presence of ':' or './' as indications that file_name is
        a full or relative path. Otherwise assume that file_name is a
        name or partial path to a file or directory.
    Parameter
        file_name: Type str
            a name or partial path to a file or directory
    Returns
        A full path to a file or directory of type Path
    Raises
        TypeError -- if file_name is not type Path or type str.
        ValueError -- if a full path cannot be built.
    '''
    if isinstance(file_name, Path):
        full_path = file_name.resolve()
    elif isinstance(file_name, str):
        if any(a in file_name for a in[':', './']):  # Check for a full path of type str
            full_path = Path(file_name).resolve()
        elif base_path:
            full_path = base_path / file_name
        else:
            msg_str = 'No base path was provided, so the file name must be a '
            msg_str +='complete path.\n\tGot {}'
            msg = msg_str.format(file_name)
            raise ValueError(msg)
    else:
        msg_str = 'file_name must be Type Path or str.\n\tGot:\t{}'
        msg = msg_str.format(type(file_name))
        raise TypeError(msg)
    return full_path


def make_full_path(file_name: PathInput, valid_types: FileTypes,
                   must_exist=True, base_path :Path = None)->Path:
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
    full_file_path = insert_base_path(file_name, base_path)
    if must_exist:
        if not full_file_path.exists():
            msg = 'The file path must refer to an existing file'
            raise FileNotFoundError(msg)
    else:
        if not valid_types.check_type(full_file_path):
            msg = '{} is not a valid file type.'.format(full_file_path)
            raise FileTypeError(msg)
    return full_file_path


def replace_top_dir(dir_path: Path, file_path: Path, new_name: str)->str:
    ''' Replace the first portion of the file path.
    Arguments:
        dir_path {PathInput} -- The root portion of the file path to be removed.
        file_path {Path} -- The full path to a file.
        new_name {str} -- The string to substitute for the root directory.
    Returns:
        A string with thr root directory portion replaced.
    Raises:
        TypeError exception
        FileNotFoundError exception
            Parameter
        dir_path: Type Path or str
            A valid path containing the first portion of the directory
            name to be removed.
    Raises
        NameInUse
    dir_path must be a parent of self.directory_to_scan or an empty
    string.
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
    file_str_sup = str(file_path).replace(remove_str, new_name)
    return file_str_sup