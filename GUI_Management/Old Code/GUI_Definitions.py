from typing import Union, Callable,  List, Dict, Tuple, Any
from collections import OrderedDict
import pandas as pd
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
TkVar = Union[tk.DoubleVar, tk.IntVar, tk.StringVar]

Cmd = Union[str, Callable]
Var = Union[str, tk.DoubleVar, tk.IntVar, tk.StringVar]
Dimension = Union[int, str]

# If you set a dimension to an integer, it is assumed to be in pixels.
# You can specify units by setting a dimension to a string containing a
# number followed by:
#   c	Centimeters
#   i	Inches
#   m	Millimeters
#   p	Printer's points (about 1/72″)

'''
Created on Feb 5 2019

@author: Greg Salomons
GUI Widget definitions for Structure templates.

tk_variables: {OrderedDict} -- All information required to construct and
    synchronize Tkinter variables.  The key is the name of the TKinter
    variable.  The value is a dictionary used for creating, referencing and
    updating the variable:
    
    name: {str} -- The name of the variable.
    type: {class} -- The class of the variable.  One of:
        (tk.DoubleVar, tk.IntVar, tk.StringVar)
    instance: {TkVar} -- The created instance of the variable.
    reference: {str} -- The name of the related Data item or equivalent.
    set_var: {Callable} -- A callable that takes one argument, the reference
        name and returns a value to pass to the TK variable.
    get_var: {Callable} -- A callable that takes two arguments, the value
        from the TK variable and the reference name.  It updates the
        reverence value with the supplied value from the TK variable.


gui_configurations: {OrderedDict} -- All information required to construct
    the GUI objects.

    name: {str} -- The name of the widget. Used as dict key.  Must be unique.
    manager: {ManagerGUI} -- The top level GUI containing the
        configuration data.
    master: {tk.TK} -- The parent widget or frame.
    widget_type: {str} -- The instance name of the widget.  One of:
        'Input' e.g. entry
        'Display' e.g. label
        'Control' e.g. button
        'Layout' e.g. frame
    widget_class: {str} -- The name of the widget class as a string.
    widget_instance: {tk.TK} -- The widget instance. This value is set
        at the time of creation.

    configuration: {dict} -- Contains items describing the function of the
        widget.  Items are specific to the widget type and class:

    ButtonConfiguration:
   		command: {str, callable} -- Either a function to be called when the
           button is pressed, or the name of the item in master.data
           containing the desired callable.
		text: {optional, str} -- The text to appear on the button.
		textvariable: {optional, tk.StringVar} -- A variable containing the
            text to appear on the button.
		image: {optional, tk.PhotoImage} -- An image to appear on the button.

    EntryConfiguration:
        show: {str} -- A single character to substitute for each of the
            actual characters entered.  Used to protect fields such as
            passwords from being visible on the screen.
        exportselection: {Optional, bool} -- Whether text within an Entry is
            automatically exported to the clipboard. Default is True.
        invalidcommand: {str, callable} -- Describes the desired action when
            validation fails. Either a function to be called, or the name of
            the item in master.data containing the desired callable.
		textvariable: {optional, tk.StringVar} -- A variable containing the
            text in the widget.
        validate: {optional, str} -- Specifies when the validatecommand will
            be called to validate the text. Options are:
                'focus' Validate whenever the Entry widget gets or loses focus
                'focusin' Validate whenever the widget gets focus.
                'focusout' Validate whenever the widget loses focus.
                'key' Validate whenever any keystroke changes the widget's contents.
                'all' Validate in all the above situations.
                'none' Turn off validation. This is the default option value.
        validatecommand: {str, callable, tuple} -- The test method to be used
            to validate the entry. It can be:
                The function to be called,
                The name of the item in master.data containing the callable,
                A tuple where the first item is one of the above and the
                    remainder of the items are codes representing values that
                    will be passed as positional arguments to the function:
                        '%d': Action code:
                            0 for an attempted deletion,
                            1 for an attempted insertion, or
                           -1 if the callback was called for
                                focus in, focus out, or
                                a change to the textvariable.
                        '%i': The index of the beginning of the insertion or
                            deletion, or -1 if the callback was due to
                                focus in, focus out, or a change to
                                textvariable.
                        '%P': The value that the text will have if the change
                            is allowed.
                        '%s': The text in the entry before the change.
                        '%S'  The text being inserted or deleted.
                        '%v'  The widget's validate option.
                        '%V'  The reason for this callback: one of:
                            'focusin',
                            'focusout',
                            'key', or
                            'forced' if the textvariable was changed.
                        '%W'  The name of the widget.


    LabelFrameConfiguration:
        text: {optional, str} -- The text to appear as part of the border.
	    labelwidget: {optional, tk.TK} -- A widget instance to use as the
            label.

gui_definition: {DataFrame} -- All information required to construct and
    use a GUI object.  The index is the name of the GUI object.  The columns
    contain dictionaries used for building and executing the GUI:

    Order: {int} -- The order in which to build and update the widgets.
    Level: {int} -- The level of hierarchy for the widget. 0 is the master.

    definition: {dict} -- Contains invariant items that identify a widget:
	    name: {str} -- The instance name of the widget.
	    type: {str} -- The instance name of the widget.  One of:
            'Input' e.g. entry
            'Display' e.g. label
            'Control' e.g. button
            'Layout' e.g. frame
        widget_class: {str} -- The name of the widget class as a string.
        widget_instance: {tk.TK} -- The widget instance. This value is set
            at the time of creation.
        manager: {ManagerGUI} -- The top level GUI containing the
            configuration data.
        master: {tk.TK} -- The parent widget or frame.

gui_appearance: {dict} -- Contains items describing the widget's appearance:
	    style: {ttk.Style} -- The style to be used in rendering the widget.
	    cursor: {str} -- The cursor that appears over the widget.
	    takefocus: {bool} -- To remove the widget from focus traversal, use
            takefocus=False.

        Entry Widget:
            font: {tk.font.Font} -- The font to use for text.
            justify: {str} -- The position of the text within the entry area.
                One of: ('left', 'center', 'right')

        Button widget:
    	    underline: {int} -- An underline to appear under the nth character.
	        compound: {int} -- The position of the image relative to the text:
                tk.TOP (image above text),
                tk.BOTTOM (image below text),
                tk.LEFT (image to the left of the text)
                tk.RIGHT (image to the right of the text)
                Default: The image appears and the text does not.

        LabelFrame widget:
    	    underline: {int} -- An underline to appear under the nth character.
        	labelanchor: {str} -- The position of the label on the widget's
                border. Can contain any combination of:
                    ('n', 's', 'e', 'w',)
	        borderwidth: {Dimension} -- The width of the border around the
                frame.
        	relief: {str} -- The 3-d border style.  One of:
                ('RAISED', 'SUNKEN', 'GROOVE', 'RIDGE)
               A nonzero borderwidth is required for this effect to appear.


    placement: {dict} -- The placement of the widget within it's parent.

        Padding Options (works with both layout managers:
            ipadx: {Dimension} -- Gap inside the widget's left and right sides.
	        ipady: {Dimension} -- Gap inside the widget's top and bottom borders.
            padx: {Dimension} -- Gap outside the widget's left and right sides.
	        pady: {Dimension} -- Gap above and below the widget.

        Frame widget Geometry:
            padding: {Dimension} -- Clear area around the contents of
                the frame.
	        height: {Dimension} -- The height of the frame. Requires calling
                the .grid_propagate(0) or .pack_propagate(0) method.
            width: {Dimension} -- The width of the frame. Requires calling
                the .grid_propagate(0) or .pack_propagate(0) method.

        layout_method: {str} -- The geometry manager to use.  One of:
                ('pack', 'grid'). All widgets with the same parent must use
                the same geometry manager.

        Grid Options:
            column: {int} -- The column number where you want the
                widget placed, counting from zero. The default value
                is zero.
            columnspan: {Optional, int} -- The number of vertical cells the
                widget should occupy.
            row: {int} -- The row number where you want the widget
                placed, counting from zero. The default is the next
                higher-numbered unoccupied row.
            rowspan: {Optional, int} -- The number of horizontal cells the
                widget should occupy.
            sticky: {Optional, str} -- How to position the widget within the
                cell. Can contain any combination of:
                    ('n', 's', 'e', 'w',)
                If 'ns' or 'ew' are used together the widget will
                stretch horizontally or vertically to fill the cell.

        Grid configuration:
            column_number: {int} -- The index to the grid column to be
                    configured.
    	        minsize: {int} -- The column or row's minimum size in pixels.
                pad: {int} -- A number of pixels that will be added to the
                    given column or row, over and above the largest cell in
                    the column or row.
                weight: {int} -- The relative weight of this column or row to
                    be used when distributing the extra space while
                    stretching. If this option is not used, the column or
                    row will not stretch.

        Pack Options:
		    anchor: {Optional, str} -- Where the widget is placed inside the
                packing box.  Can contain any combination of:
                    ('n', 's', 'e', 'w') or center
		    expand: {Optional, bool} -- Whether the widget should fill any
                extra space in the parent. Default is False
		    fill: {Optional, str} -- How the widget should occupy the space
                provided to in the parent. One of:
                    NONE (default)
                    X (fill horizontally)
                    Y (fill vertically)
                    BOTH
            side: {Optional, str} -- Which side to pack the widget against:
                TOP (default), LEFT, BOTTOM, RIGHT

        Button Entry widget:
            width: {int} -- Width of the text area as a number of characters.

gui_appearance: {dict} -- Contains items describing the widget's appearance:
	    style: {ttk.Style} -- The style to be used in rendering the widget.
	    cursor: {str} -- The cursor that appears over the widget.
	    takefocus: {bool} -- To remove the widget from focus traversal, use
            takefocus=False.

        Entry Widget:
            font: {tk.font.Font} -- The font to use for text.
            justify: {str} -- The position of the text within the entry area.
                One of: ('left', 'center', 'right')

        Button widget:
    	    underline: {int} -- An underline to appear under the nth character.
	        compound: {int} -- The position of the image relative to the text:
                tk.TOP (image above text),
                tk.BOTTOM (image below text),
                tk.LEFT (image to the left of the text)
                tk.RIGHT (image to the right of the text)
                Default: The image appears and the text does not.

        LabelFrame widget:
    	    underline: {int} -- An underline to appear under the nth character.
        	labelanchor: {str} -- The position of the label on the widget's
                border. Can contain any combination of:
                    ('n', 's', 'e', 'w',)
	        borderwidth: {Dimension} -- The width of the border around the
                frame.
        	relief: {str} -- The 3-d border style.  One of:
                ('RAISED', 'SUNKEN', 'GROOVE', 'RIDGE)
               A nonzero borderwidth is required for this effect to appear.



'''
