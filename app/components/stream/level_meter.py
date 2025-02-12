import tkinter as tk
import threading
import time
import pygame

from customtkinter import CTkFrame, CTkCanvas


class LevelMeter(CTkFrame):
    def __init__(self, parent, block_fill_time=4000, click_interval=1000):
        super().__init__(parent)

        pygame.mixer.init()

        self.block_fill_time = block_fill_time  # Time to fill the block (ms)
        self.click_interval = click_interval   # Time interval for click sound (ms)

        self.current_level = 0.0
        self.filling = True  # Start with filling
        self.timer_interval = 1000  # ms for smooth updates

        self.total_updates = self.block_fill_time / self.timer_interval
        self.step_size = 1.0 / self.total_updates
        self.counter = 0  # Click sound timer

        self.canvas = CTkCanvas(self, height=40) # highlightthickness=0)
        self.canvas.pack(expand=True, fill='both')

        self.update_flag = False
        self.level_meter_thread = None
        self.stop_flag = False  # Flag to stop the background thread

    def start_level_meter(self):
        """Start the level meter after 3 beeps."""
        if self.level_meter_thread is None or not self.level_meter_thread.is_alive():
            self.stop_flag = False
            # Start a thread to beep 3 times before starting the meter
            threading.Thread(target=self._beep_and_start_meter, daemon=True).start()

    def _beep_and_start_meter(self):
        """Play 3 beeps, then start the meter with an empty level."""
        for _ in range(3):
            self.play_click()
            time.sleep(1)  # 1 second delay between beeps

        # Start the actual level meter update process
        self.level_meter_thread = threading.Thread(target=self.update_level_meter)
        self.level_meter_thread.daemon = True
        self.level_meter_thread.start()

        # Schedule the periodic UI updates
        self.after(self.timer_interval, self.update_meter)

    def stop_level_meter(self):
        """Stop the level meter by setting the stop flag."""
        self.stop_flag = True
        if self.level_meter_thread and self.level_meter_thread.is_alive():
            self.level_meter_thread.join()

        self.current_level = 0.0
        self.filling = True
        self.update_flag = False

        self.canvas.delete("all")

    def update_level_meter(self):
        """Background thread that calculates the level updates."""
        
        while not self.stop_flag:
            if self.filling:
                self.current_level += self.step_size
                if self.current_level >= 1.0:
                    self.current_level = 1.0
                    self.filling = False
            else:
                self.current_level -= self.step_size
                if self.current_level <= 0.0:
                    self.current_level = 0.0
                    self.filling = True

            self.counter += self.timer_interval
            if self.counter >= self.click_interval:
                self.play_click()
                self.counter = 0

            self.update_flag = True

            time.sleep(self.timer_interval / 1000.0)

    def update_meter(self):
        """Update the UI if needed."""
        if self.update_flag:
            self.draw_meter()
            self.update_flag = False
        self.after(self.timer_interval, self.update_meter)

    def draw_meter(self):
        """Draw the level meter."""
        self.canvas.delete("all")
        full_width = self.canvas.winfo_width()
        full_height = self.canvas.winfo_height()

        filled_width = full_width * self.current_level

        self.canvas.create_rectangle(0, 0, filled_width, full_height,
                                     fill=self.get_level_colour(self.current_level),
                                     outline="")

    def get_level_colour(self, level):
        """Return a color from red to green based on the level."""
        red = int((1.0 - level) * 255)
        green = int(level * 255)
        return f"#{red:02x}{green:02x}00"

    def play_click(self):
        """Play a beep sound."""
        pygame.mixer.Sound('boop.wav').play()
