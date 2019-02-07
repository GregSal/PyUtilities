"""
Created on Mon Jan 7 2018

@author: Greg Salomons
"""
from pathlib import Path
from functools import partial

import tkinter as tk
from tkinter import ttk
#from tkinter.ttk import Treeview

import Tables as tb
from SelectTemplates import import_template_list


root = tk.Tk()
root.title("TreeView Test")
tree = ttk.Treeview(root)
tree.pack()

# Inserted at the root, program chooses id:
tree.insert('', 'end', 'widgets', text='Widget Tour')
# Same thing, but inserted as first child:
tree.insert('', 0, 'gallery', text='Applications')
# Treeview chooses the id:
id = tree.insert('', 'end', text='Tutorial')
# Inserted underneath an existing node:
tree.insert('widgets', 'end', text='Canvas')
tree.insert(id, 'end', text='Tree')
tree.move('widgets', 'gallery', 'end')  # move widgets under gallery
# tree.detach('widgets')
# tree.delete('widgets')
tree.item('widgets', open=True)
isopen = tree.item('widgets', 'open')


tree = ttk.Treeview(root, columns=('size', 'modified'))
tree['columns'] = ('size', 'modified', 'owner')
tree.column('size', width=100, anchor='center')
tree.heading('size', text='Size')
tree.set('widgets', 'size', '12KB')
size = tree.set('widgets', 'size')
tree.insert('', 'end', text='Listbox', values=('15KB Yesterday mark'))
tree.insert('', 'end', text='button', tags=('ttk', 'simple'))
tree.tag_configure('ttk', background='yellow')
tree.tag_bind('ttk', '<1>', itemClicked)  # the item clicked can be found via tree.focus()


active_templates = import_template_list(base_path)


from tkinter import *
window = Tk()
window.title("Welcome to LikeGeeks app")
window.geometry('350x200')
spin = Spinbox(window, from_=0, to=100, width=5)
spin.grid(column=0,row=0)
window.mainloop()
bar = Progressbar(window, length=200)
spin = Spinbox(window, values=(3, 8, 11), width=5)
var =IntVar()
var.set(36)
spin = Spinbox(window, from_=0, to=100, width=5, textvariable=var)
bar['value'] = 70


from tkinter import *
from tkinter.ttk import Progressbar
from tkinter import ttk
window = Tk()
window.title("Welcome to LikeGeeks app")
window.geometry('350x200')
style = ttk.Style()
style.theme_use('default')
style.configure("black.Horizontal.TProgressbar", background='black')
bar = Progressbar(window, length=200, style='black.Horizontal.TProgressbar')
bar['value'] = 70
bar.grid(column=0, row=0)

window.mainloop()


def calculate(*args):
    try:
        value = float(feet.get())
        meters.set((0.3048 * value * 10000.0 + 0.5)/10000.0)
    except ValueError:
        pass

root = Tk()
root.title("Feet to Meters")
mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)
feet = StringVar()
meters = StringVar()
feet_entry = ttk.Entry(mainframe, width=7, textvariable=feet)
feet_entry.grid(column=2, row=1, sticky=(W, E))
ttk.Label(mainframe, textvariable=meters).grid(column=2, row=2, sticky=(W, E))
ttk.Button(mainframe, text="Calculate", command=calculate).grid(column=3, row=3, sticky=W)
ttk.Label(mainframe, text="feet").grid(column=3, row=1, sticky=W)
ttk.Label(mainframe, text="is equivalent to").grid(column=1, row=2, sticky=E)
ttk.Label(mainframe, text="meters").grid(column=3, row=2, sticky=W)
for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)
feet_entry.focus()
root.bind('<Return>', calculate)
root.mainloop()
