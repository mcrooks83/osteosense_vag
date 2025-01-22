import tkinter as tk
import threading
import time
import pygame

class LevelMeter(tk.Frame):
    def __init__(self, parent, dot_fill_time=1000, click_interval=1000):
        super().__init__(parent)
        
        pygame.mixer.init()

        self.dot_fill_time = dot_fill_time  # Time to fill each dot (ms)
        self.click_interval = click_interval  # Time interval for click sound (ms)

        self.num_dots = 4
        self.current_dot = 0
        self.filling_phase = True  # Flag to track if we're filling or clearing the dots
        self.timer_interval = dot_fill_time  # ms

        self.canvas = tk.Canvas(self, height=40, highlightthickness=0)
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

    def _beep_and_start_meter(self):
        for _ in range(3):
            self.play_click()
            time.sleep(1)

        self.level_meter_thread = threading.Thread(target=self.update_level_meter)
        self.level_meter_thread.daemon = True
        self.level_meter_thread.start()

        self.after(self.timer_interval, self.update_meter)

    def stop_level_meter(self):
        self.stop_flag = True
        if self.level_meter_thread and self.level_meter_thread.is_alive():
            self.level_meter_thread.join()

        self.current_dot = 0
        self.update_flag = False
        self.canvas.delete("all")

    def update_level_meter(self):
        while not self.stop_flag:
            if self.filling_phase:
                # Fill dots left to right
                if self.current_dot < self.num_dots:
                    self.current_dot += 1
                else:
                    self.filling_phase = False  # Switch to clearing phase
            else:
                # Clear dots right to left
                if self.current_dot > 0:
                    self.current_dot -= 1
                else:
                    self.filling_phase = True  # Switch back to filling phase

            self.update_flag = True
            self.play_click()

            time.sleep(self.timer_interval / 1000.0)

    def update_meter(self):
        if self.update_flag:
            self.draw_meter()
            self.update_flag = False
        self.after(self.timer_interval, self.update_meter)

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
            color = "green" if i < self.current_dot else "lightgrey"
            x = start_x + i * (dot_diameter * 4)  # Position each dot
            self.canvas.create_oval(x, 10, x + dot_diameter, 10 + dot_diameter, fill=color)

    def play_click(self):
        pygame.mixer.Sound('boop.wav').play()
