'''
Created on Aug 26 2017

@author: Greg Salomons
GUI interface for DirScan.

Classes
    DirGui:
        Primary GUI window
        sub class of TKinter.Frame

'''
from functools import partial
from collections import OrderedDict, namedtuple
from pathlib import Path
from typing import Union, Callable, List, Dict, Tuple, Any
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from file_select_window import SelectFile
from file_utilities import FileTypes

Cmd = Union[Callable, str]
Var = Union[str, tk.DoubleVar, tk.IntVar, tk.StringVar]
Bol = Union[bool, str]
Dimension = Union[int, str]
Widget = Union[str, tk.Widget]
FileTypeSelection = Union[List[str], FileTypes]
PathInput = Union[Path, str]
MatchedData = namedtuple('MatchedData', ['data_link', 'updated_parameters'])
LinkMethod = namedtuple('LinkMethod', ['update_method', 'reference'])

# If you set a dimension to an integer, it is assumed to be in pixels.
# You can specify units by setting a dimension to a string containing a
# number followed by:
#   c	Centimeters
#   i	Inches
#   m	Millimeters
#   p	Printer's points (about 1/72″)


def show_message(msg: str, parent: tk.Tk):
    '''Simple Message Box'''
    messagebox.showinfo('Test message', msg, parent=parent)

class DataConfig():
    '''Class used to store parameters and configuration settings for the GUI.
    '''
    def __init__(self, *args, data=None, **kwargs):
        '''Principle Scan parameters
        '''
        if not data:
            data = dict()
        self.data = data
        super().__init__(*args, **kwargs)

    def get_command(self, command: Cmd)-> Callable:
        '''Return a callable action.
        If command is not callable assume it is a data reference and return
        the corresponding value.
        Arguments:
            command: {Cmd} -- either a single argument callable or a string
                referencing a single argument callable in data.
        '''
        if callable(command):
            return command
        return self.data[command]

    def get_tkvar(self, var: Var)-> Var:
        '''Return a tk variable.
        If var is not one of the tk variable types:
                tk.DoubleVar,
                tk.IntVar,
                tk.StringVar
            assume it is a data reference and return the corresponding value.
        Arguments:
            var: {Var} -- either a tk variable or a string referencing such a
                variable in data.
        '''
        if isinstance(var, (tk.DoubleVar, tk.IntVar, tk.StringVar)):
            return var
        return self.data[var]

    def get_widget(self, widget: Widget)-> Widget:
        '''Return a tk widget.
        If widget is not a placeable widget:
            assume it is a data reference and return the corresponding value.
        Arguments:
            widget: {Widget} -- either a tk placeable widget or a string
                referencing such a variable in data.
        '''
        if isinstance(widget, tk.Widget):
            return widget
        return self.data[widget]

    def get_str(self, text: str)-> str:
        '''Select a text string either as literal or a data reference.
        If text is a key in data, return the corresponding value.
        otherwise return str(Text).
        Arguments:
            text: {str} -- either literal string or a reference to an item in
                data.
        '''
        look_up_value = self.data.get(text)
        if look_up_value:
            return look_up_value
        return str(text)

    def get_bool(self, variable: Bol)-> bool:
        '''Return a boolean value.
        If variable is a data reference return the corresponding value,
        otherwise return variable as a boolean.
        Arguments:
            variable: {Bol} -- Either boolean or a reference to an item in
                data.
        '''
        look_up_value = self.data.get(variable)
        if look_up_value:
            return look_up_value
        return bool(variable)

    def get_path(self, path_name: PathInput)-> str:
        '''Return a file or directory path string
        Input, path_name can either be a literal path or a data reference.
        Arguments:
            path_name: {PathInput} -- either a reference to a path item in
                data or a literal path.
        Returns:
            The corresponding path as a string.
        '''
        look_up_value = self.data.get(path_name)
        if look_up_value:
            return str(look_up_value)
        return str(path_name)

    def get_file_types(self, type_selection: FileTypeSelection)-> FileTypes:
        '''Return a FileTypes object derived from the input value.
        Input, type_selection can either be a FileTypes object, a list of
        strings used to define a FileTypes object or a data reference to
        one of the above.
        Arguments:
            type_selection: {FileTypeSelection} -- either a FileTypes object,
                a list of strings used to define a FileTypes object, or a
                data reference to one of the above
        Returns:
            The FileTypes object derived from type_selection.
        '''
        look_up_value = self.data.get(type_selection)
        if look_up_value:
            file_types = look_up_value
        else:
            file_types = type_selection
        if isinstance(file_types, FileTypes):
            return file_types
        return FileTypes(file_types)

    def get_data(self, param_def: Dict[str, str],
                 parameters: Dict[str, Any])->Dict[str, Any]:
        '''Superceded by data_match'''
        # FIXME Replace with Data_match
        pass

    def data_match(self, param_def: Dict[str, str],
                 parameters: Dict[str, Any])->MatchedData:
        '''Return referenced Data values for all relevant parameters.
        For every key in parameters that corresponds to a key in param_def,
        replace the parameter value with the referenced Data value if
        applicable.
        Arguments:
            param_def: {Dict[str, str]} -- A dictionary containing the
                parameter name and corresponding data type name.
            parameters: {Dict[str, Any]} -- A shallow copy of parameters with
                referenced values from Data added.
        Returns: {MatchedData}
            A two element named tuple:
                data_link: {Dict[str, LinkMethod]} -- A dictionary with the
                    keys being parameter names and the value being two element
                    named tuple containing teh update_method callable and the
                    relevant data reference.
                updated_parameters: {Dict[str, Any]} -- A new dictionary
                    containing all parameters items with the new values.
        '''
        updated_parameters = dict()
        data_link = dict()
        for param, value in parameters.items():
            data_type = param_def.get(param)
            if data_type:
                method_name = 'get_' + data_type
                if hasattr(self, method_name):
                    update_method = getattr(self, method_name)
                    updated_value = update_method(value)
                    data_link[param] = LinkMethod(update_method, value)
                else:
                    updated_value = value
            else:
                updated_value = value
            updated_parameters[param] = updated_value
        return MatchedData(data_link, updated_parameters)

    def refresh(self):
        '''Set all variable values to their referenced data value.
        '''
        # FIXME Add refresh method
        pass 

    def update(self):
        '''Set all data values to their coresponding variable value.
        '''
        # FIXME Add update method
        pass 


