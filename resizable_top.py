import tkinter as tk
import tkinter.font as tkFont
import tkinter.ttk as ttk

class Application(tk.Frame):
    def __init__(self, master=None):
           tk.Frame.__init__(self, master)
           self.grid(sticky=tk.N+tk.S+tk.E+tk.W)
           self.createWidgets()
    def createWidgets(self):
        top=self.winfo_toplevel()
        normal_font = tkFont.Font(family='Calibri', size=11, weight='normal')
        button_font = tkFont.Font(family='Calibri', size=12, weight='bold')
        title_font = tkFont.Font(family='Tacoma', size=36, weight='bold')
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)
        sg_w = ttk.Sizegrip(top)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.quit = ttk.Button(self, text='Quit', command=self.quit)
        self.quit.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)

app = Application()
app.master.title('Sample application')
app.mainloop()




