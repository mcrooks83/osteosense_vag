import tkinter as tk
import threading
import time
import pygame

class LevelMeter(tk.Frame):
    def __init__(self, parent, dot_fill_time=1000, click_interval=1000):
        super().__init__(parent)
        
        pygame.mixer.init()
        self.configure(bg="black")

        self.dot_fill_time = dot_fill_time  # Time to fill each dot (ms)
        self.click_interval = click_interval  # Time interval for click sound (ms)

        self.num_dots = 4
        self.current_dot = 0
        self.filling_phase = True  # Flag to track if we're filling or clearing the dots
        self.timer_interval = dot_fill_time  # ms

        self.canvas = tk.Canvas(self, height=40, highlightthickness=0,bg="black")
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

    def start_level_meter(self):
        if self.level_meter_thread is None or not self.level_meter_thread.is_alive():
            self.stop_flag = False
            threading.Thread(target=self._beep_and_start_meter, daemon=True).start()

    def stop_level_meter(self):
        self.stop_flag = True
        if self.level_meter_thread and self.level_meter_thread.is_alive():
            self.level_meter_thread.join()

        self.current_dot = 1
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
        self.after(1000, self.update_meter)  # Schedule the next update in 1 second

    def draw_meter(self):
        self.canvas.delete("all")
        dot_radius = 10
        dot_diameter = 2 * dot_radius
        canvas_width = self.canvas.winfo_width()

        total_dots_width = self.num_dots * dot_diameter
        total_spacing_width = ((self.num_dots - 1) * dot_diameter) * 2  # Space between dots

        total_width_needed = total_dots_width + total_spacing_width

        # Calculate the start position to center the dots
        start_x = (canvas_width - total_width_needed) / 2

        # Draw the dots
        for i in range(self.num_dots):
            color = "#616CAB" if i < self.current_dot else "white"
            x = start_x + i * (dot_diameter * 4)  # Position each dot
            self.canvas.create_oval(x, 10, x + dot_diameter, 10 + dot_diameter, fill=color)

    def play_click(self):
        pygame.mixer.Sound('boop.wav').play()
