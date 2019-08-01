'''
Created on Aug 26 2017

@author: Greg Salomons
GUI interface for DirScan.

Classes
    DirGui:
        Primary GUI window
        sub class of TKinter.Frame

'''

import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from functools import partial

from dir_scan_parameters import ParameterError
from dir_scan_parameters import ParameterWarning
from dir_scan_parameters import DirScanParameters


class DirGuiFrameBase(tk.Frame):
    '''Base class for DirGui frames containing defaults and parameters.
    '''
    def __init__(self, scan_param=None, master_frame=None, **kwargs):
        '''initialize the TK frame and link it with the frame it is
        embedded in.
        '''
        if not scan_param:
            scan_param = DirScanParameters()
        self.data = scan_param
        self.update_master_frame(master_frame)
        self.build_instructions = list()
        self.child_frames = list()
        super().__init__(self.master_frame, **kwargs)

    def update_master_frame(self, master_frame):
        ''' Update the calling TK frame.
        '''
        if not master_frame:
            self.master_frame = tk.Tk()
        elif hasattr(master_frame, 'tk'):
            self.master_frame = master_frame
        else:
            err_msg = 'master_frame must be a TK widget or frame.'
            '\n\t Got type {}'
            raise TypeError(err_msg.format(type(master_frame)))

    def add_build_instruction(self, subgui, build_method='pack', kwargs: dict=None):
        '''A build instruction is a length 3 tuple:
            subgui: a TK.frame or widget object,
            build_method: One of 'pack' or 'grid',
            kwargs: keyword dict with 'pack' or 'grid' parameters.
        '''
        self.child_frames.append(subgui)
        if not kwargs and 'pack' in build_method:
            kwargs = {'fill': tk.X, 'side': tk.LEFT, 'padx': 10, 'pady': 5}
        instruction = (subgui, build_method, kwargs)
        self.build_instructions.append(instruction)

    def get_data(self):
        '''Initialize all child frames.
        '''
        for child in child_frames:
            if hasattr(child, get_data):
                child.get_data()

    def refresh(self):
        '''Update all child frames.
        '''
        for child in child_frames:
            if hasattr(child, refresh):
                child.refresh()

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
            message = messagebox.showinfo(parent=self, **kwargs)
        elif 'askretrycancel' in message_type:
            message = messagebox.askretrycancel(parent=self, **kwargs)
        elif 'showerror' in message_type:
            message = messagebox.showerror(parent=self, **kwargs)
        elif 'showwarning' in message_type:
            message = messagebox.showwarning(parent=self, **kwargs)
        elif 'showinfo' in message_type:
            message = messagebox.showinfo(parent=self, **kwargs)
        else:
            raise ValueError('message_type must be one of:\t\nshowinfo\t'
                             '(default)\n\t'
                             'showwarning\n\t'
                             'showerror\n\t'
                             'askretrycancel')
        return message

    def build(self):
        '''Configure the GUI frame and add sub-frames.
        This method may be overwritten for sub-classes.
        Parameter:
            build_instructions: Type list of length 3 tuples.
            Each tuple contains:
                (sub-GUI object, 'pack'|'grid', pack or grid keyword dict)
        '''
        if self.build_instructions:
            for (subgui, method, kwargs) in self.build_instructions:
                try:
                    build_method = subgui.__getattribute__(method)
                except AttributeError as err:
                    raise err('{} is not a valid method of {}'.format(
                        str(method),str(subgui)))
                build_method(**kwargs)


class DirGuiElementFrame(DirGuiFrameBase):
    '''DirGui Base class for selecting or changing a specific
    DirScanParameters element.
    '''
    # TK variable types to link with parameter values
    var_type_dict = {
        'string': tk.StringVar,
        'int': tk.IntVar
        }

    def __init__(self, parameter_name=None, var_type='string', **kwargs):
        '''Build a frame and link the access variable to a specific parameter.
        '''
        super().__init__(**kwargs)
        var_select = self.var_type_dict[var_type]
        self.select_var = var_select()
        self.parameter = parameter_name

    def set(self, select_value):
        '''Set the frame variable.
        '''
        self.select_var.set(select_value)

    def get(self):
        '''Get the frame variable.
        '''
        return self.select_var.get()

    def refresh(self):
        '''Initialize the Gui variable from the initial scan_param values.
        '''
        value = self.data.__getattribute__(self.parameter)
        self.set(value)

    def get_data(self):
        '''Update the scan_param data element from the Gui variable.
        '''
        param = {self.parameter: self.get()}
        try:
            self.data.update_parameters(**param)
        except ParameterError as err:
            self.action_message('showerror', title=type(err), message=err)
        except ParameterWarning as err:
            self.action_message('showwarning', title=type(err), message=err)

    def build(self, build_instructions=None):
        '''Configure the GUI frame and add sub-frames.
        This method may be overwritten for sub-classes.
        Parameter:
            build_instructions: Type list of length 3 tuples.
            Each tuple contains:
                (sub-GUI object, 'pack'|'grid', pack or grid keyword dict)
        '''
        self.refresh()
        super().build()


