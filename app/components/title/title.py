from tkinter import Label, CENTER

class Title(Label):
    def __init__(self, master, text, *args, **kwargs):
        super().__init__(master, 
                         width=60, 
                         height=2, 
                         pady=2, 
                         bg='black', 
                         fg="#616CAB", 
                         text=text,  
                         font=("Montserrat", 20, "bold"),  # Bold font 
                         anchor=CENTER, 
                         #highlightbackground="purple",  # Border color
                         #highlightcolor="purple",       # Border color when focused
                         #highlightthickness=2,          # Thickness of border
                         *args, **kwargs)
        self.grid(row=0, column=0, columnspan=1, sticky='nsew')