class ManagerGUI(DataConfig, tk.Toplevel):
    '''Base class for Gui frames containing defaults and parameters.
    '''
    def __init__(self, root, shape=None, bg_color='light blue',
                 title='Test GUI', data=None):
        '''Defines the main window for the GUI
        '''
        self.widget_list = OrderedDict()
        self.variables = OrderedDict()        
        super().__init__(root, bg=bg_color, data=data)
        self.geometry(shape)
        self.title(title)
        # make sure main_gui is on top to start
        self.attributes("-topmost", 1)
        #self.attributes("-topmost", 0)

    def add_widget(self, widget_name: str, widget_instance: tk.Widget,
                   widget_type: str, widget_parent: tk.Tk):
        '''Add the suplied widget to the set of sub-widgets.        
        Arguments:
            widget_name {str} -- The unique name of the widget
            widget_instance {tk.Widget} -- [description]
            widget_type: {str} -- The type of widget.  One of:
                'Input' e.g. entry
                'Display' e.g. label
                'Control' e.g. button
                'Layout' e.g. frame
            parent: {tk.TK} -- The parent widget or frame.
        '''
        self.widget_list[widget_name] = {
            'instance': widget_instance,
            'type': widget_type,
            'parent': widget_parent}

    def add_variable(self, variable_name: str, data_name: str = None,
                     variable_instance: Var = None,
                     variable_type: str = None)->Var:
        '''Add a variable to the set of variables.
        If the variable is not provided, create it.    
        Arguments:
            variable_name {str} -- The unique name of the variable
            data_name {optional, str} -- The data reference to coresponding to
                the variable. update and refresh calls will synchronize the
                variable value and the referenced data value.
            variable_instance {optional, Var} -- A tk variable instance or a
                reference to one in data.
            variable_type {optional, str} -- the variable type. One of:
                "Double", "Int", "String"
        Returns:
            Var -- The variable instance
        '''
        if variable_instance:
            variable = self.data.get_tkvar(variable_instance)
        elif variable_type:
            if 'Double' in variable_type:
                variable = tk.DoubleVar
            elif 'Int' in variable_type:
                variable = tk.IntVar
            elif 'String' in variable_type:
                variable = tk.StringVar
            else:
                raise ValueError('Variable type not defined.')
        else:
            raise ValueError('No Variable Type supplied.')
        if variable_name in self.variables.keys():
            raise ValueError('Variable name arleady defined.')
        self.variables[variable_name] = {
            'instance': variable,
            'reference': data_name}
        return variable

    def build(self, build_instructions: dict):
        '''Constrict the top GUI window and add all sub-widgets.
        Arguments:
            build_instructions: {dict} -- Overides any pre-set geometry
                settings for a given widget.  The keys are the names of the
                widgets and the values are dictioanries containing the geometry overide 
        This method may be overwritten for sub-classes.
        Parameter:
            build_instructions: Type list of length 3 tuples.
            Each tuple contains:
                (sub-GUI object, 'pack'|'grid', pack or grid keyword dict)
        '''
        for (subgui, layout_method, kwargs) in build_instructions:
            if 'pack' in layout_method:
                if kwargs:
                    subgui.pack(**kwargs)
                else:
                    subgui.pack()
            elif 'grid' in layout_method:
                if kwargs:
                    subgui.grid(**kwargs)
                else:
                    subgui.grid()
        pass


