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

PathInput = Optional[Path, str, None]

base_path = Path.cwd()


def trueiterable(variable):
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
        self.type_list = list()
        self.all_types = False
        self.is_dir = False
        if type_selection is None:
            selection_list = list(self.file_types.keys())
        elif not trueiterable(type_selection):
            raise TypeError('type_selection must be a list of strings')
        else:
            selection_list = type_selection
        for item in selection_list:
            type_name = str(item)
            if 'directory' in type_name:
                self.type_list = None
                self.is_dir = True
            elif type_name in self.file_types:
                self.append((type_name, ';'.join(self.file_types[type_name])))
                self.type_list.extend(sufix.replace('*.', '.')
                                      for sufix in self.file_types[type_name])
            else:
                msg = '{} is not a valid file type group.'.format(type_name)
                raise FileTypeError(msg)
        if '.*' in self.type_list:
            self.all_types = True

    def suffix_match(self, file_name: Path)->bool:
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
            is_match = True
        else:
            is_match = file_name.suffix in self.type_list
        return is_match


# Functions to check directories and files
def valid_dir(dir_path: PathInput, exist=True)->Path:
    ''' If dir_path is a string convert it to type Path.
        Resolve any relative path parts.
        Check that the supplied path exists and is a directory.
    Arguments:
        dir_path: Type Path or str
            a relative or full path to a directory
        exist: Type bool
            Check whether the directory exists
    Returns:
        A full path to an existing directory of type Path
    Raises:
        TypeError exception
        NotADirectoryError exception
    '''
    if isinstance(dir_path, Path):
        full_directory_path = dir_path.resolve()
    elif isinstance(dir_path, str):
        full_directory_path = Path(dir_path).resolve()
    else:
        raise TypeError('The directory path must be Type Path or str')
    if exist:
        if full_directory_path.is_dir():
            return full_directory_path
        else:
            raise NotADirectoryError(\
                'The directory path must refer to an existing directory')
    else:
        return full_directory_path

# TODO merge valid_file and valid_dir
def valid_file(file_path: Path, exist=True):
    ''' If file_path is a string convert it to type Path.
        Resolve any relative path parts.
        Check that the supplied path exists and is a file.
    Parameters
        file_path: Type Path or str
            a relative or full path to a file
        exist: Type bool
            Check whether the file exists
    Returns
        A full path to an existing file of type Path
    Raises
        TypeError exception
        FileNotFoundError exception
    '''
    if isinstance(file_path, Path):
        full_file_path = file_path.resolve()
    elif isinstance(file_path, str):
        full_file_path = Path(file_path).resolve()
    else:
        raise TypeError('The file path must be Type Path or str')
    if exist:
        if full_file_path.exists():
            return full_file_path
        else:
            msg = 'The file path must refer to an existing file'
            raise FileNotFoundError(msg)
    else:
        return full_file_path



def insert_base_path(self, file_name: str):
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
        TypeError exception
    '''
    if isinstance(file_name, Path):
        full_path = file_name.resolve()
        return full_path
    elif isinstance(file_name, str):
        if any(a in file_name for a in[':', './']):
            full_path = Path(file_name).resolve()
            return full_path
        else:
            full_path = self.base_path / file_name
            return full_path
    else:
        raise TypeError('file_name must be Type Path or str')


def update_top_dir(self, dir_path):
    ''' Update the first portion of the directory name to be removed.
    Parameter
        dir_path: Type Path or str
            A valid path containing the first portion of the directory
            name to be removed.
    Raises
        NameInUse
    dir_path must be a parent of self.directory_to_scan or an empty
    string.
    '''
    # If scanning a directory check that dir_path exists
    exists = self.do_dir_scan
    # If directory_path is a string treat it as a partial and combine it
    # with the base path.
    if isinstance(dir_path, str):
        remove_path = self.valid_dir(self.insert_base_path(dir_path), exist=exists)
    else:
        remove_path = dir_path.resolve()
    # If scanning a directory check that remove_path is a parent of
    # directory_to_scan.
    if exists and str(remove_path) not in str(self.directory_to_scan):
        status = str(remove_path) + \
                    ' is not a parent of ' + \
                    str(self.directory_to_scan) + \
                    ' Top directory path will not be removed.'
        warnings.warn(status, InvalidPath)
        remove_path = ''
    self.top_dir = str(remove_path)
