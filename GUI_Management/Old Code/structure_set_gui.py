'''
Created on Aug 26 2017

@author: Greg Salomons
GUI interface for DirScan.

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
##




class DirGuiElementFrame(DirGuiBase):
    '''DirGui Base class for selecting or changing a specific
    DirScanParameters element.
    '''
    # TK variable types to link with parameter values
    var_type_dict = {
        'string': tk.StringVar,
        'int': tk.IntVar
        }

    def __init__(self, parameter_name='base_path', var_type='string',
                 scan_param=DirScanParameters(), **kwargs):
        '''Build a frame and link the access variable to a specific parameter.
        '''
        super().__init__(**kwargs)
        var_select = self.var_type_dict[var_type]
        self.select_var = var_select()
        self.parameter = parameter_name

    def set(self, select_value: str):
        '''Set the path_string frame variable.
        '''
        self.select_var.set(select_value)

    def get(self):
        '''Get the path_string frame variable.
        '''
        return self.select_var.get()

    def initialize(self):
        '''Initialize the Gui variable from the initial DirScanParameters values.
        '''
        value = self.data.__getattribute__(self.parameter)
        self.set(value)

    def update(self):
        '''Update the DirScanParameters data element from the Gui variable.
        '''
        param = {self.parameter: self.get()}
        self.data.update_parameters(self.empty_label.get())

    def build(self, **kwargs):
        '''Configure the GUI frame and add sub-frames.
        This method is to be overwritten for each sub-class.
        '''
        self.initialize()
        super().build(self, **kwargs)


class DirGuiLabelFrame(DirGuiBase, tk.LabelFrame):
    '''DirGui Base class for grouping one or more DirGuiElementFrames
    together within a labeled frame.
    '''
    def __init__(self, form_title=None, **kwargs):
        '''Build the frame and define the access variable
        '''
        super().__init__(owner_frame, text=form_title, **kwargs)

    def build(self, **kwargs):
        '''Configure the GUI frame and add sub-frames.
        This method is to be overwritten for each sub-class.
        '''
        self.initialize()
        super().build(self, **kwargs)



class FileSelectGui(DirGuiElementFrame, SelectFileParameters):
    '''GUI frame for selecting a file or directory.
    sub class of TKinter.LabelFrame.
    used inside the InputPathsFrame and OutputPathsFrame.
    '''
    def select_file_dialog(self):
        '''Open a dialog to select a file or directory.
        Returns the selected file or directory
        '''
        starting_path = self.starting_path
        if self.action is 'save':
            select_method = tkf.asksaveasfilename
        else:
            select_method = tkf.askopenfilename
        if 'dir' in self.file_types:
            selected_file_string = \
                tkf.askdirectory(parent=self.master_frame,
                                 title=file_parameters.heading,
                                 mustexist=file_parameters.exist,
                                 initialdir=file_parameters.starting_path)
        else:
            extension = file_parameters.extension
            if not extension:
               extension = '.txt'
            selected_file_string = select_method(
                parent=file_parameters.master_frame,
                title=file_parameters.heading,
                initialdir=file_parameters.starting_path,
                initialfile=file_parameters.initial_file_string,
                defaultextension=extension,
                filetypes=file_parameters.type_select)
        # ToDo Move confirm overwrite to parameters driven method
        # confirmoverwrite=exist,
        return selected_file_string

        def build(self, select_cmd):
            file_show = tk.Entry(self, textvariable=self.select_var, width=100)
            select_file = tk.Button(self, text='Browse', command=select_cmd)
            file_show.pack(fill=tk.X, padx=10, pady=5, side=tk.LEFT)
            select_file.pack(padx=5, pady=5, side=tk.RIGHT)
        #if selected_file_string is not '':
        #    try:
        #        file_select = Path(selected_file_string)
        #        file_parem_set(file_select)
        #    except (TypeError, FileTypeError) as err:
        #        #TODO add warning to status
        #        print("OS error: {0}".format(err))
        #    else:
        #        master_frame.set(selected_file_string)


class InputSelectFrame(DirGuiSubFrame):
    '''GUI frame for selecting whether to scan a directory or parse a file.
    used inside the InputPathsFrame.
    '''
    def build(self):
        '''Build the frame to select a file or directory.
        Add the form to select a directory to scan.
        '''
        choose_dir = tk.Radiobutton(self, text="", variable=self.select_var, value=0)
        choose_file = tk.Radiobutton(self, text="",variable=self.select_var, value=1)
        choose_dir.grid(column=1, row=1,pady=0, padx=0, sticky=tk.E)
        choose_file.grid(column=1, row=2,pady=0, padx=0, sticky=tk.E)


class InputPathsFrame(DirGuiFrame):
    '''GUI frame for selecting the file or directory path to scan or parse.
    used inside the main GUI.
    '''
    def get_input_option(self,choose_widget):
        '''Set a radial button widget variable to the current input option
        from parameters as an integer.
            0   Scan a directory
            1   Parse a file.
        '''
        if self.data.do_dir_scan:
            choose_widget.set(0)
        else:
            choose_widget.set(1)

    def set_input_option(self, input_select):
        '''Update the parameter flag to indicate whether to scan a directory
        or parse a file.
        '''
        if input_select == 0:
            self.data.update_do_dir_scan(True)
        else:
            self.data.update_do_dir_scan(False)


    def set_choice(self, value, choose_widget, event):
        '''Update the radial button widget variable and the parameter flag to
        indicate whether to scan a directory or parse a file.
        The event parameter is from the binding and is not used.
        '''
        self.set_input_option(value)
        choose_widget.set(value)

    def build(self):
        '''Build the frame to select a file or directory.
        Add the form to select either a directory to scan or a file to parse.
        '''
        # Add the select buttons
        select_source_header = 'Select the directory to scan or file to parse.'
        choose_source = InputSelectFrame(self, select_source_header, 'int')
        choose_source.build()
        choose_source.grid(column=1, row=1, rowspan=2, pady=3, padx=0,
                           sticky=tk.E)
        self.get_input_option(choose_source)
        self.choose_source = choose_source

        # Add the directory selection
        select_dir_header = 'Select the directory to scan.'
        select_dir = FileSelectGui(choose_source, select_dir_header)
        if self.data.directory_to_scan:
            select_dir.set(str(self.data.directory_to_scan))
        dir_select_dialog = partial(
            select_file_dialog,
            master_frame=select_dir,
            heading=select_dir_header,
            file_parem_set=self.data.update_directory_to_scan,
            filetypes='dir',
            exist=True)
        select_dir.build(dir_select_dialog)
        select_dir.grid(column=2, row=1, columnspan=2,
                        pady=3, padx=0, sticky=tk.W)
        choose_dir = partial(self.set_choice, 0, choose_source)
        select_dir.bind('<FocusIn>', choose_dir)
        self.select_dir = select_dir

        # Add the file source selection
        select_file_header = 'Select the file to parse.'
        select_file = FileSelectGui(choose_source, select_file_header)
        if self.data.file_to_scan:
            select_file.set(str(self.data.file_to_scan))
        file_select_dialog = partial(
            select_file_dialog,
            master_frame=select_file,
            heading=select_file_header,
            file_parem_set=self.data.update_file_to_scan,
            filetypes='Text File',
            action='open',
            exist=True)
        select_file.build(file_select_dialog)
        select_file.grid(column=2, row=2, columnspan=2,
                         pady=3, padx=0, sticky=tk.W)
        choose_file = partial(self.set_choice, 1, choose_source)
        select_file.bind('<FocusIn>', choose_file)
        self.select_file = select_file


    def update(self):
        '''Update all data values from the GUI sub-frames.
        '''
        self.data.update_directory_to_scan(self.select_dir.get())
        self.data.update_file_to_scan(self.select_file.get())
        self.set_input_option(self.choose_source.select_var.get())


class OutputFileSelectGui(DirGuiSubFrame):
    '''GUI frame for selecting the file or directory path to scan or parse.
    used inside the main GUI.
    '''
    def __init__(self, owner_frame, header=None, var_type='string'):
        '''Build the frame and define the select and file path variable.
        '''
        super().__init__(owner_frame, form_title=header)
        self.use_file = tk.IntVar()

    def set_choice(self, value, event=None):
        '''Update the check box to indicate whether use the file.
        The event parameter is from the binding and is not used.
        '''
        self.use_file.set(int(value))

    def get_choice(self, event=None):
        '''Return true or false if box selected.
        The event parameter is from the binding and is not used.
        '''
        return bool(self.use_file.get())

    def change_choice(self, event=None):
        '''Return true or false if box selected.
        The event parameter is from the binding and is not used.
        '''
        current_val = bool(self.use_file.get())
        flip = int(not(current_val))
        self.use_file.set(flip)

    def build(self, select_cmd):
        '''Build the frame to select an output file and usage Check Box.
        '''
        # Add the select button
        file_checkbox = tk.Checkbutton(self, text="", variable=self.use_file)
        file_checkbox.pack(pady=0, padx=0, side=tk.LEFT)
        # Add the directory selection
        file_show = tk.Entry(self, textvariable=self.select_var, width=100)
        select_file = tk.Button(self, text='Browse', command=select_cmd)
        file_show.pack(fill=tk.X, padx=10, pady=5, side=tk.LEFT)
        select_file.pack(padx=5, pady=5, side=tk.RIGHT)
        choose_file = partial(self.set_choice, 1)
        file_show.bind('<FocusIn>', choose_file)


class OutputPathsFrame(DirGuiFrame):
    '''GUI frame for selecting the files to store the output from
    Scan and Parse.
    used inside the main GUI.
    '''
    def build(self):
        '''Build the frame to select a file or directory.
        Add the form to select a directory to scan.
        '''
        # TODO add check that at least one output is selected in GUI
        # Add frame to select a file to save the DIR output
        scan_output_header = 'Select the file to save the DIR scan output'
        scan_output_select = OutputFileSelectGui(self, scan_output_header)
        scan_output_select.set(str(self.data.directory_scan_output))
        scan_output_select.set_choice(int(self.data.save_scan_output))
        scan_output_dialog = partial(
            select_file_dialog,
            master_frame=scan_output_select,
            heading=scan_output_header,
            file_parem_set=self.data.update_directory_scan_output,
            filetypes='Text File',
            action='save')
        scan_output_select.build(scan_output_dialog)
        scan_output_select.grid(column=1, row=1, columnspan=4,
                                pady=3, padx=10, sticky=tk.W)
        self.scan_output_file = scan_output_select
        # Add frame to select a file to save file data from the parse output
        file_data_header = 'Select the file to save the parsed file info.'
        file_data_select = OutputFileSelectGui(self, file_data_header)
        file_data_select.set(str(self.data.file_data_output))
        file_data_select.set_choice(int(self.data.output_file_data))
        file_data_dialog = partial(
            select_file_dialog,
            master_frame=file_data_select,
            heading=file_data_header,
            file_parem_set=self.data.update_file_data_output,
            filetypes=['Comma Separated Variable File', 'Excel Files'],
            action='save',
            extension='.csv')
        file_data_select.build(file_data_dialog)
        file_data_select.grid(column=1, row=2, columnspan=4,
                              pady=3, padx=10, sticky=tk.W)
        self.file_data_output = file_data_select
        # Add frame to select a file to save directory data from the parse output
        dir_data_header = 'Select the file to save the parsed directory info.'
        dir_data_select = OutputFileSelectGui(self, dir_data_header)
        dir_data_select.set(str(self.data.dir_data_output))
        dir_data_select.set_choice(int(self.data.output_dir_data))
        dir_data_dialog = partial(
            select_file_dialog,
            master_frame=dir_data_select,
            heading=dir_data_header,
            file_parem_set=self.data.update_dir_data_output,
            filetypes=['Comma Separated Variable File', 'Excel Files'],
            action='save',
            extension='.csv')
        dir_data_select.build(dir_data_dialog)
        dir_data_select.grid(column=1, row=3, columnspan=4,
                              pady=3, padx=10, sticky=tk.W)
        self.dir_data_output = dir_data_select

    def update(self):
        '''Update all data values from the GUI sub-frames.
        This method is to be overwritten for each sub-class.
        '''
        self.data.update_directory_scan_output(self.scan_output_file.get())
        self.data.update_file_data_output(self.file_data_output.get())
        self.data.update_dir_data_output(self.dir_data_output.get())
        self.data.update_save_scan_output(self.scan_output_file.get_choice())
        self.data.update_output_file_data(self.file_data_output.get_choice())
        self.data.update_output_dir_data(self.dir_data_output.get_choice())

class ActionButtonsFrame(DirGuiFrame):
    '''Add the buttons to start or cancel the scan.
    '''
    def build(self):
        '''Configure the GUI frame and add sub-frames.
        This method is to be overwritten for each sub-class.
        '''
        #self.status = 'Making Selections'
        action_label = self.data.action_text()
        run = self.master.run_method
        cancel = self.master.cancel_method
        self.run_button = tk.Button(self, text=action_label, command=run)
        self.cancel_button = tk.Button(self, text='Cancel', command=cancel)
        self.run_button.grid(column=1, row=1, padx=5)
        self.cancel_button.grid(column=2, row=1, padx=5)

    def update(self):
        '''Update all data values from the GUI sub-frames.
        This method is to be overwritten for each sub-class.
        '''
        action_label = self.data.action_text()
        self.run_button.config(text=action_label)

class StatusTextFrame(DirGuiFrame):
    '''GUI frame for indicating current status of the Actions.
    '''
    def build(self, initial_status='Enter Selections'):
        '''Build the frame to display the status.
        '''
        self.master.status_text.set(initial_status)
        status_box = tk.Label(self, textvariable=self.master.status_text)
        status_box.pack()


class DirGui(tk.Frame):
    '''TKinter GUI class used for the DIR Scan program main GUI.
    '''
    def __init__(self, scan_param: DirScanParameters, master, run_cmd):
        '''Create the DIR Scan GUI and set the initial parameters
        '''
        super().__init__(master)
        self.data = scan_param
        self.run_method = partial(self.update_and_run, run_cmd)
        self.cancel_method = master.destroy
        self.status_text = tk.StringVar()

    def window_format(self):
        '''Format and label main GUI window.
        Add a window title,
        Add a window icon,
        Add a header label
        '''
        root = self._root()
        root.title("Directory Scan")
        # Add a window icon
        ico_pict = r'.\Icon test.png'
        root.iconphoto(root, tk.PhotoImage(file=ico_pict))
        #Add Top header
        header = tk.Label(self, text='Directory Scan')
        header.config(font=('system', 20, 'bold'))
        header.grid(column=1, row=1, columnspan=3)

    def build(self):
        '''Configure the main GUI window and add sub-frames.
        '''

        self.window_format()
        input_select_frame = InputPathsFrame(self.data, self)
        input_select_frame.build()
        input_select_frame.grid(column=1, row=2, columnspan=3,
                                padx=10, sticky=tk.W)
        self.input_select = input_select_frame

        output_select_frame = OutputPathsFrame(self.data, self)
        output_select_frame.build()
        output_select_frame.grid(column=1, row=3, columnspan=3,
                                 padx=10, sticky=tk.W)
        self.output_select = output_select_frame

        action_buttons_frame = ActionButtonsFrame(self.data, self)
        action_buttons_frame.build()
        action_buttons_frame.grid(column=1, row=5, columnspan=3, pady=2)

        status_message_frame = StatusTextFrame(self.data, self)
        status_message_frame.build()
        status_message_frame.grid(column=1, row=6, columnspan=3,
                                  padx=10, sticky=tk.W)

    def update(self):
        '''Update all scan and parse parameters from the GUI frames.
        '''
        self.input_select.update()
        self.output_select.update()

    def update_and_run(self, run_cmd):
        '''Set all values for the scan parameters from the GUI.
        '''
        self.update()
        # Perhaps split up scan and parse commands
        run_cmd(self.data, self)


def activate_gui(scan_param: DirScanParameters, run_cmd):
    '''Activate the GUI and return the selected parameters.
    '''
    root = tk.Tk()
    dir_gui = DirGui(scan_param, root, run_cmd)
    dir_gui.build()
    dir_gui.pack()
    root.mainloop()
    return dir_gui


def main():
    '''Test the activate_gui function call.
    '''
    def param_string(scan_param: DirScanParameters):
        '''Display the parameters in a pop-up message a test function.
        '''
        param_dict = {
            'dir_command_switches': str(scan_param.dir_command_switches),
            'file_data_variables': str(scan_param.file_data_variables),
            'dir_summary_variables': str(scan_param.dir_summary_variables),
            'base_path': str(scan_param.base_path),
            'directory_to_scan': str(scan_param.directory_to_scan),
            'file_to_scan': str(scan_param.file_to_scan),
            'do_dir_scan': str(scan_param.do_dir_scan),
            'parse_dir_data': str(scan_param.parse_dir_data),
            'directory_scan_output': str(scan_param.directory_scan_output),
            'save_scan_output': str(scan_param.save_scan_output),
            'file_data_output': str(scan_param.file_data_output),
            'output_file_data': str(scan_param.output_file_data),
            'dir_data_output': str(scan_param.dir_data_output),
            'output_dir_data': str(scan_param.output_dir_data),
            'file_data_sheet': str(scan_param.file_data_sheet),
            'dir_data_sheet': str(scan_param.dir_data_sheet),
            'top_dir': str(scan_param.top_dir),
            'source': str(scan_param.source),
            'time_type': str(scan_param.time_type)
            }

        param_text = 'Scan Parameters'
        param_text += '\n' + 'base_path = {base_path}'
        param_text += '\n' + 'directory to scan = {directory_to_scan}'
        param_text += '\n' + 'file to parse = {file_to_scan}'
        param_text += '\n' + 'Scan a directory = {do_dir_scan}'
        param_text += '\n' + 'Parse dir data = {parse_dir_data}'
        param_text += '\n' + 'File to save directory scan = {directory_scan_output}'
        param_text += '\n' + 'Save scan output = {save_scan_output}'
        param_text += '\n' + 'File-data output file = {file_data_output}'
        param_text += '\n' + 'Save file data = {output_file_data}'
        param_text += '\n' + 'Dir-data output file = {dir_data_output}'
        param_text += '\n' + 'Save dir data = {output_dir_data}'

        param_text = param_text.format(**param_dict)
        return param_text

    def test_message(scan_param: DirScanParameters):
        '''Display a message box containing parameter info.
        '''
        message_text = param_string(scan_param)
        results = messagebox.showinfo(title='Parameters',
                                message=message_text)

    test_scan_param = DirScanParameters(\
        base_path=Path('.'),
        file_to_scan='Test_Files.txt',
        time_type="C",
        source='Test Files',
        top_dir=Path('.'),
        file_data_output='Test_files_data.csv',
        output_dir_data=False,
        dir_data_output='Test_dir_data.csv')
    #run_cmd = partial(test_message, test_scan_param)
    dir_gui = activate_gui(test_scan_param, test_message)

if __name__ == '__main__':
    main()
