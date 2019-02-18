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
import tkinter as tk
import tkinter.filedialog as tkf
from file_utilities import FileTypes, get_file_path
from file_utilities import set_base_dir

FileTypeSelection = Union[List[str], FileTypes]
PathInput = Union[Path, str]


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
	    parent: {tk.Tk} -- The logical parent of the file dialog. The file
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
    Save File Selection Window
	    multiple: {bool} -- If True, Allows the user to choose multiple files
            from the Open dialog.
        '''
    all_dialogue_options = ('parent',
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
        parent=None, title='', initialdir=str(set_base_dir()),
        mustexist=False,
        initialfile=None, typevariable=None,
        confirmoverwrite=False, defaultextension=None)
    action_options = ('save', 'open', 'dir')

    def __init__(self, **kwargs):
        '''
        '''
        # Set defaults
        for attr, value in self.default_attributes.items():
            self.__setattr__(attr, value)
        reduced_kwargs = self.set_dialogue(**kwargs)
        reduced_kwargs = self.set_starting_path(reduced_kwargs)
        self.set_attributes(reduced_kwargs)
        self.set_options_list()

    def set_dialogue(self, type_selection: FileTypeSelection = None,
                     action='', **kwargs):
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
        return kwargs

    def set_starting_path(self, starting_path: PathInput = None,
                          initialfile: str = None,
                          defaultextension: str = None,
                          **kwargs)->Dict[str, Any]:
        '''Set the starting selection path and file name.
        Arguments:
            starting_path: {optional, PathInput} -- The initial path, possibly
                including a default file name, for the file selection.
                Default is the path returned by set_base_dir().
            initialfile: {optional, str} -- The initial file name for
                the file selection. Default = None.  Ignored if starting_path
                includes a file name.
            defaultextension: {optional, str} -- The initial file type to
                prompt for. Must reference a key in the FileTypes class.
                Ignored when selecting a directory. Default is first type in
                file_types.
            **kwargs: {Dict[str, Any]}: -- Additional keyword arguments to
                pass back.
        '''
        if starting_path is not None:
            initial_path = get_file_path(starting_path)
        else:
            initial_path = Path(self.initialdir)
        if initial_path.is_file():
            self.initialdir = str(initial_path.parent)
            self.initialfile = initial_path.name
        elif initialfile is not None:
            self.initialfile = initialfile
            self.initialdir = str(initial_path)
        else:
            self.initialdir = str(initial_path)

        if defaultextension:
            if self.filetypes.valid_extension(defaultextension):
                self.defaultextension = defaultextension
        return kwargs

    def set_attributes(self, kwargs: Dict[str, Any]):
        '''Set passed attributes using defined methods.
        '''
        for item in kwargs:
            if hasattr(self, 'set_' + item):
                set_method = getattr(self, 'set_' + item)
                set_method(kwargs[item])
            elif hasattr(self, item):
                self.__setattr__(item, kwargs[item])
        pass

    def get_options(self, option_list: Tuple[str])->Dict[str, Any]:
        '''Create a dictionary of options arguments.
        Arguments:
            option_list: {Tuple(str)} -- The list of option values to extract.
        Returns:
            A dictionary of the options and their values.
        '''
        options_set = {option: self.__getattribute__(option)
                       for option in option_list
                       if self.__getattribute__(option) is not None}
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

    def call_dialog(self, parent: tk.Tk = None):
        '''Open the appropriate dialog window and return the selected path.
        Arguments:
            parent: {tk.Tk} -- The logical parent of the file dialog.
        '''
        if parent:
            self.options_set['parent'] = parent
        if not self.options_set.get('parent'):
            root = tk.Tk()
            root.overrideredirect(1)            root.withdraw()
            self.options_set['parent'] = root
        selected_path = self.dialog(**self.options_set)        return selected_pathdef main():
    '''open test selection window.
    '''
    file_str = SelectFile().call_dialog()
    print(file_str)

if __name__ == '__main__':
    main()
