'''
Created on Aug 11 2017

@author: Greg Salomons
Define parameters required for DirScan.

Warnings
    NameInUse:
        An output file or sheet name is already in use.
    InvalidPath:
        The given path is not a valid selection.
Exceptions
    NameInUse:
        An output file or sheet name is already in use.
    InvalidPath:
        The given path is not a valid selection.
    FileTypeError:
        The file extension is not the appropriate type.
    SelectionError:
        The string contents are not valid.
Classes
    dir_scan_parameters:  Input parameters required for DirScan.

Functions
    valid_dir:
        Convert string to path if required, check that the path is an
        existing directory and return the full path.
    valid_file:
        Convert string to path if required, check that the path is an
        exiting file and return the full path.
    valid_sheet_name
        Check that the supplied sheet_name is valid.
'''
from pathlib import Path
import warnings
from file_type_definitions import FileTypes


#Warning and Exception definitions
class ParameterWarning(UserWarning):
    '''Base warning for setting and getting parameters.
    '''
    pass
class ParameterError(Exception):
    '''Base exception for setting and getting parameters.
    '''
    pass

class NameInUse(ParameterWarning):
    '''An output file or sheet name is already in use.
    '''
    pass
class InvalidPath(ParameterWarning):
    '''The given path is not a valid selection.
    '''
    pass
class FileTypeError(ParameterError, FileNotFoundError):
    '''The file extension is not the appropriate type.
    '''
    pass
class SelectionError(ParameterError, TypeError):
    '''The string contents are not valid.
    '''
    pass


def valid_sheet_name(sheet_name: str):
    ''' Check that the supplied sheet_name is valid.
    Parameter
        sheet_name: Type str
            An excel worksheet name.
    Returns
        A full path to an existing file of type Path
    Raises
        TypeError exception
    '''
    if not isinstance(sheet_name, str):
        raise TypeError('The sheet name must be Type str')
    else:
        #ToDo Add legal worksheet name tests
        return True

