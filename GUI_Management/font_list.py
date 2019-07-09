from pathlib import Path
import xml.etree.ElementTree as ET
import tkinter as tk
import tkinter.font as tkFont

root = tk.Tk()
family_list = list(tkFont.families())
family_list.sort()
for family in family_list:
    print("\t{}".format(family))

