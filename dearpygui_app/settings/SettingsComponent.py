import dearpygui.dearpygui as dpg

class Settings:
    def __init__(self, settings):
        self.settings = settings
        self.window = None

    def create(self):
        with dpg.window(label="Settings", width=400, height=self.settings.get_screen_dimensions()[1]) as self.window:
        
            dpg.add_spacer(height=15)  # Add space before next section
            dpg.add_separator()  # Adds a line to separate sections
            dpg.add_spacer(height=15)  # Another space for clarity

            # USB port settings
            with dpg.collapsing_header(label="USB Port Settings", default_open=False):
                dpg.add_combo(["9600", "115200", "256000"], label="Select Baud Rate", default_value=self.settings.get_baud_rate(), callback=self.on_baud_change)
              
             # Filter Settings
            with dpg.collapsing_header(label="Bandpass Filter Settings", default_open=False):
                dpg.add_slider_int(label="low cut off ", default_value=self.settings.get_low_cut_off(), 
                                   min_value=10, max_value=500, callback=self.on_low_cut_off_change)
                dpg.add_slider_int(label="high cut off ", default_value=self.settings.get_high_cut_off(), 
                                   min_value=500, max_value=2000, callback=self.on_high_cut_off_change)
                dpg.add_input_int(label="filter order", default_value=self.settings.get_filter_order(), min_value=2, max_value=6, callback=self.on_filter_order_change)

            
            # settings to consider
            # spectrogram - seg_length, overlap, method?
            # audio_buffer 1024 (used for audio processor and vag signal)
            # BUFFER_SIZE 10000 number of data points to keep for display
            # conversions (set the conversion) -> 4g 8g etc (useful when the sensor can be configured)
            # stream length (currently uses only accelerometer but could add gryro)
            # sensors (as above)
            # sonfiy or audify (choose a method?)
            
            
            # test button to update another window
            #dpg.add_button(label="Click Me", callback=self.on_button_click)
        return self.window

    def on_button_click(self, sender, app_data):
        pass
        # this is updating a text field with the tag status_text
        #dpg.set_value("status_text", "Button Settings clicked!")

    def on_baud_change(self, sender, app_data):
        self.settings.set_baud_rate = app_data

    def on_low_cut_off_change(self, sender, app_data):
        # result should be less than the high cut off that is currently set
        self.settings.set_low_cut_off(app_data)
    
    def on_high_cut_off_change(self, sender, app_data):
        self.settings.set_high_cut_off(app_data)
    
    def on_filter_order_change(self, sender, app_data):
        self.settings.set_filter_order(app_data)