class WidgetManager(tk.Widget):
    '''Define methods common to all WidgetManager classes.
    '''
    widget_type = ''
    default_geometry = {'ipadx': 5, 'ipady': 5, 'padx': 5, 'pady': 5}
    def __init__(self, name: str, manager: ManagerGUI, master: tk.Tk,
                 **widget_parameters):
        '''Create the widget instance and register it with the widget manager.
        Arguments:
            name: {str} -- The instance name of the widget.
            manager: {ManagerGUI} -- The top level GUI containing the
                configuration data.
            master: {tk.TK} -- The parent widget or frame.
        '''
        self.manager = manager
        self.name = name
        manager.add_widget(name, self, self.widget_type, master)
        self.set_geometry()
        super().__init__(master=master, **widget_parameters)

    def define(self, **widget_parameters):
        '''Configure information related to input/output or control
        Arguments:
            command: {str, callable} -- Either a function to be called when the
                button is pressed, or the name of the item in master.data
                containing the desired callable.
            text: {optional, str} -- The text to appear on the button.
            textvariable: {optional, tk.StringVar} -- A variable containing the
                text to appear on the button.
            image: {optional, tk.PhotoImage} -- An image to appear on the button.
    '''
        # FIXME add define method config???
        pass
        
    def set_geometry(self, **geometry):
        '''Set the parameters for the widget's placement in it's parent widget.
        Arguments:
            geometry: {dict} -- Contains items to be passed to the grid or
                pack method describing the padding around the widget and it's
                location in the parent widget.  Items are:
                    layout_method: {str} -- The placement method to use.
                        One of: 'pack' or 'grid'. Default is 'grid'.
                    ipadx: {Dimension} -- Internal x padding; padding added
                        inside the widget's left and right sides.
		            ipady: {Dimension} -- Internal y padding; padding added
                        inside the widget's top and bottom borders.
            		padx: {Dimension} -- External x padding; padding added
                        outside the widget's left and right sides.
		            pady: {Dimension} -- External y padding; padding added
                        above and below the widget.
                    width: {int} -- The absolute width of the text area
                        on the button, as a number of characters; the actual
                        width is that number multiplied by the average width
                        of a character in the current font.
            		column: {int} -- The column number where you want the
                        widget placed, counting from zero. The default value
                        is zero.
            		columnspan: {int} -- The number of vertical cells the
                        widget should occupy.
            		row: {int} -- The row number where you want the widget
                        placed, counting from zero. The default is the next
                        higher-numbered unoccupied row.
            		rowspan: {int} -- The number of horizontal cells the
                        widget should occupy.
                    sticky: {str} -- How to position the widget within the
                        cell. Can contain any combination of:
                            ('n', 's', 'e', 'w',)
                        If 'ns' or 'ew' are used together the widget will
                        stretch horizontally or vertically to fill the cell.
        '''
        self.geometry = self.default_geometry
        if geometry:
            width = geometry.pop('width', None)
            if width:
                self.configure(width=width)
        self.geometry.update(geometry)

    def set_appearance(self, **appearance):
        '''Set the parameters for the widget's padding.
        Arguments:
            appearance: {dict} -- Contains items describing the appearance of
                the widget.  Items are:
		            style: {ttk.Style} -- The style to be used in rendering
                        this button.
		            cursor: {str} -- The cursor that will appear when the
                        mouse is over the button.
                    width: {int} -- The width of the text area as a number of
                        characters.
		            takefocus: {bool} -- By default, a ttk.Button will be
                        included in focus traversal. To remove the widget
                        from focus traversal, use takefocus=False.
            For Button Widget Only:
		            underline: {int} -- If this option has a nonnegative
                        value n, an underline will appear under the character
                        at position n.
		            compound: {int} -- If you provide both image and text
                        options, the compound option specifies the position
                        of the image relative to the text. The value may be:
                            tk.TOP (image above text),
                            tk.BOTTOM (image below text),
                            tk.LEFT (image to the left of the text), or
                            tk.RIGHT (image to the right of the text).
			            When you provide both image and text options but don't
                        specify a compound option, the image will appear and
                        the text will not.
            For Entry Widget Only:
                    font: {tk.font.Font} -- The font to use for text.
                    justify: {str} -- The position of the text within the
                        entry area. One of: ('left', 'center', 'right')
                    show: {str} -- A single character to substitute for each
                        of the actual characters entered.
        '''
        self.configure(**appearance)

    def build(self, **build_instructions):
        '''Add the widget to it's parent using the grid or pack method.
        Arguments:
            build_instructions: {dict} -- Options related to the layout
                method.
        '''
        build_instructions.update(self.geometry)
        layout_method = build_instructions['build_instructions']
        if 'grid' in layout_method:
            self.grid(**build_instructions)
        elif 'pack' in layout_method:
            self.pack(**build_instructions)
        else:
            raise ValueError



