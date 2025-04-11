import tkinter as tk
import pygame
from customtkinter import CTkFrame, CTkCanvas
import sys, os

class LevelMeter(CTkFrame):
    def __init__(self, parent, settings, dot_fill_time=1000, click_interval=1000):
        super().__init__(parent)

        # this can be moved to settings
        if getattr(sys, 'frozen', False):  # Check if the app is frozen (running as an executable)
            self.base_path = sys._MEIPASS  # If frozen, use the temporary folder where PyInstaller extracts the files
        else:
            self.base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # Go up two levels to the root directory

        
        pygame.mixer.init()
        self.s = settings

        self.num_dots = 4
        self.dot_fill_time = int(self.s.get_half_cycle_time() * 1000 / self.num_dots)  # Time to fill each dot (ms)
        
        self.current_dot = 0
        self.filling_phase = True  # Flag to track if we're filling or clearing the dots

        self.canvas = CTkCanvas(self, height=100, width=1000, bg="gray16", borderwidth=0, highlightthickness=0) #highlightthickness=0,bg="black")
        self.canvas.pack()

        self.update_flag = False
        self.stop_flag = False
        self.level_meter_thread = None
        self.check_canvas_width()

    def check_canvas_width(self):
        # Continuously check for the width of the canvas until it's rendered
        canvas_width = self.canvas.winfo_width()
        if canvas_width > 1:
            self.draw_meter()  # Now it's safe to draw the dots
        else:
            self.after(100, self.check_canvas_width)  # Check again after a short delay

    def stop_level_meter(self):
        self.stop_flag = True
        self.current_dot = 0
        self.update_flag = False
        self.draw_meter()  # Redraw the empty meter

    def start_level_meter(self):
        if self.level_meter_thread is None or not self.level_meter_thread.is_alive():
            self.stop_flag = False
            self.current_dot = 0  # Start at the beginning
            self.filling_phase = True

            self.play_click()  # First beep with first dot

            self.update_meter()  # Start the Tkinter update loop

    def update_meter(self):
        if self.stop_flag:
            return

        # If we are filling dots
        if self.filling_phase:
            if self.current_dot < self.num_dots:
                self.current_dot += 1  # Fill one more dot
                self.play_click()  # Beep when a new dot is filled
            # Once full, we switch to clearing phase without a delay
            if self.current_dot == self.num_dots:
                self.filling_phase = False
        # If we are clearing dots
        else:
            if self.current_dot > 0:
                self.current_dot -= 1  # Remove one dot
                self.play_click()  # Beep when a dot is cleared
            # Once empty, we switch to filling phase without a delay
            if self.current_dot == 0:
                self.filling_phase = True

        self.draw_meter()  # Draw the updated meter
        self.after(self.dot_fill_time, self.update_meter)  # Schedule the next update in 1 second

    def draw_meter(self):
        self.canvas.delete("all")
        dot_radius = 20
        dot_diameter = 2 * dot_radius
        canvas_width = self.canvas.winfo_width()

        total_dots_width = self.num_dots * dot_diameter
        total_spacing_width = ((self.num_dots - 1) * dot_diameter) * 2  # Space between dots

        total_width_needed = total_dots_width + total_spacing_width

        # Calculate the start position to center the dots
        start_x = (canvas_width - total_width_needed) / 2

        padding_top = 10  # Space above dots for label & arrow
        arrow_y = padding_top  # Arrow and label position

        # Define shorter arrow start and end positions
        arrow_length = (self.num_dots - 1) * (dot_diameter)  # Reduce arrow length
        arrow_start_x = start_x + (dot_diameter * 2)  # Shift start to center it better
        arrow_end_x = arrow_start_x + arrow_length

        # Draw label + forward arrow (extension: left to right)
        if(self.filling_phase):
            fill_color = "#3a7ebf"
        else:
            fill_color = "gray90"

        self.canvas.create_text(arrow_start_x - 15, arrow_y, text="Extension", fill=fill_color, font=("Montserrat", 8, "bold"), anchor="e")
        self.canvas.create_line(arrow_start_x, arrow_y, arrow_end_x, arrow_y, fill=fill_color, width=2, arrow=tk.LAST)
        # Draw the dots
        dot_y = arrow_y + 20  # Move dots slightly lower
        for i in range(self.num_dots):
            color = "#3a7ebf" if i < self.current_dot else "gray20"
            x = start_x + i * (dot_diameter * 4)  # Position each dot
            self.canvas.create_oval(x, dot_y, x + dot_diameter, dot_y + dot_diameter, fill=color, outline="")

        arrow_y_below = dot_y + dot_diameter + 20  # Adjusted position below dots
        flexion_start_x = start_x + (self.num_dots - 1) * (dot_diameter * 4) -20 # Start at last dot
        flexion_end_x = flexion_start_x - arrow_length  # Move backward

        
        if(self.filling_phase == False):
            flex_fill_color = "#3a7ebf"
        else:
            flex_fill_color = "gray90"

        self.canvas.create_text(flexion_start_x + 15, arrow_y_below, text="Flexion", fill=flex_fill_color, font=("Montserrat", 8, "bold"), anchor="w")
        self.canvas.create_line(flexion_start_x, arrow_y_below, flexion_end_x, arrow_y_below, fill=flex_fill_color, width=2, arrow=tk.LAST)
            

    def play_click(self):
        boop_wav_path = os.path.join(self.base_path, "assets", 'boop.wav')
        pygame.mixer.Sound(boop_wav_path).play()
