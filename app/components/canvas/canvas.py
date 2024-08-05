
from tkinter import LabelFrame, Frame, IntVar, Radiobutton
from components.stream.stream import StreamFrame
from components.analyse.analyse import AnalyseFrame

class Canvas(LabelFrame):
    def __init__(self, master,  settings,  *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.s = settings
       
        self.configure(text = "Osteosense",)

        # makes the column and row in this widget expandable
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.operations_frame = Frame(self)
        self.operations_frame.grid(row=0, column=0, columnspan=1, sticky="nsew")

        self.stream_var = IntVar()
        
        # Create radio buttons to switch frames
        self.stream_rb = Radiobutton(self.operations_frame, text="stream", value=0, variable = self.stream_var, command=self.select_frame)
        self.stream_rb.grid(row=0,column=0,pady=5, sticky="w")
        self.analyse_rb = Radiobutton(self.operations_frame, text="analyse", value=1, variable = self.stream_var, command=self.select_frame)
        self.analyse_rb.grid(row=0,column=1,pady=5, sticky="w" )

        self.grid(row=1, column=0,rowspan=1,columnspan=1, sticky='news',padx=5,pady=5)

        # conditionally load the correct frame
        if(self.s.get_default_frame() == 0):
            self.stream_frame = StreamFrame(self, self.s) 
        else:
            self.analyse_frame = AnalyseFrame(self, self.s)

    def select_frame(self):
        if(self.stream_var.get() == 0):
            self.analyse_frame.grid_forget()
            self.stream_frame = StreamFrame(self, self.s) 
        elif(self.stream_var.get() == 1):
            self.stream_frame.grid_forget()
            self.analyse_frame = AnalyseFrame(self, self.s)

