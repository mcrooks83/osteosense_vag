#from tkinter import Label, CENTER
from customtkinter import CTkLabel, CENTER

class Title(CTkLabel):
    def __init__(self, master, text, *args, **kwargs):
        super().__init__(master, 
                         width=80, 
                         height=50, 
                         pady=1, 
                         bg_color='black', 
                         #fg_color="#616CAB", 
                         fg_color= "#3a7ebf", # inkeeping with the theme
                         text=text,  
                         font=("Montserrat", 20, "bold"),  # Bold font 
                         anchor=CENTER, 
                         #highlightbackground="purple",  # Border color
                         #highlightcolor="purple",       # Border color when focused
                         #highlightthickness=2,          # Thickness of border
                         *args, **kwargs)
        self.grid(row=0, column=0, columnspan=1, sticky='nsew')