class ButtonManager(WidgetManager, ttk.Button):
    '''Define a Base Button class.
    Arguments:
		name: {str} -- The instance name of the widget.
        manager: {ManagerGUI} -- The top level GUI containing the
            configuration data.
        master: {tk.TK} -- The parent widget or frame.
   		command: {str, callable} -- Either a function to be called when the
           button is pressed, or the name of the item in master.data
           containing the desired callable.
		text: {optional, str} -- The text to appear on the button.
		textvariable: {optional, tk.StringVar} -- A variable containing the
            text to appear on the button.
		image: {optional, tk.PhotoImage} -- An image to appear on the button.
    '''
    widget_type = 'Control'
    default_text = 'Button Widget'

    def __init__(self, name: str, manager: ManagerGUI, **button_params):
        '''Defines the main window for the GUI
        '''
        button_params = self.set_button_params(button_params, manager)
        super().__init__(name, manager, **button_params)

    def set_button_params(self, button_params: dict, manager: ManagerGUI)->dict:
        '''Convert referenced to manager.data into their appropriate values.
        set defaults as needed.
        '''
        button_params['command'] = manager.get_command(
            button_params['command'])
        text_variable = button_params.get('textvariable')
        text_str = button_params.get('text')
        if text_variable:
            button_params['textvariable'] = manager.get_tkvar(text_variable)
        elif text_str:
            button_params['text'] = manager.get_str(text_str)
        else:
            button_params['text'] = self.default_text
        return button_params


