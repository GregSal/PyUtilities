# -*- coding: utf-8 -*-
'''
Created on Wed Sept 4 2019

@author: gsalomon
Select and Save file dialogues.
'''

from pathlib import Path
import tkinter as tk
from tkinter import filedialog


def select_file(starting_dir=Path.cwd())->Path:
    '''Select a file.
    Arguments
        starting_dir {Path} -- The directory to begin with when prompting for
            file selection.   Default is current working directory.
    Returns
        Path -- The full path to the file.
    '''
    root = tk.Tk()
    root.withdraw()
    filename =  filedialog.askopenfilename(
            initialdir=starting_dir,
            title = "Select a file",
            filetypes = (("Text files","*.txt"),
                         ("all files","*.*"))
            )
    return Path(filename)


def save_file(text_to_save: str, starting_dir=Path.cwd())->Path:
    '''Save the text as a file.
    Arguments
        text_to_save {str} -- The text to be saved in the file.
    Keyword Arguments
        starting_dir {Path} -- The directory to begin with when prompting for
            file save. Default is current working directory.
    Returns
        Bool -- True for successfule file save False otherwise.
    '''
    root = tk.Tk()
    root.withdraw()
    filename =  filedialog.asksaveasfilename(
            initialdir=starting_dir,
            initialfile='Text.txt',
            title = "Save Text As:",
            defaultextension='.txt',
            confirmoverwrite=True,
            filetypes = (("Text files","*.txt"),
                         ("all files","*.*"))
            )
    save_file = Path(filename)    
    return save_file.write_text(text_to_save)

