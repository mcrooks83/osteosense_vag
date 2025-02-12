# main app entry point

#tkinter
from tkinter import Tk

#from classes.Config import Config
from components.title import title as t
from components.canvas import canvas as c
#from classes.LocalSensorManager import LocalSensorManager
from settings import settings as s
import os, sys
import customtkinter as ctk

# main application class
class MainApplication(ctk.CTk):
    def __init__(self):
        super().__init__()

        settings = s.Settings()

        # screen setup
        self.width = Tk.winfo_screenwidth(self)
        self.height = Tk.winfo_screenheight(self)
        self.geometry(f"{self.width}x{self.height}")
        self.state("zoomed")
        '''
        if(sys.platform == "linux"):
            self.state("normal")
        else:
            self.state("zoomed")
        '''
        self.title("A Right Step Health & TalTech Collaboration")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        #self.configure(bg="black")
        ctk.set_default_color_theme("dark-blue")
        ctk.set_appearance_mode("dark")

        
        self.canvas = c.Canvas(self, settings)
        self.title_label = t.Title(self, text="OSTEOSENSE VIBROSONIX")

        
def on_menu_select(self):
     pass

def on_keyboard_interrupt( event):
        print("killing app", event)
        app.destroy()
        os._exit(0)

if __name__ == "__main__":
    app = MainApplication()
    app.bind("<Control-c>", on_keyboard_interrupt)
    app.mainloop()