class EntryManager(WidgetManager, ttk.Entry):
    '''Define a Base Entry class.
    Arguments:
		name: {str} -- The instance name of the widget.
        manager: {ManagerGUI} -- The top level GUI containing the
            configuration data.
        master: {tk.TK} -- The parent widget or frame.
		textvariable: {optional, Var} -- A variable containing the
            text to appear in the widget.
        validate_command: {str, callable, tuple} -- The test method to be used
            to validate the entry.
        invalidcommand: {str, callable} -- The function to be called, or the
            name of the item in master.data containing the function to be
            called when validation fails.
        validate: {optional, str} -- Specifies when the validate_command will
            be called to validate the text.
        exportselection: {Optional, bool} -- Whether text within an Entry is
            automatically exported to the clipboard. Default is True.
    '''
    widget_type = 'Input'
    default_text = ''
    param_def = dict(textvariable='tkvar', invalidcommand='command',
                     validate='str', exportselection='bool')
    def __init__(self, name: str, manager: ManagerGUI, validate_command=None,
                 **entry_params):
        '''Defines the main window for the GUI
        '''
        updated_entry_params = self.define_entry(manager, entry_params)
        super().__init__(name, manager, **updated_entry_params)

    def set_validate_command(self, manager: ManagerGUI, validate_command):
        '''Convert referenced to manager.data into their appropriate values.
        Set defaults as needed.
        '''
        if isinstance(validate_command, tuple):
            validate_cmd = manager.get_command(validate_command[0])
            validate_command[0] = validate_cmd
        else:
            validate_command = manager.get_command(validate_command)
        return validate_command

    def define_entry(self, manager, entry_params):
        updated_entry_params = manager.get_data(self.param_def, entry_params)
        if validate_command:
            validate_cmd = self.set_validate_command(manager, validate_command)
            updated_entry_params['validatecommand'] = validate_cmd
        return updated_entry_params


class LabelFrameManager(WidgetManager, ttk.LabelFrame):
    '''Define a Base LabelFrame class.
    Arguments:
		name: {str} -- The instance name of the widget.
        manager: {ManagerGUI} -- The top level GUI containing the
            configuration data.
        master: {tk.TK} -- The parent widget or frame.
   		text_str: {optional, str} -- The text to appear as part of the border
            or a reference to a the text in the configuration data.
	    label_widget: {optional, tk.TK, str} -- A widget instance to use as
            the label or a reference to a widget in the configuration data.
    '''
    widget_type = 'Layout'
    default_text = ''
    # TODO add variable describing sub widgets.

    def __init__(self, name: str, manager: ManagerGUI, **frame_params):
        '''Defines the main window for the GUI
        '''
        reduced_frame_params = self.set_frame_params(manager, **frame_params)
        super().__init__(name, manager, **reduced_frame_params)

    def set_frame_params(self, manager: ManagerGUI, label_widget=None,
                         text_str=None, **frame_params)->dict:
        '''Convert arguments that reference manager.data values into their
        appropriate values.  Set defaults as needed.
        Returns modified and unused arguments as a dictionary
        '''
        if label_widget:
            frame_params['labelwidget'] = manager.get_widget(label_widget)
        elif text_str:
            frame_params['text'] = manager.get_str(text_str)
        else:
            frame_params['text'] = self.default_text
        return frame_params


