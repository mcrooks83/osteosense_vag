import dearpygui.dearpygui as dpg
from settings import SettingsComponent as SC
from settings import settings as s
from modules import serial_interface as si # import the serial interface
from modules import audio_processor as ap
from modules import data_streamer as ds
import collections
import time
import numpy as np
from scipy.signal.windows import hann

"""
    settings class is where all settings are kept throughout use

    Next step: create a raw accleration class (window) that will register a callback to the data streamer and plot the data in real time
"""



# main application class
class App:
    def __init__(self, settings):
        self.settings = settings
        self.components = []
        self.windows = {}  # Store windows (ids)

        self.sp = None
        self.audio_processor = None
        self.data_streamer = None

        # example buffers for data
        self.raw_magnitude = collections.deque(maxlen=self.settings.get_buffer_size())
        self.raw_x_accel = collections.deque(maxlen=self.settings.get_buffer_size())
        self.raw_y_accel = collections.deque(maxlen=self.settings.get_buffer_size())
        self.raw_z_accel = collections.deque(maxlen=self.settings.get_buffer_size())
        self.raw_time = collections.deque(maxlen=self.settings.get_buffer_size())

        self.vag_signal = collections.deque(maxlen=self.settings.get_buffer_size()*2) # this buffer should be a multiple of the audio buffer size 1024
        self.vag_time = collections.deque(maxlen=self.settings.get_buffer_size())
        self.dt = 1 / 3000 # time step (i.e data rate / samping frequency)

        self.spectrograms = collections.deque(maxlen=10)  # Store a fixed number of spectrograms'
        self.spec_data_size = 8192  # a number of samples to compute the spectrogtam over.
        self.segment_length = 1024
        self.hann_window = hann(self.segment_length)
        self.overlap = self.segment_length // 2  # 50% overlap
        self.im = None  # For storing the image object to update later
        self.heatmap_values = np.zeros((50, 100))
    
    
    def toggle_window(self, window_name):
        """ Show or hide windows dynamically """
        if window_name in self.windows:
            is_visible = dpg.is_item_shown(self.windows[window_name])
            dpg.configure_item(self.windows[window_name], show=not is_visible)

    def recieve_raw_data(self, mag, x, y, z, time_count):
        self.raw_magnitude.append(mag)
        self.raw_x_accel.append(x)
        self.raw_y_accel.append(y)
        self.raw_z_accel.append(z)
        self.raw_time.append(time_count)
        self.update_raw_accel_window()

    def recieve_vag_signal(self, signal):
        
        self.vag_signal.extend(signal) 
        self.update_vag_signal_window()

        # compute spectogram 
        if len(self.vag_signal) >= self.spec_data_size:
            signal_data = np.array(self.vag_signal)[-self.spec_data_size:]
            spec_image = self.data_streamer.compute_spectrogram(signal_data)
            self.spectrograms.append(spec_image)
            #self.update_spectrogram_window()
    
    def update_spectrogram_window(self):
        spec_image = self.spectrograms[-1]
        # Resize or trim if necessary
        # Update the texture
        dpg.set_value(self.heat_series, spec_image)
    
    def update_vag_signal_window(self):
        dpg.set_value("vag_tag", (list(range(len(self.vag_signal))), list(self.vag_signal)))

        #dpg.set_value('vag_tag', (list(self.vag_time), list(self.vag_signal)))
        dpg.fit_axis_data("vag_x_axis")
        dpg.fit_axis_data("vag_y_axis")

    def update_raw_accel_window(self):
        dpg.set_value('raw_mag_tag', (list(self.raw_time), list(self.raw_magnitude)))
        dpg.set_value('raw_x_tag', (list(self.raw_time), list(self.raw_x_accel)))
        dpg.set_value('raw_y_tag', (list(self.raw_time), list(self.raw_y_accel)))
        dpg.set_value('raw_z_tag', (list(self.raw_time), list(self.raw_z_accel)))
        dpg.fit_axis_data("x_axis")
        dpg.fit_axis_data("y_axis")

    def setup(self):
        print("running app setup")

        """ setup the serial port and data streamer """
        self.sp = si.SerialInterface("COM4", self.settings.get_baud_rate()) # opens the port on creation
        # NOTE: should close the serial port when we are done with it 

        self.audio_processor = ap.AudioProcessor(self.settings)

        # no need to pass individual settings as the whole class is being passed in.
        self.data_streamer = ds.DataStreamer(self.settings, 
                                             self.settings.get_conversion_4g(), 
                                             self.settings.get_stream_frame_length(), 
                                             self.sp.get_serial(),
                                             self.audio_processor)
        

        #register the callbacks before we do anything else.
        self.data_streamer.register_raw_acceleration_cb(self.recieve_raw_data)
        self.data_streamer.register_vag_signal_cb(self.recieve_vag_signal)
        
        #self.serial_int.open_serial_port()

        """ Initialize and display all components dynamically """
        dpg.create_viewport(title="My DPG App", resizable=True)  # Allow resizing
        dpg.maximize_viewport()  # Fullscreen the viewport

        dpg.setup_dearpygui()
        dpg.show_viewport()

        ## add the menu
        with dpg.viewport_menu_bar():
            with dpg.menu(label="Settings"):
                pass
                #dpg.add_menu_item(label="Settings", callback=lambda: self.toggle_window("Settings"))
                #dpg.add_menu_item(label="Raw accleration") # add to callback
            with dpg.menu(label="About"):
                pass
            

        # Now get fullscreen size
        screen_width = dpg.get_viewport_width()
        screen_height = dpg.get_viewport_height()
        #print(f"screen height: {screen_height} screen width: {screen_width}")
        self.settings.set_screen_dimensions(screen_width, screen_height)

        """  Test plottig raw acceleration axes + magnitude in a window """
        with dpg.window(label='Raw Accleration Signal', tag='win',width=800, height=600):

            with dpg.plot(label='Line Series', height=-1, width=-1):
                # optionally create legend
                dpg.add_plot_legend()

                # REQUIRED: create x and y axes, set to auto scale.
                x_axis = dpg.add_plot_axis(dpg.mvXAxis, label='time', tag='x_axis')
                y_axis = dpg.add_plot_axis(dpg.mvYAxis, label='Accleration', tag='y_axis')


                # series belong to a y axis. Note the tag name is used in the update
                # function update_data
                dpg.add_line_series(x=list(self.raw_time), y=list(self.raw_magnitude), 
                            label='Magnitude', parent='y_axis', 
                            tag='raw_mag_tag')
                dpg.add_line_series(x=list(self.raw_time), y=list(self.raw_x_accel), 
                            label='Accel X', parent='y_axis', 
                            tag='raw_x_tag')
                dpg.add_line_series(x=list(self.raw_time), y=list(self.raw_y_accel), 
                            label='Accel Y', parent='y_axis', 
                            tag='raw_y_tag')
                dpg.add_line_series(x=list(self.raw_time), y=list(self.raw_z_accel), 
                            label='Accel Z', parent='y_axis', 
                            tag='raw_z_tag')
                
        """ Test plotting the VAG signal """
        with dpg.window(label='VAG Signal', tag='vag_win',width=800, height=600):

            with dpg.plot(label='VAG Signal', height=-1, width=-1):
                # optionally create legend
                dpg.add_plot_legend()
                
                # REQUIRED: create x and y axes, set to auto scale.
                x_axis = dpg.add_plot_axis(dpg.mvXAxis, label='time', tag='vag_x_axis')
                y_axis = dpg.add_plot_axis(dpg.mvYAxis, label='VAG Accleration', tag='vag_y_axis')
                dpg.set_axis_limits("vag_y_axis", -4, 4)

                dpg.add_line_series(x=list(self.vag_time), y=list(self.vag_signal), 
                            label='VAG Signal', parent='vag_y_axis', 
                            tag='vag_tag')
        

        """ Test plot the spectrograms 
        with dpg.window(label="Spectrogram Window", width=800, height=600):
            with dpg.plot(label="Spectrogram", height=400, width=600):
                dpg.add_plot_axis(dpg.mvXAxis, label="Time", tag="t_axis")
                with dpg.plot_axis(dpg.mvYAxis, label="Frequency", tag="f_axis"):
                    self.heat_series = dpg.add_heat_series(self.heatmap_values, rows=50, cols=100, scale_min=0, scale_max=1)
        """

        # start the stream
        self.audio_processor.start()
        self.data_streamer.start()  # starts the stream
        

        # test control window
        #with dpg.window(label="Control Window", width=-1, height=100, pos=(0, 10), no_move=True, no_resize=False, no_collapse=True):
        #    dpg.add_text("Application Controls")
            
        
                    
             # Create footer
            #with dpg.child_window(width=dpg.get_viewport_width(), height=40, pos=(0, dpg.get_viewport_height() - 75)):
            #    dpg.add_text("Footer Text")

            # Make sure footer stays at the bottom

            #dpg.set_item_pos(dpg.last_item(), (0, dpg.get_viewport_height() - 50))
                    
        # this creates another window (this is the concept of Dear Py GUI)
        # we can use child windows to nest windows or groupings or tabs)
        """
        with dpg.window(label="Main Window", width=500, height=400, pos=(20, 20)):
            dpg.add_text("Device Selection", color=(255, 200, 0, 255))  # Section title
            
            # Group to align dropdown & button
            with dpg.group(horizontal=True):
                dpg.add_combo([], tag="device_combo", width=200, default_value="Select a Device")
                dpg.add_button(label="Find Devices", callback=self.find_device_callback)  # Button next to dropdown
        """
        # create an instance of the component
        #settings_component = SC.Settings(self.settings)
        # add to a list of components
        #self.components.extend([settings_component])
        #self.windows["Settings"] = settings_component.create() # create the settings window


        # Global UI elements
        
        #with dpg.window(label="Status", width=300, height=100, pos=(screen_width // 4, screen_height -800)):
        #    dpg.add_text("", tag="status_text")

    def run(self):
        """ Start the DPG UI loop """
        dpg.create_context()
        # docking configurations can be saved and loadied from init_files 
        dpg.configure_app(docking=True, docking_space=True) # must be called before create_viewport
        self.setup()
        #dpg.start_dearpygui()
        while dpg.is_dearpygui_running():
            # Render the frame and process any events
            dpg.render_dearpygui_frame()

            #time.sleep(0.05)  # Wait for 50ms before next update

        dpg.destroy_context()

    def find_device_callback(self):
        pass


# Run the app
if __name__ == "__main__":
    app_settings = s.Settings()
    app = App(app_settings) # pass settings class into the App class
    app.run()
