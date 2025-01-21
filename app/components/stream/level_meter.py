import tkinter as tk
import threading
import time
import sys
import pygame


class LevelMeter(tk.Frame):
    def __init__(self, parent, block_fill_time=4000, click_interval=1000):
        super().__init__(parent, bg='darkgrey')

        pygame.mixer.init()

        self.block_fill_time = block_fill_time  # Time to fill the block (ms)
        self.click_interval = click_interval   # Time interval for click sound (ms)

        self.current_level = 0.0
        self.filling = True  # Start with filling
        self.timer_interval = 1000  # ms for smooth updates

        self.total_updates = self.block_fill_time / self.timer_interval  # This will be 400 for 4 seconds
        self.step_size = 1.0 / self.total_updates  # How much the level increases/decreases per update
        self.counter = 0  # Click sound timer

        # Add a canvas inside the frame to draw the level meter
        self.canvas = tk.Canvas(self, height=80, bg='darkgrey', highlightthickness=0)
        self.canvas.pack(expand=True, fill='both')

        # Create a flag to communicate between the background thread and the main thread
        self.update_flag = False

        # Initially, don't start the level meter, it will be started later
        self.level_meter_thread = None
        self.stop_flag = False  # Flag to stop the background thread

    def start_level_meter(self):
        """Start the level meter update process in a background thread."""
        if self.level_meter_thread is None or not self.level_meter_thread.is_alive():
            self.stop_flag = False  # Ensure stop flag is reset when starting
            self.level_meter_thread = threading.Thread(target=self.update_level_meter)
            self.level_meter_thread.daemon = True
            self.level_meter_thread.start()

        # Call the method to periodically check the flag and update the meter
        self.after(self.timer_interval, self.update_meter)

    def stop_level_meter(self):
        """Stop the level meter by setting the stop flag."""
        self.stop_flag = True
        if self.level_meter_thread and self.level_meter_thread.is_alive():
            self.level_meter_thread.join()  # Wait for the thread to finish

        # Reset any other necessary values
        self.current_level = 0.0
        self.filling = True
        self.update_flag = False  # Prevent any further updates

        # Clear the canvas and reset the UI
        self.canvas.delete("all")

    def update_level_meter(self):
        """Background thread that calculates the level updates."""
        while not self.stop_flag:
            # Perform calculations for the level meter
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

            # Set the flag to signal the main thread to update the UI
            self.update_flag = True

            # Sleep for the timer interval before updating again
            time.sleep(self.timer_interval / 1000.0)

    def update_meter(self):
        """This method will be called periodically to update the UI."""
        if self.update_flag:
            self.draw_meter()  # Update the canvas with the current level
            self.update_flag = False  # Reset the flag to prevent constant redrawing
        # Schedule the next update if needed
        self.after(self.timer_interval, self.update_meter)

    def draw_meter(self):
        """Update the level meter on the canvas."""
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
        """Return a color from red to green based on the level value."""
        red = int((1.0 - level) * 255)
        green = int(level * 255)
        return f"#{red:02x}{green:02x}00"

    def play_click(self):
        """Simulate playing a click sound (beep)."""
        pygame.mixer.Sound('boop.wav').play()
        