class FileSelectDialog(SelectFile):
    '''Define a Dialog window for selecting files or directories.
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
    Open File Selection Window
	    multiple: {bool} -- If True, Allows the user to choose multiple files
            from the Open dialog.
    '''
    param_def = dict(type_selection='file_types', action='str',
                     starting_path='path', initialfile='str',
                     defaultextension='str', confirmoverwrite='bool',
                     multiple='bool', title='str', check_validity='bool',
                     mustexist='bool', typevariable='tkvar')

    def __init__(self, manager: ManagerGUI, **dialog_params):
        '''Defines the main window for the GUI
        '''
        self.manager = manager
        super().__init__(**dialog_params)

    def define_dialog(self, **dialog_params)->Dict[str, Any]:
        '''Set the definition of the dialog window.
        Extract all parameter values referencing manager.data, define the
        dialog window and return unused parameters.
        Returns:
            A dictionary containing all supplied keyword arguments not used in
            defining the dialog window.
        '''
        matched_data = self.manager.data_match(self.param_def, dialog_params)
        updated_dialog_params = matched_data.updated_parameters
        self.data_link = matched_data.data_link
        unused_parameters = super().configure(**updated_dialog_params)
        return unused_parameters


class FileSelectGui(LabelFrameManager):
    '''GUI frame for selecting a file or directory.
    sub class of ttk.LabelFrame.
    '''
    def __init__(self, name: str, manager: ManagerGUI, **file_params):
        '''Defines the main window for the GUI
        '''
        frame_params = self.set_file_params(manager, **file_params)
        super().__init__(name, manager, **frame_params)

    def browse(self, file_select_dialog):
        '''Function to call when Browse button is clicked.'''
        self.file_str.set(file_select_dialog.call_dialog(parent=self))

    def set_file_params(self, manager: ManagerGUI, path_var: Var = None,
                        **file_params)->dict:
        '''Convert referenced to manager.data into their appropriate values.
        set defaults as needed.
        '''
        file_select_dialog = FileSelectDialog(manager=manager, parent=self)
        reduced_file_params = file_select_dialog.define_dialog(**file_params)
        if path_var:
            self.file_str = manager.get_tkvar(path_var)
        else:
            self.file_str = tk.StringVar()
        self.browse_action = partial(self.browse, file_select_dialog)

        # FIXME do not do a 2 part INIT for the widgets
        self.path_entry = EntryManager('File_Path', manager=manager,
                                       master=self,
                                       textvariable=self.file_str)
        frame_params = self.path_entry.set_entry_params(manager=manager,
                                                        **reduced_file_params)
        self.browse_button = ButtonManager('Browse Button', manager=manager,
                                           master=self, text='Browse',
                                           command=self.browse_action)
        return frame_params

    def build(self, **build_instructions):
        entry_geometry = dict(layout_method='grid', padx=10, pady=5,
                              width=115, column=0, row=0, sticky='nsew')
        entry_appearance = dict(justify='left', cursor='X_cursor')

        button_geometry = dict(layout_method='grid', padx=5, pady=5,
                               width=10, column=0, row=1, sticky='nsew')
        button_appearance = dict(cursor='xterm')

        self.path_entry.set_appearance(**entry_appearance)
        self.path_entry.set_geometry(**entry_geometry)
        self.path_entry.build()

        self.browse_button.set_appearance(**button_appearance)
        self.browse_button.set_geometry(**button_geometry)
        self.browse_button.build()

        frame_geometry = dict(layout_method='grid', padx=0, pady=0,
                              width=115, column=0, row=0, sticky='nsew')
        frame_geometry.update(build_instructions)
        frame_appearance = dict(labelanchor='ne', borderwidth=4,
                                relief='groove')
        self.set_appearance(**frame_appearance)
        self.set_geometry(**frame_geometry)
        self.build()
        self.master.columnconfigure(1, pad=14, minsize=60, weight=0.82)
        self.master.columnconfigure(2, pad=0, minsize=10, weight=0.18)



