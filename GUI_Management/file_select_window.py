'''
Created on Aug 26 2017

@author: Greg Salomons
File Select Window
Functions and classes to allow for simple file or directory selection.

Classes
    SelectFileParameters:
        Primary GUI window
        sub class of TKinter.Frame

'''
from typing import Union, Callable, List, Dict, Tuple, Any
from pathlib import Path
from functools import partial
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as tkf
from tkinter import messagebox
from Utilities.file_utilities import FileTypes, get_file_path, make_full_path
from Utilities.file_utilities import set_base_dir, PathInput

FileTypeSelection = Union[List[str], FileTypes]
StringValue = Union[tk.StringVar, str]

class SelectFile():
    '''Contains all parameters required for selecting a file or directory.
    Attributes:
        action: {optional, str} -- Indicates if the file is to be opened for
            reading or writing.  One of 'save', 'open' or 'dir'.
            Default is 'save'.  Ignored when selecting a directory.
        type_selection: {FileTypeSelection, optional} -- The desired types of
            files to be selected from, or an instance of FileTypes generated
            from such a list. If type_selection contains "directory" a
            directory will
        starting_path: {optional, PathInput} -- The initial path, possibly
                including a default file name, for the file selection.
                Default is the path returned by set_base_dir().
        check_validity: {optional, bool} -- Whether to check the validity of
            the selected file or directory. Default is False.
    All Windows:
        title: {str} -- The window title for the selection dialog.
            Default = ''
        initialdir: {optional, PathInput} -- The initial path, possibly
            including a default file name, for the file selection.
            Default is the path returned by set_base_dir().
        master: {tk.Tk} -- The logical parent of the file dialog. The file
            dialog is displayed on top of its parent window.
    Directory Window:
        mustexist: {bool} -- Specifies whether the user may specify
            non-existent directories. If this parameter is true, then the
            user may only select directories that already exist. Default is
            False.
    All File Selection Windows
        initialfile: {optional, str} -- The initial file name for the
            file selection. Default = None.  Ignored if starting_path includes
            a file name.
        typevariable: {tk.StringVar} -- The TK string variable used to
            preselect which file type filter is used when the dialog box is
            opened and is updated when the dialog box is closed, to the last
            selected filter. The variable is read once at the beginning to
            select the appropriate filter. If the variable does not exist, or
            its value does not match any filter typename, or is empty ({}),
            the dialog box will revert to the default behavior of selecting
            the first filter in the list. If the dialog is canceled, the
            variable is not modified.
    Save File Selection Window
        defaultextension: {optional, str} -- The initial file type to
            prompt for. Must reference an extension in filetypes.
        confirmoverwrite: {bool} -- A true value requests a confirmation
            dialog be presented to the user when the selected file already
            exists. A false value ignores existing files. Default is False.
    Open File Selection Window
        multiple: {bool} -- If True, Allows the user to choose multiple files
            from the Open dialog.
        '''
    all_dialogue_options = ('master',
                            'title',
                            'initialdir')
    dir_dialogue_options = all_dialogue_options + ('mustexist',)
    file_dialogue_options = all_dialogue_options + ('initialfile',
                                                    'filetypes',
                                                    'typevariable')
    save_dialogue_options = file_dialogue_options + ('confirmoverwrite',
                                                     'defaultextension')
    open_dialogue_options = file_dialogue_options + ('multiple',)
    initialdir=None
    default_attributes = dict(
        action='save', filetypes=FileTypes(), check_validity=False,
        master=None, title='', initialdir=str(set_base_dir()),
        mustexist=False, initialfile=None, typevariable=None,
        confirmoverwrite=False, defaultextension=None)
    action_options = ('save', 'open', 'dir')

    def __init__(self, **file_params):
        '''
        '''
        # Set defaults
        for attr, value in self.default_attributes.items():
            self.__setattr__(attr, value)
        self.configure(**file_params)

    def set_dialogue(self, type_selection: FileTypeSelection = None,
                     action='', **reduced_file_params):
        '''Set the file dialog method to use.
        Select between:
            "asksaveasfilename",
            "askopenfilename", and
            "askdirectory"
        based on action and file_types.  Also set action and file_types
        attributes.
        Arguments:
            type_selection: {FileTypeSelection, optional} -- A list of the
                desired file types to be selected from, or an instance of
                FileTypes generated from such a list. If not supplied no file
                type filtering will be done. If 'directory', A directory will
                be selected.
            action: {str, optional} -- Indicates if the file is to be opened
                for reading or writing.  One of 'save', 'open' or 'dir'.
                Default is 'save'. If file_types is a directory, action will
                be ignored.
            **kwargs: {Dict[str, Any]}: -- Additional keyword arguments to
                pass back.
        '''
        if isinstance(type_selection, FileTypes):
            self.filetypes = type_selection
        elif type_selection is None:
            self.filetypes = FileTypes()
        else:
            self.filetypes = FileTypes(type_selection)

        # Set the action selector
        if any(option in action for option in self.action_options):
            self.action = action  # otherwise use default action

        # Select dialog
        if self.filetypes.is_dir:
            self.dialog = tkf.askdirectory
            self.action = 'dir'
        elif 'dir' in self.action:
            self.filetypes = FileTypes('directory')
            self.dialog = tkf.askdirectory
        elif 'open' in self.action:
            self.dialog = tkf.askopenfilename
        elif 'save' in self.action:
            self.dialog = tkf.asksaveasfilename
        return reduced_file_params

    def set_starting_path(self, starting_path: PathInput = None,
                          initialfile: str = None,
                          defaultextension: str = None,
                          **attr_dict)->Dict[str, Any]:
        '''Set the starting selection path and file name.
        Arguments:
            starting_path: {optional, PathInput} -- The initial path, possibly
                including a default file name, for the file selection.
                Default is the path returned by set_base_dir().
            initialfile: {optional, str} -- The initial file name for
                the file selection. Default = None.  Ignored if starting_path
                includes a file name.
            defaultextension: {optional, str} -- The initial file type to
                prompt for. Must reference an extension in filetypes. Default
                is first type in filetypes.
            **kwargs: {Dict[str, Any]}: -- Additional keyword arguments to
                pass back.
        '''
        if starting_path is not None:
            initial_path = get_file_path(starting_path)
        else:
            initial_path = Path(self.initialdir)
        if initial_path.is_file():
            self.initialdir = str(initial_path.master)
            self.initialfile = initial_path.name
        elif initialfile is not None:
            self.initialfile = initialfile
            self.initialdir = str(initial_path)
        else:
            self.initialdir = str(initial_path)

        if defaultextension:
            if self.filetypes.valid_extension(defaultextension):
                self.defaultextension = defaultextension
        return attr_dict

    def set_attributes(self, attr_dict: Dict[str, Any])->Dict[str, Any]:
        '''Set passed attributes using defined methods.
        Searches through attr_dict for keys that have corresponding methods
        named set_keyname or attributes called keyname.
        Returns a dictionary containing all items that did not match a method
        or attribute.
        '''
        unused_parameters = dict()
        for item, value in attr_dict.items():
            if hasattr(self, 'set_' + item):
                set_method = getattr(self, 'set_' + item)
                set_method(value)
            elif hasattr(self, item):
                self.__setattr__(item, value)
            else:
                unused_parameters[item] = value
        return unused_parameters

    def get_options(self, option_list: Tuple[str])->Dict[str, Any]:
        '''Create a dictionary of options arguments.
        Arguments:
            option_list: {Tuple(str)} -- The list of option values to extract.
        Returns:
            A dictionary of the options and their values.
        '''
        options_set = {option: self.__getattribute__(option)
                       for option in option_list
                       if hasattr(self, option)}
        # Convert master to parent for dialog options
        master = options_set.pop('master', None)
        if master:
            options_set['parent'] = master
        return options_set

    def set_options_list(self):
        '''Set the option parameters to pass to the dialog.
        '''
        if 'dir' in self.action:
            self.options_set = self.get_options(self.dir_dialogue_options)
        elif 'save' in self.action:
            self.options_set = self.get_options(self.save_dialogue_options)
        else:
            self.options_set = self.get_options(self.open_dialogue_options)
        pass

    def configure(self, **file_params)->Dict[str, Any]:
        '''Set the definition of the dialog window.
        Extract all supplied attributes and combine with defaults for
        attributes not supplied to define the dialog window functionality.
        Returns all supplied keyword arguments not used in defining the
        dialog window.
        '''
        reduced_file_params = self.set_dialogue(**file_params)
        attr_dict = self.set_starting_path(**reduced_file_params)
        unused_parameters = self.set_attributes(attr_dict)
        self.set_options_list()
        return unused_parameters

    def call_dialog(self, master: tk.Tk = None)->str:
        '''Open the appropriate dialog window and return the selected path.
        Arguments:
            master: {tk.Tk} -- The logical master of the file dialog.
        '''
        if master:
            self.options_set['parent'] = master
        if not self.options_set.get('parent'):
            root = tk.Tk()
            root.overrideredirect(1)
            root.withdraw()
            self.options_set['parent'] = root
        selected_path = self.dialog(**self.options_set)
        return selected_path

    def get_path(self, master: tk.Tk = None)->Path:
        '''Open the appropriate dialog window and return the selected path.
        Arguments:
            master: {tk.Tk} -- The logical parent of the file dialog.
        Returns: (Path}
            The selected path as type Path, with the requested checking
        '''
        # TODO add existence checking
        path_str = self.call_dialog(master)
        return make_full_path(path_str, self.filetypes)


