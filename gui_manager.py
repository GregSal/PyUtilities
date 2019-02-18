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
from typing import Union, Callable, List, Dict, Tuple, Any
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

Cmd = Union[Callable, str]
Var = Union[str, tk.DoubleVar, tk.IntVar, tk.StringVar]
Bol = Union[bool, str]
Dimension = Union[int, str]
Widget = Union[str, tk.Widget]


# If you set a dimension to an integer, it is assumed to be in pixels.
# You can specify units by setting a dimension to a string containing a
# number followed by:
#   c	Centimeters
#   i	Inches
#   m	Millimeters
#   p	Printer's points (about 1/72″)


def show_message(msg: str, parent: tk.Tk):
        messagebox.showinfo('Test message', msg, parent=parent)

class DataConfig(object):
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
        else:
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
        else:
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
        else:
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
        else:
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
        else:
            return bool(variable)

class WidgetManager(object):
    '''Define methods common to all WidgetManager classes.
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
    widget_type = None
    default_geometry = {'ipadx': 5, 'ipady': 5, 'padx': 5, 'pady': 5}
    default_placement = {}
    def __init__(self, name: str, manager: DataConfig, **widget_parameters):
        '''Configure widget parameters.
        '''
        self.manager = manager
        widget_parameters['name'] = name
        self.set_geometry()
        super().__init__(**widget_parameters)

    def set_geometry(self, **geometry):
        '''Set the parameters for the widget's padding.
        Arguments:
            geometry: {dict} -- Contains items describing the padding around
                the widget.  Items are:
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

    def set_placement(self, **placement):
        '''Define the widget's placement in it's parent widget.
        Arguments:
            placement: {dict} -- Contains items to be passed to the grid or
                pack method.  Items are:
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
        self.placement = self.default_placement
        if placement:
            self.placement.update(placement)

    def build(self, layout_method='grid', **build_instructions):
        '''Add the widget to it's parent using the grid or pack method.
        Arguments:
            layout_method: {str} -- the layout method to use.
                One of: 'pack' or 'grid'. Default is 'grid'.
            build_instructions: {dict} -- Options related to the layout
                method.
        '''
        build_instructions.update(self.geometry)
        if 'grid' in layout_method:
            self.grid(**build_instructions)
        elif 'pack' in layout_method:
            self.pack(**build_instructions)
        else:
            raise ValueError

    def update(self):
        '''Update data values.
        '''
        pass  # TODO make Update method


class ManagerGUI(DataConfig, tk.Toplevel):
    '''Base class for Gui frames containing defaults and parameters.
    '''
    def __init__(self, root, shape=None, title='Test GUI', data=None):
        '''Defines the main window for the GUI
        '''
        bg_color = 'light blue'
        super().__init__(root, bg=bg_color, data=data)
        self.geometry(shape)
        self.title(title)
        # make sure main_gui is on top to start
        self.attributes("-topmost", 1)
        #self.attributes("-topmost", 0)


    def build(self, build_instructions):
        '''Configure the GUI frame and add sub-frames.
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
        button_icon = button_params.get('image')
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
		textvariable: {optional, tk.StringVar} -- A variable containing the
            text to appear in the widget.
        validatecommand: {str, callable, tuple} -- The test method to be used
            to validate the entry.
        invalidcommand: {str, callable} -- The function to be called, or the
            name of the item in master.data containing the function to be
            called when validation fails.
        validate: {optional, str} -- Specifies when the validatecommand will
            be called to validate the text.
        exportselection: {Optional, bool} -- Whether text within an Entry is
            automatically exported to the clipboard. Default is True.
    '''
    widget_type = 'Input'
    default_text = ''

    def __init__(self, name: str, manager: ManagerGUI, **entry_params):
        '''Defines the main window for the GUI
        '''
        entry_params = self.set_entry_params(entry_params, manager)
        super().__init__(name, manager, **entry_params)

    def set_entry_params(self, entry_params: dict, manager: ManagerGUI)->dict:
        '''Convert referenced to manager.data into their appropriate values.
        set defaults as needed.
        '''
        validate_command = entry_params.get('validatecommand')
        invalid_command = entry_params.get('invalidcommand')
        text_variable = entry_params.get('textvariable')
        validate = entry_params.get('validate')
        to_clipboard = entry_params.get('exportselection')
        if validate_command:
            if isinstance(validate_command, tuple):
                command = manager.get_command(validate_command[0])
                validate_command[0] = command
            else:
                validate_command = manager.get_command(validate_command)
        if invalid_command:
            entry_params['invalidcommand'] = manager.get_command(
                invalid_command)
        if text_variable:
            entry_params['textvariable'] = manager.get_tkvar(text_variable)
        if validate:
            entry_params['validate'] = manager.get_str(validate)
        if to_clipboard:
            entry_params['exportselection'] = manager.get_bool(to_clipboard)
        return entry_params


class LabelFrameManager(WidgetManager, ttk.Frame):
    '''Define a Base LabelFrame class.
    Arguments:
		name: {str} -- The instance name of the widget.
        manager: {ManagerGUI} -- The top level GUI containing the
            configuration data.
        master: {tk.TK} -- The parent widget or frame.
   		text: {optional, str} -- The text to appear as part of the border.
	    labelwidget: {optional, tk.TK} -- A widget instance to use as the
            label.
    '''
    widget_type = 'Layout'
    default_text = ''
    # TODO add variable describing sub widgets.

    def __init__(self, name: str, manager: ManagerGUI, **frame_params):
        '''Defines the main window for the GUI
        '''
        frame_params = self.set_frame_params(frame_params, manager)
        super().__init__(name, manager, **frame_params)

    def set_frame_params(self, frame_params: dict, manager: ManagerGUI)->dict:
        '''Convert reference to manager.data into their appropriate values.
        set defaults as needed.
        '''
        text_str = frame_params.get('text')
        label_widget = frame_params.get('labelwidget')
        if label_widget:
            frame_params['labelwidget'] = manager.get_widget(label_widget)
        elif text_str:
            frame_params['text'] = manager.get_str(text_str)
        else:
            frame_params['text'] = self.default_text
        return frame_params




def build_top(root: tk.Tk)->tk.Tk:
    '''Generate a top level test window with an exit button in the background.
    Arguments:
        root: {tk.Tk} -- The primary GUI object.
    Returns:
        The toplevel GUI widget.
    '''
    # Define TopLevel geometry as 1024x768, centered on the screen
    scrW = root.winfo_screenwidth()
    scrH = root.winfo_screenheight()
    workwindow = (str(1024) + "x" + str(768)+ "+"
                  +str(int((scrW-1024)/2)) + "+" +str(int((scrH-768)/2)))
    main_gui = ManagerGUI(root, shape=workwindow)
    root.attributes('-fullscreen', True)
    root.configure(background='white')
    #exit button - note: uses grid
    exit_button=tk.Button(root, text="Egress", command=root.destroy)
    exit_button.grid(row=0,column=0,ipadx=10, ipady=10,
                     pady=5, padx=5, sticky='wn')
    root.update()
    return main_gui

def basic_test():
    '''Test top level window creation.
    '''
    # TODO convert to function that takes root and returns top_level.
    root = tk.Tk()
    main_gui = build_top(root)
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


def main():
    '''run current GUI test.
    '''
    entry_test()

if __name__ == '__main__':
    main()