def build_top(root: tk.Tk, data=None)->tk.Tk:
    '''Generate a top level test window with an exit button in the background.
    Arguments:
        root: {tk.Tk} -- The primary GUI object.
    Returns:
        The toplevel GUI widget.
    '''
    # Define TopLevel geometry as 1024x768, centered on the screen
    scr_w = root.winfo_screenwidth()
    scr_h = root.winfo_screenheight()
    workwindow = (str(1024) + "x" + str(768)+ "+"
                  +str(int((scr_w-1024)/2)) + "+" +str(int((scr_h-768)/2)))
    main_gui = ManagerGUI(root, shape=workwindow, data=data)
    root.attributes('-fullscreen', True)
    root.configure(background='white')
    #exit button - note: uses grid
    exit_button = tk.Button(root, text="Egress", command=root.destroy)
    exit_button.grid(row=0, column=0, ipadx=10, ipady=10,
                     pady=5, padx=5, sticky='wn')
    root.update()
    return main_gui

def basic_test():
    '''Test top level window creation.
    '''
    # TODO convert to function that takes root and returns top_level.
    root = tk.Tk()
    build_top(root)
    root.mainloop()


def button_test():
    '''Test button in top level window.
    '''
    root = tk.Tk()
    main_gui = build_top(root)
    test_message = partial(show_message, 'Button Was Pressed',
                           parent=main_gui)
    test_button = ButtonManager('test button', main_gui, master=main_gui,
                                command=test_message, text='Test Button')
    test_button.grid()
    root.mainloop()


def entry_test():
    '''Test entry in top level window.
    '''
    root = tk.Tk()
    main_gui = build_top(root)
    entry_text = tk.StringVar()
    test_entry = EntryManager('test entry', main_gui, master=main_gui,
                              textvariable=entry_text)
    entry_placement = dict(layout_method='grid', column=0, row=0)
    entry_geometry = dict(ipadx=10, ipady=20, padx=50, pady=10)
    entry_appearance = dict(width=30, justify='center', cursor='xterm')
    test_entry.set_appearance(**entry_appearance)
    test_entry.set_geometry(**entry_geometry)
    test_entry.build(**entry_placement)

    def show_entry():
        '''An info widget that displays the entry text.'''
        show_message(entry_text.get(), main_gui)
    test_button = ButtonManager('test button', main_gui, master=main_gui,
                                command=show_entry, text='Show Text')
    button_appearance = dict(cursor='X_cursor')
    button_placement = dict(layout_method='grid', column=0, row=1, sticky='w')
    test_button.set_appearance(**button_appearance)
    test_button.build(**button_placement)

    root.mainloop()


def file_select_test():
    '''Test entry in top level window.
    '''
    root = tk.Tk()
    file_str = tk.StringVar()
    file_types = FileTypes('Text Files')
    starting_dir = Path.cwd()
    test_data = dict(file_path=file_str,
                     valid_files=file_types,
                     default_path=starting_dir)
    file_selection_parameters = dict(
        name='file_selector',
        action='open',
        starting_path='default_path',
        type_selection='valid_files',
        path_var='file_path',
        text_str='Test File Selection')
    main_gui = build_top(root, data=test_data)
    test_entry = FileSelectGui(manager=main_gui, master=main_gui,
                               **file_selection_parameters)
    test_entry.build()

    def show_file():
        '''An info widget that displays the selected file name.'''
        show_message(file_str.get(), main_gui)
    test_button = ButtonManager('test button', main_gui, master=root,
                                command=show_file, text='Show File')
    test_button.grid(row=1, column=0, ipadx=10, ipady=10,
                     pady=5, padx=5, sticky='wn')
    root.mainloop()


def main():
    '''run current GUI test.
    '''
    file_select_test()

if __name__ == '__main__':
    main()