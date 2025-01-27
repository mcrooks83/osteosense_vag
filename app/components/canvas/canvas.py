
from tkinter import  Frame, IntVar, Radiobutton, Button
from components.stream.stream import StreamFrame
from components.analyse.analyse import AnalyseFrame

class Canvas(Frame):
    def __init__(self, master,  settings,  *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.s = settings
       
        self.configure(bg="black")
        self.grid(row=1, column=0,rowspan=1,columnspan=1, sticky='news',padx=5,pady=5)

        # makes the column and row in this widget expandable
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.operations_frame = Frame(self, bg="black")
        self.operations_frame.grid(row=0, column=0, columnspan=1, sticky="nsew", padx=5, pady=10)

        self.stream_var = IntVar()

        # Create radio buttons to switch frames
        self.stream_rb = Radiobutton(self.operations_frame, text="Stream", value=0, variable = self.stream_var, 
                                     command=self.select_frame, bg="black", fg="white",
                                     font=("Montserrat", 14), 
                                     selectcolor="#616CAB",
                                     anchor="w", 
                                   
                                     )
        self.stream_rb.grid(row=0,column=0,pady=5, sticky="w", padx=20)
        self.analyse_rb = Radiobutton(self.operations_frame, text="Analyse", value=1, variable = self.stream_var, 
                                      command=self.select_frame, bg="black", fg="white",
                                      font=("Montserrat", 14), 
                                       selectcolor="#616CAB",
                                       anchor="w", 
                                       )
        self.analyse_rb.grid(row=0,column=1,pady=5, sticky="w", padx=20 )

        # conditionally load the correct frame - for now this will always be stream but can be added back to play back previous recordings.
        
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

