'''
Created on Aug 11 2017

@author: Greg Salomons
Define parameters required for building Structure Templates.

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
    ParametersBase: Base class for parameter objects.
    template_selection:  Input parameters required for building Structure Templates.

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
# TODO Convert to VariableSet
from pathlib import Path
from typing import Dict, Union, List
import warnings
from file_utilities import FileTypes

# TODO Convert to Custom Variable Set
# TODO Add 	Show inactive variable

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

		
class GuiBase(object):
    '''Base class for Gui frames containing defaults and parameters.
    '''
    def __init__(self, scan_param=None):
        '''Principle Scan parameters
        '''
        if not scan_param:
            scan_param = DirScanParameters()
        self.data = scan_param


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


