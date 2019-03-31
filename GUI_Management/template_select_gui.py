'''
Created on Aug 26Jan 12 2019

@author: Greg Salomons
Initial GUI interface for building Structure Templates.

Classes
    DirGui:
        Primary GUI window
        sub class of TKinter.Frame

'''

import tkinter.filedialog as tkf
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from functools import partial

from structure_set_parameters import ParametersBase
from structure_set_parameters import DirScanParameters
from file_type_definitions import FileTypeError
from file_type_definitions import FileTypes
#from dir_scan_parser import parse_dir_scan
#from dir_scan import scan_and_parse


# pylint: disable=too-many-ancestors

class GuiBase(object):
    '''Base class for Gui frames containing defaults and parameters.
    '''
    def __init__(self, scan_param=None):
        '''Principle Scan parameters
        '''
        if not scan_param:
            scan_param = DirScanParameters()
        self.data = scan_param


class GuiFrameBase(tk.Frame, GuiBase):
    '''Base class for Gui frames containing defaults and parameters.
    '''
    def __init__(self, scan_param=None, owner_frame=tk.Tk(), **kwargs):
        '''initialize the TK frame and link it with the frame it is
        embedded in.
        '''
        self.update_master_frame(self, owner_frame)
        tk.Frame.__init__(owner_frame, **kwargs)
        DirGuiBase.__init__(scan_param)

    def update_master_frame(self, master_frame):
        ''' Update the calling TK frame.
        '''
        if issubclass(master_frame, tk.Tk):
            self.master_frame = master_frame
        else:
            raise TypeError('master_frame must be a TK widget or frame.\n\t'
                            'Got type %'%type(master_frame))

    def action_message(self, message_type=None, **kwargs):
        '''Generic message box
        message_type can be one of:
            'showinfo'  (default)
            'showwarning'
            'showerror'
            'askretrycancel'
        Parameter options are:
            title='This is a message box',
            message='This is the message',
            detail='Some more details',
        '''
        if not message_type:
            return messagebox.showinfo(parent=self, **kwargs)
        elif 'askretrycancel' in message_type:
            return messagebox.askretrycancel(parent=self, **kwargs)
        elif 'showerror' in message_type:
            return messagebox.showerror(parent=self, **kwargs)
        elif 'showwarning' in message_type:
            return messagebox.showwarning(parent=self, **kwargs)
        elif 'showinfo' in message_type:
            return messagebox.showinfo(parent=self, **kwargs)
        else:
            raise ValueError('message_type must be one of:\t\nshowinfo\t'
                             '(default)\n\t'
                             'showwarning\n\t'
                             'showerror\n\t'
                             'askretrycancel')

    def build(self, build_instructions):
        '''Configure the GUI frame and add sub-frames.
        This method may be overwritten for sub-classes.
        Parameter:
            build_instructions: Type list of length 3 tuples.
            Each tuple contains:
                (sub-GUI object, 'pack'|'grid', pack or grid keyword dict)
        '''
        for (subgui, method, kwargs) in build_instructions:
            if not kwargs:
                kwargs = {'fill': tk.X, 'padx': 10, 'pady': 5, 'side': tk.LEFT}
            subgui.pack(**kwargs)
        grid(column=1, row=1,pady=0, padx=0, sticky=tk.E)