# Principal class definition
class ParametersBase(object):
    '''Base class for parameter objects used by DirScan.
    Class Attributes:
        base_path
            Type: Path
            The starting path to use for incomplete file and directory
            parameters
            Default = Path.cwd()
    Instance Attributes:
        parameters_valid
            Type bool
            Indicate whether the parameters object contains validated
            parameters.
            Default = True
    Methods
        valid_dir(dir_path: Path, exist=True):
            Static method
            Check that the supplied path exists and is a directory.
        valid_file(file_path: Path, exist=True):
            Static method
            Check that the supplied path exists and is a file.
        __init__(base_path=None, **kwargs):
			Set attributes
			Verify that attributes are reasonable
        insert_base_path(file_name: str):
            Add the base path to a filename or relative string path and
            return a full path to a file or directory of type Path.
        update_parameters(base_path=None, **kwargs)
            Update any supplied parameters by calling the relevant method.

        The following methods are used to test and modify individual
        parameter attributes:
            update_base_path(directory_path: Path):
                Update the base path used to complete any file name or partial
                paths.
        The following methods set boolean options to True or False
            set_parameters_valid(is_valid: bool):
                Indicate whether the parameters object contains validated
                parameters.
    '''
	# Initialize class level parameters
    base_path = Path.cwd()

    # Methods to check directories, files and sheet names
    @staticmethod
    def valid_dir(dir_path: Path, exist=True):
        ''' If dir_path is a string convert it to type Path.
            Resolve any relative path parts.
            Check that the supplied path exists and is a directory.
        Parameters:
            dir_path: Type Path or str
                a relative or full path to a directory
            exist: Type bool
                Check whether the directory exists
        Returns
            A full path to an existing directory of type Path
        Raises
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

    @staticmethod
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


    def __init__(self, base_path=None, **kwargs):
        '''
        Initialize all parameters, using default values if a value is
        not supplied
        '''
		# Initialize all parameters, using default values
        self.base_path = Path.cwd()
		# Initialize boolean options, using default values
        self.parameters_valid = True

        # Update all parameters passed as arguments.
        self.update_parameters(base_path, **kwargs)

    def update_parameters(self, base_path=None, **kwargs):
        '''Update any supplied parameters.
        '''
        if base_path is not None:
            self.update_base_path(base_path)
        # Set boolean options using defined method
        # Boolean options should be set before any corresponding
        # parameters are changed.
        for item in kwargs:
            if hasattr(self, 'set_' + item):
                set_method = getattr(self, 'set_' + item)
                set_method(kwargs[item])
        # Set passed parameters using defined method
        for item in kwargs:
            if hasattr(self, 'update_' + item):
                set_method = getattr(self, 'update_' + item)
                set_method(kwargs[item])


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

    #The following methods are used to check and update parameters
    def update_base_path(self, directory_path: Path):
        ''' Update the base path.
        directory_path must exist and be a directory.
        directory_path must be of type Path.
        Parameter
            directory_path: Type Path
                The path to be used to complete any file name or partial
                paths
        Raises
            TypeError exception
        '''
        if not isinstance(directory_path, Path):
            raise TypeError('directory_path must be Type Path')
        full_directory_path = self.valid_dir(directory_path)
        self.base_path = full_directory_path

    # The following methods set boolean options to True or False
    def set_parameters_valid(self, is_valid: bool):
        '''Indicate whether the parameters object contains validated
        parameters.
        Parameter
            is_valid: Type bool
                True: Parameters have passed all validation tests.
                False: At least one parameter is not valid.
        Raises
            TypeError
        '''
        try:
            self.parameters_valid = bool(is_valid)
        except TypeError as err:
            raise err('do_scan must be True or False')


# Principal class definition


class DirScanParameters(ParametersBase):
    '''Contains all parameters required for scanning a directory tree and
        saving the results.
    Class Attributes:
        base_path (inherited)
            Type: Path
            The starting path to use for incomplete file and directory
            parameters
            Default = Path.cwd()

    The following Class-level attributes are currently not updated directly:
        dir_command_switches
            Type: List of Strings
            The switches used by the DIR command
                /S   Displays files in specified directory and all
                      subdirectories.
                /-C  Disable display of the thousand separator in file sizes.
                /N   New long list format where filenames are on the far
                     right.
                /4   Displays four-digit years
                /T   Controls which time field displayed or used for sorting
            Default = ["/S", "/-C", "/N", "/4", "/T"+time_type]
        file_data_variables
            Type: List of Strings
            A list of the variable names used for the file_data output
            Default =
               ['Source','Directory','File Name','Size','Date','Time','Type']
        dir_summary_variables
            Type: List of Strings
            A list of the variable names used for the dir_data output
            Default = ['Source', 'Directory', 'NumFiles', 'DirSize']

    Instance Attributes:
        directory_to_scan
            Type: Path
            The path to the top directory of a tree to scan
            Default = base_path
        file_to_scan
            Type: Path
            The path to a text file containing the output from an
                MS DIR command
            The file must exists and the extension must be ".txt"
            Default = base_path / 'dir_output.txt'
        directory_scan_output
            Type: Path
            The path to a text file where the raw output from an
                MS DIR command will be saved
            The extension must be ".txt"
            Default = base_path / 'dir_output.txt'
        file_data_output
            Type: Path
            The path to a .csv or excel file where the results of the
                file scanning will be written
            The file extension must be either ".csv", ".xls" or ".xlsx"
            Default = base_path / "file_data.csv"
        dir_data_output
            Type: Path
            The path to a .csv or excel file where the results of the
                directory summary will be written.
            The file extension must be either ".csv", ".xls" or ".xlsx"
            Default = base_path / "dir_data.csv"
        file_data_sheet
            Type: String
            If file_data_output refers to an excel file, the name of the
                worksheet within that file where the results of the
                file scanning will be written.
            Default = File Data"
        dir_data_sheet
            Type: String
            If dir_data_output refers to an excel file, the name of the
                worksheet within that file where the results of the
                directory summary will be written.
            Default = "Dir Data"
        top_dir
            Type: String
            A string containing the first portion of the directory name to
            be removed.
            Default = ""
        source
            Type: String
            A string intended to identify the top level of the directory.
                e.g.: My Jump Drive
            Default = ""
        time_type
            Type: String, one of [C, A, W]
            Indicates which date stamp to request with the DIR command:
                C  Creation date
                A  Last Access date
                W  Last Written date
            Default = "W"
        status
            Type: String
            Indicates the current stage of the program or any
            error/warning messages
            Default = ""

    The following Action attributes select the processing options:
    All of these attributes are of type Boolean.
        do_dir_scan
            Indicates whether to run the scan_dir method on the selected
            directory tree or parse a selected scan_dir output file.
            Default = True
        save_scan_output
            Indicates whether to save the output from the scan_dir method
            to a text file or directly parse it.
            If scan_directory is False this attribute is ignored.
            Default = True
        parse_dir_data
            Indicates whether to parse the output from the scan_dir method.
            If scan_directory is False this attribute is ignored.
            Default = True
        output_file_data
            Indicates whether to save the file data from the parse results.
            If scan_directory is or parse_dir_data are False this attribute
            is ignored.
            Default = True
        output_dir_data
            Indicates whether to save the directory data from the parse
            results.
            If scan_directory is or parse_dir_data are False this attribute
            is ignored.
            Default = True

    Methods
        __init__
			Set attributes
			Verify that attributes are reasonable
        The following methods are used to test or modify passed parameters
            add_base_path(file_name: str)  (inherited)
            is_output_collision()
        The following methods are used to check and update parameters
            update_directory_to_scan(directory_path)
            update_file_to_scan(file_path)
            update_directory_scan_output(file_path)
            update_file_data_output(file_path)
            update_dir_data_output(file_path)
            update_file_data_sheet(sheet_name str)
            update_dir_data_sheet(sheet_name str)
            update_top_dir(dir_path)
            update_source(path_name)
            update_time_type(time_code)
        The following methods set action options to True or False
            set_do_dir_scan(do_scan: bool)
            set_save_scan_output(save_scan: bool):
            set_parse_dir_data(parse_dir: bool)
            set_output_file_data(save_file_data: bool)
            set_output_dir_data(save_dir_data: bool)
    '''
	# Initialize class level parameters
    dir_command_switches = ''
    dir_summary_variables = []
    file_data_variables = []

    #The following method initializes parameters
    def __init__(self, base_path=None, **kwargs):
        '''
        Initialize all parameters, using default values if a value is
        not supplied
        '''
        # set the base path
        self.update_parameters(base_path)
		# Initialize all parameters using default values
        self.directory_to_scan = self.base_path
        self.file_to_scan = self.base_path / 'dir_output.txt'
        self.directory_scan_output = self.base_path / 'dir_output.txt'
        self.file_data_output = self.base_path / "file_data.csv"
        self.dir_data_output = self.base_path / "dir_data.csv"
        self.file_data_sheet = 'File Data'
        self.dir_data_sheet = 'Dir Data'
        self.top_dir = ""
        self.source = ""
        self.time_type = "W"
        self.status = ""
        self.action_text = ''
        self.dir_command_switches = ["/S", "/-C", "/N", "/4",
                                     "/T:"+self.time_type]
        self.dir_summary_variables = ['Source', 'Directory', 'NumFiles',
                                      'DirSize']
        self.file_data_variables = ['Source', 'Directory', 'File Name',
                                    'Size', 'Date', 'Time', 'Type']
		# Initialize action options, using default values
        self.do_dir_scan = True
        self.save_scan_output = True
        self.parse_dir_data = True
        self.output_file_data = True
        self.output_dir_data = True
		# Initialize action methods, using default values
        self.action_methods = dict()
        self.action_sequences = dict()
        self.selected_action = None
        self.run_label = 'Run'
        # Set all passed parameter values
        super().__init__(**kwargs)

    #The following methods are used to test or modify passed parameters
    #TODO add method to test for valid set of action options
    def is_output_collision(self):
        '''Check that the file data output and Dir data output are not the
           same.
        Returns
            A boolean True if a collision is found.
        '''
        if self.dir_data_output == self.file_data_output:
            if 'csv' in self.dir_data_output.suffix:
                return True
            elif self.dir_data_sheet == self.file_data_sheet:
                return True

    def update_action_methods(self, actions: dict):
        '''Create a dictionary of callable methods.
        '''
        for (action_name, action_method) in actions:
            if callable(action_method):
                self.action_methods[action_name] = action_method
            else:
                message = 'The method {} for {} is not valid; Ignored'.format(
                    str(action_name), str(action_method))
                raise ParameterWarning(message)

    def valid_action(self, action_name):
        return action_name in self.action_methods

    def update_action_sequences(self, action_sets: dict):
        '''Create a dictionary of callable methods.
        '''
        for (sequence_name, action_sequence) in action_sets:
            if all(self.valid_action(action_name) in self.action_methods):
                self.action_sequence[sequence_name] = action_method
            else:
                message =  'The action {} in sequence {} is not valid.\n'
                message += 'The sequence will be ignored'
                message = message.format(str(action_name), str(action_method))
                raise ParameterWarning(message)

    def update_selected_action(self, action_sequence):
        '''Create a dictionary of callable methods.
        '''
        if action_sequence in self.action_sequences:
            self.selected_action = action_sequence
        else:
            raise ParameterError('% is not a valid action sequence'%action_sequence)

    def set_action_sequence(self):
        '''select the action sequence based on the action options.
        '''
        if self.do_dir_scan:
            if self.parse_dir_data:
                self.update_selected_action('Scan and Parse')
                self.run_label = 'Scan and Parse'
            else:
                self.update_selected_action('Scan and Save')
                self.run_label = 'Scan and Save'
        else:
            self.update_selected_action('Parse File')
            self.run_label = 'Parse File'

    def run(self):
        '''Perform the action sequence
        '''
        action_sequence = self.action_sequences[self.selected_action]
        for action in action_sequence:
            # TODO probably need to add value passing from one action to the next.
            action(self)


    #The following methods are used to check and update parameters
    def update_directory_to_scan(self, directory_path):
        ''' Update the directory to scan.
        If do_dir_scan is False, do not update the parameter.
        Parameter
            directory_path: Type Path or str
                The directory path to be scanned.
        If directory_path is a string treat it as a partial and combine it
        with the base path.
        directory_path must exist and be a directory.
        '''
        # If directory_path is a string treat it as a partial and
        # combine it with the base path, then check that the directory exits.
        if self.do_dir_scan:
            scan_path = self.valid_dir(self.insert_base_path(directory_path))
            self.directory_to_scan = scan_path

    def update_file_to_scan(self, file_path):
        ''' Update the name of a text file containing the output from an MS
        DIR command for parsing.
        If do_dir_scan is True, do not update the parameter.
        Parameter
            file_path: Type Path
                The file containing scan results to be parsed.
        Raises
            FileTypeError exception
        If file_path is a string treat it as a partial and combine it with
        the base path.
        The file must exist and the extension must be ".txt"
        '''
        # If directory_path is a string treat it as a partial and combine it
        # with the base path
        if not self.do_dir_scan:
            scan_file = self.valid_file(self.insert_base_path(file_path))
            if 'txt' in scan_file.suffix:
                self.file_to_scan = scan_file
            else:
                raise FileTypeError('File for scanning must be of type ".txt"')

    def update_directory_scan_output(self, file_path):
        ''' Update the name of a text file where the output from an
            MS DIR command will be stored.
        If do_dir_scan is False, or save_scan_output is False,
        do not update the parameter.
        Parameter
            file_path: Type Path
                The file containing scan results to be parsed.
        Raises
            FileTypeError exception
        If file_path is a string treat it as a partial and combine it with
        the base path.
        The file extension must be ".txt"
        '''
        # If file_path is a string treat it as a partial and combine it with
        # the base path
        if self.do_dir_scan and self.save_scan_output:
            scan_file = self.insert_base_path(file_path)
            # If the scan_file already exists issue a warning
            if 'txt' in scan_file.suffix:
                try:
                    scan_file = self.valid_file(scan_file)
                except FileNotFoundError:
                    status = str(scan_file) + \
                        ' already exists and will be overwritten.'
                    warnings.warn(status, NameInUse)
                finally:
                    self.directory_scan_output = scan_file
            else:
                raise FileTypeError(
                    'File for scanning must be of type ".txt"')

    def update_file_data_output(self, file_path):
        ''' Update the name of a file where the results of the file scanning
        will be written.
        If parse_dir_data is False, or output_file_data is False,
        do not update the parameter.
        Parameter
            file_path: Type str
                A name or partial path to a file or directory used for
                file data output
        Raises
            FileTypeError
            NameInUse
        If file_path is a string treat it as a partial and combine it with
        the base path.
        The file extension must be either ".csv", ".xls" or ".xlsx"
        If the file extension is ".csv" file_data_output and dir_data_output
            should not be identical.
        '''
        # If directory_path is a string treat it as a partial and combine it
        # with the base path
        if self.parse_dir_data and self.output_file_data:
            output_file = self.insert_base_path(file_path)
            if output_file.suffix not in ['.csv', '.xls', '.xlsx']:
                msg = 'Output file must be of type ".csv", ".xls" or ".xlsx"'
                raise FileTypeError(msg)
            else:
                self.file_data_output = output_file
                if self.is_output_collision():
                    status = str(output_file) + \
                        ' is already in use as the directory data output file'
                    warnings.warn(status, NameInUse)

    def update_dir_data_output(self, file_path):
        ''' Update the name of a file where the results of the directory
            scanning will be written.
            If parse_dir_data is False, or output_dir_data is False,
            do not update the parameter.
        Parameter
            file_path: Type str
                A name or partial path to a file or directory used for
                directory data output
        Raises
            FileTypeError
            NameInUse
        If file_path is a string treat it as a partial and combine it with
        the base path.
        The file extension must be either ".csv", ".xls" or ".xlsx"
        If the file extension is ".csv" file_data_output and dir_data_output
            should not be identical.
        '''
        # If directory_path is a string treat it as a partial and combine it
        # with the base path
        if self.parse_dir_data and self.output_dir_data:
            output_file = self.insert_base_path(file_path)
            if output_file.suffix not in ['.csv', '.xls', '.xlsx']:
                msg = 'Output file must be of type ".csv", ".xls" or ".xlsx"'
                raise FileTypeError(msg)
            else:
                self.dir_data_output = output_file
                if self.is_output_collision():
                    status = str(output_file)
                    status += ' is already in use as the output file'
                    status += ' for file data.'
                    warnings.warn(status, NameInUse)

    def update_file_data_sheet(self, sheet_name: str):
        ''' Update the name of an excel worksheet where the results of the
            file scanning will be written.
            If parse_dir_data is False, or output_file_data is False,
            do not update the parameter.
        Parameter
            sheet_name: Type str
                The name of the worksheet where the results of the
                file scanning will be written.
        Raises
            NameInUse
        Only used if file_data_output refers to an excel file.
        file_data_sheet and dir_data_sheet should not be identical.
        '''
        if self.parse_dir_data and self.output_file_data:
            if valid_sheet_name(sheet_name):
                self.file_data_sheet = sheet_name
                if self.is_output_collision():
                    status = str(sheet_name)
                    status += ' is already in use as the'
                    status += ' worksheet for directory data.'
                    warnings.warn(status, NameInUse)

    def update_dir_data_sheet(self, sheet_name: str):
        ''' Update the name of an excel worksheet where the results of the
            directory scanning will be written.
            If parse_dir_data is False, or output_dir_data is False,
            do not update the parameter.
        Parameter
            sheet_name: Type str
                The name of the worksheet where the results of the
                directory scanning will be written.
        Raises
            NameInUse
        Only used if dir_data_output refers to an excel file.
        file_data_sheet and dir_data_sheet should not be identical if
            file_data_output and dir_data_output are identical.
        '''
        if self.parse_dir_data and self.output_dir_data:
            if valid_sheet_name(sheet_name):
                self.dir_data_sheet = sheet_name
                if self.is_output_collision():
                    status = str(sheet_name) + \
                        ' is already in use as the worksheet for file data'
                    warnings.warn(status, NameInUse)

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

    def update_source(self, path_name):
        ''' Update the string intended to identify the top level of the
        directory.
        Parameter
            path_name: Type str
                A string intended to identify the top level of the directory.
        Raises
            TypeError
        '''
        if not isinstance(path_name, str):
            raise TypeError('path_name must be type str')
        self.source = path_name

    def update_variables(self, time_code_def):
        '''Update the Variable Names 'Date', 'Time' based on the time code.
        '''
        var_names = ['Date', 'Time']
        for var in var_names:
            var_index = self.file_data_variables.index(var)
            header = time_code_def[self.time_type].replace('X', var)
            self.file_data_variables[var_index] = header

    def update_time_type(self, time_code):
        ''' Update the Code for the Time stamp to be obtained.
        Parameter
            time_code: Type str
                The code to select the date stamp type to request with the
                DIR command.
        Raises
            SelectionError
        time_code must be one of ["C", "A", "W"]
        '''
        if not isinstance(time_code, str):
            raise TypeError('path_name must be type str')
        #Definitions for time codes
        time_code_def = dict(C='Creation X',
                             A='Last Access X',
                             W='Last Written X')
        if time_code not in time_code_def:
            raise SelectionError('time_code must be one of "C", "A" or "W"')
        self.time_type = time_code
        #Update the command switches
        self.dir_command_switches = \
            ["/S", "/-C", "/N", "/4", "/T"+time_code]
        self.update_variables(time_code_def)

    def update_status(self, status=None):
        '''Update the current program status with current module or
        warning messages.
        Parameter
            status: Type str or Exception
                The current module or an exception.
        '''
        if status:
                self.status = str(status)
        else:
            raise SelectionError('Cannot have Status of "None"')

    # The following methods set action options to True or False
    def set_do_dir_scan(self, do_scan: bool):
        '''Indicate whether a directory should be scanned or a file parsed.
        Parameter
            do_scan: Type bool
                True: Use Dir command to scan a directory tree.
                False: Parse Dir command output saved to a file.
        Raises
            TypeError
        '''
        if not isinstance(do_scan, bool):
            raise TypeError('do_scan must be True or False')
        self.do_dir_scan = do_scan

    def set_save_scan_output(self, save_scan: bool):
        '''Indicate whether a the output of a directory scan should be saved
        to a file.
        Parameter
            save_scan: Type bool
                True: Save the results of the directory tree scan to a file.
                False: Only parse the results of the directory tree scan.
        Raises
            TypeError
        '''
        if not isinstance(save_scan, bool):
            raise TypeError('save_scan must be True or False')
        self.save_scan_output = save_scan

    def set_parse_dir_data(self, parse_dir: bool):
        '''Indicate whether a the output of a directory scan should be parsed.
        Parameter
            parse_dir: Type bool
                True: Parse the data from a directory tree scan.
                False: Only save the directory tree scan output to a file.
        Raises
            TypeError
        '''
        if not isinstance(parse_dir, bool):
            raise TypeError('parse_dir must be True or False')
        self.parse_dir_data = parse_dir

    def set_output_file_data(self, save_file_data: bool):
        '''Indicate whether a the parsed file data should be saved to a file.
        Parameter
            save_file_data: Type bool
                True: Save the file data obtained from parsing a directory
                tree.
                False: Do not save the file data.
        Raises
            TypeError
        '''
        if not isinstance(save_file_data, bool):
            raise TypeError('save_file_data must be True or False')
        self.output_file_data = save_file_data

    def set_output_dir_data(self, save_dir_data: bool):
        '''Indicate whether a the parsed directory summary data should be
           saved to a file.
        Parameter
            save_dir_data: Type bool
                True: Save the directory summary data.
                False: Do not save the directory summary data.
        Raises
            TypeError
        '''
        if not isinstance(save_dir_data, bool):
            raise TypeError('save_dir_data must be True or False')
        self.output_dir_data = save_dir_data


def main():
    '''Test the Parameters class definition
    '''
    base_path = Path('.')
    scan_dir = 'Test Dir Structure'

    scan_parameters = \
        DirScanParameters(base_path,
                          directory_to_scan=scan_dir,
                          source='Test Files',
                          top_dir=base_path,
                          time_type='W')
    print(scan_parameters)
    #data_file = base_path / 'Test_Files.txt'
    #file = open(data_file, "r")

if __name__ == '__main__':
    main()
