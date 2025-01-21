from tkinter import  Frame,Label, Button, NORMAL, DISABLED, IntVar, Canvas
from matplotlib.pyplot import Figure
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,NavigationToolbar2Tk)
from matplotlib import style
from tkinter import Frame, Canvas

class LevelMeter(Frame):
    def __init__(self, parent, block_fill_time=4000, click_interval=1000):
        super().__init__(parent, bg='darkgrey')

        self.block_fill_time = block_fill_time  # Time to fill the block (ms)
        self.click_interval = click_interval   # Time interval for click sound (ms)

        self.current_level = 0.0
        self.filling = True  # Start with filling
        self.timer_interval = 10  # ms for smooth updates

        self.total_updates = self.block_fill_time / self.timer_interval  # This will be 400 for 4 seconds
        
        self.step_size = 1.0 / self.total_updates  # How much the level increases/decreases per update
        print(self.total_updates, self.step_size)

        self.counter = 0  # Click sound timer

        # Add a canvas inside the frame to draw the level meter
        self.canvas = Canvas(self, height=80, bg='darkgrey', highlightthickness=0)
        self.canvas.pack(expand=True, fill='both')

    
    def start_animation(self):
        self.update_meter()
        self.after(self.timer_interval, self.start_animation)

    def update_meter(self):
        if self.filling:
            self.current_level += self.step_size
            
            if self.current_level >= 1.0:
                self.current_level = 1.0
                self.filling = False  # Switch to unfilling once filled
        else:
            self.current_level -= self.step_size
            if self.current_level <= 0.0:
                self.current_level = 0.0
                self.filling = True  # Switch to filling once emptied

        # Handle click sound simulation every second
        self.counter += self.timer_interval
        if self.counter >= self.click_interval:
            self.play_click()
            self.counter = 0

        self.draw_meter()

    def draw_meter(self):
        self.canvas.delete("all")
        full_width = self.canvas.winfo_width()
        full_height = self.canvas.winfo_height()

        # Calculate the width of the filled portion based on the current level
        filled_width = full_width * self.current_level

        # Draw the filled portion based on whether we are filling or unfilling
        self.canvas.create_rectangle(0, 0, filled_width, full_height,
                                     fill=self.get_level_colour(self.current_level),
                                     outline="")

    def get_level_colour(self, level):
        """ Return a color from red to green based on the level value. """
        red = int((1.0 - level) * 255)
        green = int(level * 255)
        return f"#{red:02x}{green:02x}00"

    def play_click(self):
        """ Simulate playing a click sound. """
        print("Click!")