class SelectFileParameters(ParametersBase):
    '''Contains all parameters required for selecting a file or directory.
    Class Attributes:
        action_types:
            Type: list of strings
            A list of valid action types
            Default = ['save', 'dir' 'open']
        action_types_str:
            Type: string
                A string defining all valid action types.
                Built from action_types
            Default = ['save', 'dir' 'open']
        valid_file_types
            Type: list of strings
            A list of valid file types
            Default = list of keys from FileTypes.file_types
        valid_types_str
            Type: string
                A string defining all valid file types.
                Built from valid_file_types
    Instance Attributes:
        heading
            Type: str
            The window title for the selection dialog.
            Default = ''
        file_types
            Type: str
            A string describing a directory or type of file to select.
            must reference an item in the FileTypes class
            Default = 'All Files'
        type_select
            Type: FileTypes
            Defined based on file_types value
            Default = None
        action
            Type: str
            A string indicating if the file is to be opened for reading or
            writing.
            One of 'save' or 'open'.
            Default = 'save'
        starting_path
            Type: Path
            The initial path, possibly including a default file name, for the
            file selection.
            Default = base_path
        initial_file_string
            Type: str
            The initial file name for the file selection.
            Default = None
        extension
            Type: str
            The initial extension for the file selection.
            Default = None

    The boolean option attribute:
        exist
            Indicates whether the selected file or directory must already
            exist.
            Default = False
        overwrite
            Indicates whether to silently overwrite existing files or send a
            warning message.
            Default = False
    Methods
        __init__
			Set attributes
			Verify that attributes are reasonable
        The following methods are used to check and update parameters
            update_update_heading(heading)
            update_file_types(file_types)
            update_action(action)
            update_starting_path(starting_path)
            update_initial_file_string(initial_file_string)
            update_extension(extension)
        The following methods set boolean options to True or False
            set_exist(exist)
            set_overwrite(overwrite)
    '''
    # Initialize class level parameters
    action_types = ['save', 'dir' 'open']
    action_types_str = '["' + '",\n\t"'.join(ft for ft in action_types) + '"]'
    valid_file_types = list(ft for ft in FileTypes.file_types)
    valid_file_types_str = '["' +\
        '",\n\t"'.join(ft for ft in valid_file_types) +\
        '"]'

    #The following method initializes parameters
    def __init__(self, base_path=None, **kwargs):
        '''
        Initialize all parameters, using default values if a value is
        not supplied
        '''
		# Initialize all parameters using default values
        super().__init__(base_path, **kwargs)
        self.heading = ''
        self.file_types = 'All Files'
        self.type_select = None
        self.action = 'save'
        self.starting_path = self.base_path
        self.initial_file_string = None
        self.extension = None

		# Initialize boolean option attributes, using default values
        exist = False
        overwrite = False

        # Set all passed parameter values
        self.update_parameters(base_path, **kwargs)

    #The following methods are used to check and update parameters
    def update_heading(self, heading):
        ''' Update the window title.
        '''
        try:
            self.heading = str(heading)
        except TypeError as err:
            raise err('heading must be a string.\n\t'
                      'Got type %'%type(heading))

        # If directory_path is a string treat it as a partial and
        # combine it with the base path, then check that the directory exits.
        if self.do_dir_scan:
            scan_path = self.valid_dir(self.insert_base_path(directory_path))
            self.directory_to_scan = scan_path

    def update_file_types(self, file_types):
        ''' Update the allowable file types to select from.
        '''
        if 'dir' in file_types:
            self.file_types = 'dir'
            self.type_select = None
        elif isinstance(file_types,str):
            if file_types in self.valid_file_types:
                self.file_types = [file_types]
                self.type_select = FileTypes(self.file_types)
            else:
                raise TypeError('file_types must be a string or '
                                'a list of strings with the following '
                                'values:\n\t' + self.valid_file_types_str)
        else:
            try:
                self.filetypes = list(file_types)
            except TypeError as err:
                raise err('file_types must be a string or a list of strings.'
                          '\n\tGot type %'%type(file_types))
            else:
                self.type_select = FileTypes(self.file_types)

    def update_action(self, action):
        ''' Update the type of file selection.
        '''
        if action in self.action_types:
            self.action = str(action)
        else:
            raise TypeError('action must be one of: \n\t' +
                            self.action_types_str)

    def update_starting_path(self, starting_path):
        ''' Update the starting file selection path.
        '''
        file_path = self.insert_base_path(starting_path)
        if file_path.is_file():
            self.starting_path = file_path.parent
            if not self.initial_file_string:
                self.initial_file_string = file_path.name
                self.extension = file_path.suffix
        elif self.valid_dir(file_path):
            self.starting_path = file_path
        else:
            raise TypeError('starting_path must type Path or type str.\n\t'
                            'Got type %'%type(starting_path))

    def update_initial_file_string(self, initial_file_string):
        ''' Update the default file name.
        '''
        try:
            self.initial_file_string = str(initial_file_string)
        except TypeError as err:
            raise err('initial_file_string must be a string.\n\t'
                      'Got type %'%type(initial_file_string))

        # If directory_path is a string treat it as a partial and
        # combine it with the base path, then check that the directory exits.
        if self.do_dir_scan:
            scan_path = self.valid_dir(self.insert_base_path(directory_path))
            self.directory_to_scan = scan_path



        # If directory_path is a string treat it as a partial and
        # combine it with the base path, then check that the directory exits.
        if self.do_dir_scan:
            scan_path = self.valid_dir(self.insert_base_path(directory_path))
            self.directory_to_scan = scan_path

    def update_extension(self, extension):
        ''' Update the default extension.
        '''
        try:
            self.extension = str(extension)
        except TypeError as err:
            raise err('extension must be a string.\n\t'
                      'Got type %'%type(extension))

    # The following methods set boolean options to True or False
    def set_exist(self, exist: bool):
        '''Indicate whether a directory or file should already exist.
        Parameter
            exist: Type bool
                True: Raise error if file does not exist.
                False: Do not check if the file exists.
        Raises
            TypeError
        '''
        try:
            self.exist = bool(exist)
        except TypeError as err:
            raise err('exist must be True or False')

    def set_overwrite(self, overwrite: bool):
        '''Indicate whether a file should be silently overwritten if it
        already exists.
        Parameter
            overwrite: Type bool
                True: Do not check if the file exists.
                False: Raise warning if the file exists.
        Raises
            TypeError
        '''
        try:
            self.overwrite = bool(overwrite)
        except TypeError as err:
            raise err('overwrite must be True or False')

