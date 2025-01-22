
from tkinter import LabelFrame, Frame, IntVar, Radiobutton, Button
from components.stream.stream import StreamFrame
from components.analyse.analyse import AnalyseFrame

class Canvas(Frame):
    def __init__(self, master,  settings,  *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.s = settings
       
        self.configure(bg="black")

        # makes the column and row in this widget expandable
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)


        self.stream_var = IntVar()

        self.grid(row=1, column=0,rowspan=1,columnspan=1, sticky='news',padx=5,pady=5)

        # conditionally load the correct frame - for now this will always be stream but can be added back to play back previous recordings.
        #if(self.s.get_default_frame() == 0):
        self.stream_frame = StreamFrame(self, self.s) 
        #else:
        #    self.analyse_frame = AnalyseFrame(self, self.s)

    def select_frame(self):
        if(self.stream_var.get() == 0):
            self.analyse_frame.grid_forget()
            self.stream_frame = StreamFrame(self, self.s) 
        elif(self.stream_var.get() == 1):
            self.stream_frame.grid_forget()
            self.analyse_frame = AnalyseFrame(self, self.s)