class StatusTextFrame(DirGuiElementFrame):
    '''GUI frame for indicating current status of the Actions.
    '''
    def __init__(self, **kwargs):
        kwargs.update({'parameter_name': 'status'})
        super().__init__(**kwargs)
        status_box = tk.Label(self, textvariable=self.select_var)
        self.add_build_instruction(status_box)
        self.build()


class ActionButtonsFrame(DirGuiElementFrame):
    '''GUI frame containing a single button.
    '''
    def __init__(self, button_text='', action_method=None, **kwargs):
        kwargs.update({'parameter_name': 'action_text'})
        super().__init__(**kwargs)
        action_button = tk.Button(self, text=button_text, command=action_method)
        #action_button = tk.Button(self, textvariable=self.select_var)
        self.add_build_instruction(action_button)
        self.build()


class TestFrame(DirGuiFrameBase):
    '''GUI frame for indicating current status of the Actions.
    '''
    def __init__(self, frame_label='', master_frame=None, **kwargs):
        super().__init__(master_frame=master_frame, **kwargs)
        labeled_frame = tk.LabelFrame(self, text=frame_label)
        status_box = StatusTextFrame(master_frame=labeled_frame, **kwargs)

        def update_label(widget=status_box, text='changed'):
            widget.set(text)

        test_button = ActionButtonsFrame(master_frame=labeled_frame,
                                         button_text='try me',
                                         action_method=update_label)
        warning_button = ActionButtonsFrame(master_frame=labeled_frame,
                                         button_text='warning',
                                         action_method=self.show_warning)
        self.add_build_instruction(status_box)
        self.add_build_instruction(test_button)
        self.add_build_instruction(warning_button)
        self.add_build_instruction(labeled_frame)
        self.build()

    def show_warning(self, message_type='showwarning',
                        title='test warning',
                        message='test warning message'):
        self.action_message('showwarning', title=title, message=message)


class DirGui(DirGuiFrameBase):
    '''TKinter GUI class used for the DIR Scan program main GUI.
    '''
    def __init__(self, scan_param=None, **kwargs):
        '''Create the DIR Scan GUI and set the initial parameters
        '''
        super().__init__(scan_param, **kwargs)
        #status = StatusTextFrame(scan_param=scan_param, master_frame=self)
        status = TestFrame(scan_param=scan_param, master_frame=self,
                           frame_label='test label')
        self.add_build_instruction(status, 'grid',
                                   {'column': 1, 'row': 2, 'columnspan': 3,
                                    'padx': 10, 'sticky': tk.W})
        self.add_build_instruction(self)
        self.window_format()
        self.build()

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

    def activate(self):
        self.master_frame.mainloop()


def main():
    '''Test the activate_gui function call.
    '''
    def param_string(scan_param: DirScanParameters):
        '''Display the parameters in a pop-up message a test function.
        '''
        prams_to_display = [
            ('base_path = ', 'base_path'),
            ('directory to scan = ', 'directory_to_scan'),
            ('file to parse = ', 'file_to_scan'),
            ('Scan a directory = ', 'do_dir_scan'),
            ('Parse dir data = ', 'parse_dir_data'),
            ('File to save directory scan = ', 'directory_scan_output'),
            ('Save scan output = ', 'save_scan_output'),
            ('File-data output file = ', 'file_data_output'),
            ('Save file data = ', 'output_file_data'),
            ('Dir-data output file = ', 'dir_data_output'),
            ('Save dir data = ', 'output_dir_data')
            ]
        param_text = 'Scan Parameters'
        for (text_str, parameter) in prams_to_display:
            value = scan_param.__getattribute__(parameter)
            param_text += '\n' + text_str + str(value)
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
        dir_data_output='Test_dir_data.csv',
        status='Test of GUI')

    action_param = dict(
        action_methods={
            'Test_Action': partial(test_message, test_scan_param),
            'Exit': tk._exit
            },
        action_sequences={
            'Test_Action': ('Test_Action',),
            'Exit': ('Exit',)
            }
        )

    #dir_gui = DirGui(scan_param=test_scan_param)
    #dir_gui.activate()

    test_message(test_scan_param)

if __name__ == '__main__':
    main()