class FileSelectGUI(ttk.LabelFrame):
    entry_layout=dict(layout_method='grid', padx=10, pady=10, row=0, column=0)
    button_layout=dict(layout_method='grid', padx=10, pady=10, row=0, column=1)

    def __init__(self, master: tk.Tk, **options):
        super().__init__(master=master)
        self.browse_window = SelectFile(master=master)
        self.file_entry = ttk.Entry(master=self)
        self.browse_button = ttk.Button(text='Browse', master=self)

    def config(self, **options):
        reduced_options = self.entry_config(**options)
        reduced_options = self.browse_window.configure(**reduced_options)
        reduced_options = self.button_config(**reduced_options)
        super().config(**reduced_options)

    def entry_config(self, path_variable: tk.StringVar = None,
                     **options)->Dict[str, Any]:
        option_prefix = 'entry_'
        if not path_variable:
            path_variable = tk.StringVar()
        self.path_variable = path_variable
        entry_options = dict(textvariable=path_variable)
        unused_parameters = dict()
        for option_name, value in options.items():
            if option_name.startswith(option_prefix):
                option = option_name[len(option_prefix):]
                entry_options[option] = value
            else:
                unused_parameters[option_name] = value
        self.file_entry.configure(**entry_options)
        return unused_parameters

    def browse_command(self):
        '''Command for Browse Buttons.'''
        self.path_variable.set(self.browse_window.call_dialog())

    def button_config(self, **options)->Dict[str, Any]:
        option_prefix = 'button_'
        browse_command = self.browse_command
        browse_options = dict(text='Browse', width=10, command=browse_command)
        unused_parameters = dict()
        for option_name, value in options.items():
            if option_name.startswith(option_prefix):
                option = option_name[len(option_prefix):]
                browse_options[option] = value
            else:
                unused_parameters[option_name] = value
        self.browse_button.configure(**browse_options)
        return unused_parameters

    def build(self, **build_instructions):
        reduced_instructions = self.build_entry(**build_instructions)
        unused_parameters = self.build_button(**reduced_instructions)
        self.columnconfigure(0, weight=1)
        layout_method = unused_parameters.pop('layout_method', None)
        if 'pack' in layout_method:
            self.pack(**unused_parameters)
        else:
            self.grid(**unused_parameters)

    def build_entry(self, **build_instructions):
        option_prefix = 'entry_'
        entry_layout = self.entry_layout.copy()
        unused_parameters = dict()
        for option_name, value in build_instructions.items():
            if option_name.startswith(option_prefix):
                option = option_name[len(option_prefix):]
                entry_layout[option] = value
            else:
                unused_parameters[option_name] = value
        layout_method = entry_layout.pop('layout_method', None)
        if 'pack' in layout_method:
            self.file_entry.pack(**entry_layout)
        else:
            self.file_entry.grid(**entry_layout)
        return unused_parameters

    def build_button(self, **build_instructions):
        option_prefix = 'button_'
        button_layout = self.button_layout.copy()
        unused_parameters = dict()
        for option_name, value in build_instructions.items():
            if option_name.startswith(option_prefix):
                option = option_name[len(option_prefix):]
                button_layout[option] = value
            else:
                unused_parameters[option_name] = value
        layout_method = button_layout.pop('layout_method', None)
        if 'pack' in layout_method:
            self.browse_button.pack(**button_layout)
        else:
            self.browse_button.grid(**button_layout)
        return unused_parameters

    def get(self):
        return self.path_variable.get()

    def set(self, file_path: PathInput):
        return self.path_variable.set(str(file_path))


def message_window(parent_window: tk.Widget, window_text: StringValue = '',
                   variable: StringValue = 'Nothing to say'):
    '''Display the sting message or variable content.'''
    if isinstance(variable, tk.StringVar):
        str_message = variable.get()
    else:
        str_message = str(variable)
    messagebox.showinfo(title=window_text, message=variable.get(),
                        parent=parent_window)

def main():
    '''open test selection window.
    '''
    file_str = SelectFile().call_dialog()
    print(file_str)

if __name__ == '__main__':
    main()
