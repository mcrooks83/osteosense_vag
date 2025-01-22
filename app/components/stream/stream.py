from tkinter import  Frame,Label, Button, NORMAL, DISABLED, IntVar, Checkbutton
from tkinter.ttk import Combobox
import matplotlib
from matplotlib.pyplot import Figure
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,NavigationToolbar2Tk)
from matplotlib import style

import collections
from modules import data_streamer as ds
from modules import serial_interface as si # serial port operations including sending messages to the device
import serial.tools.list_ports
from modules import audio_processor as ap
import numpy as np
from scipy.signal import spectrogram, stft
from scipy.signal.windows import hann
#from components.stream import level_meter as lm
from components.stream import dot_level_meter as lm
import threading


class StreamFrame(Frame):
    def __init__(self, master, s, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.s = s  # settings
        
        self.grid(row=0, column=0, rowspan=1, columnspan=1, sticky='news', padx=5, pady=5)
        self.grid_columnconfigure(0, weight=1)

        # Create a frame for operations and controls (buttons)
        self.operations_frame = Frame(self)
        self.operations_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.operations_frame.grid_columnconfigure(0, weight=1)
        self.operations_frame.grid_rowconfigure(0, weight=1)
        self.operations_frame.grid_rowconfigure(1, weight=1)
        self.operations_frame.grid_rowconfigure(2, weight=1)  # Ensure row 2 expands

        # create a frame for the control buttons
        self.ctl_buttons_frame = Frame(self.operations_frame)
        self.ctl_buttons_frame.grid(row=0, column=0, sticky="w")

        # Create a combobox for USB ports
        self.usb_port_combo = Combobox(self.ctl_buttons_frame, values=[])
        self.usb_port_combo.grid(row=0, column=0, padx=10, pady=5)
        self.usb_port_combo.bind("<<ComboboxSelected>>", self.on_usb_port_combo_select)
        self.get_usb_ports()

        #self.sensor_name_label = Label(self.operations_frame, text="")
        #self.sensor_name_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        self.log_var = IntVar()
        self.sonify_var = IntVar(value=1)

        # this will be used to record - it should record the VAG signal rather than the raw data set    
        #self.log_rb = Checkbutton(self.operations_frame, text="log", onvalue=1, offvalue=0, variable=self.log_var, command=self.set_log)
        #self.log_rb.grid(row=0, column=2, pady=5, sticky="w")

        # Start and Stop buttons
        self.poll_device = Button(self.ctl_buttons_frame, text="Find Device", command=lambda: self.get_usb_ports())
        self.poll_device.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.poll_device.configure(bg="red", fg="white")

        self.start_button = Button(self.ctl_buttons_frame, text="Start Streaming", state=DISABLED, command=lambda: self.start_stream())
        self.start_button.grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.start_button.configure(bg="blue", fg="white")

        self.stop_button = Button(self.ctl_buttons_frame, text="Stop Streaming", command=lambda: self.stop_stream())
        self.stop_button.grid(row=0, column=5, padx=5, pady=5, sticky="w")
        self.stop_button.configure(bg="orange", fg="white")

         # starts on and if it is off there is no audio processed
        self.sonify_rb = Checkbutton(self.ctl_buttons_frame, text="sonify", onvalue=1, offvalue=0, variable=self.sonify_var, command=self.set_sonify)
        self.sonify_rb.grid(row=0, column=6, pady=5, sticky="w")

        #self.identify_button = Button(self.operations_frame, text="Identify", command=lambda: self.identify())
        #self.identify_button.grid(row=0, column=6, padx=5, pady=5, sticky="w")
        #self.identify_button.configure(bg="purple", fg="white")

        # Create data buffers
        self.x_data = collections.deque(maxlen=self.s.get_buffer_size())
        self.y_data = collections.deque(maxlen=self.s.get_buffer_size())
        self.z_data = collections.deque(maxlen=self.s.get_buffer_size())
        self.mag_data = collections.deque(maxlen=self.s.get_buffer_size())
        self.time_index = collections.deque(maxlen=self.s.get_buffer_size())
        self.vag_signal = collections.deque(maxlen=self.s.get_buffer_size())
        self.spectrograms = collections.deque(maxlen=20)  # Store a fixed number of spectrograms'

        # probably better in settings
        self.spec_data_size = 8192  # a number of samples to compute the spectrogtam over.
        self.segment_length = 1024
        self.hann_window = hann(self.segment_length)
        self.overlap = self.segment_length // 2  # 50% overlap
        self.im = None  # For storing the image object to update later

        self.meter = lm.LevelMeter(self.operations_frame)
        self.meter.grid(row=1, column=0, padx=10, columnspan=999, pady=50, sticky="nsew")

        # Acceleration Graph
        #""""
        self.vag_stream = Figure(facecolor='black')
        self.ax = self.vag_stream.subplots()
        self.ax.set_title(f"3D Raw Acceleration",)
        self.ax.set_ylim(-6, 6)
        self.ax.set_facecolor("black")
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.set_xlabel("packet count", fontsize=8, color="white")
        self.ax.set_ylabel("acceleration (g)", fontsize=8, color="white")
        self.ax.xaxis.set_ticks_position('bottom')
        self.ax.yaxis.set_ticks_position('left')
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.autoscale(False)
        
        #"""
        # Vag signal
        self.vag_sonify_stream = Figure(facecolor='black')
        self.ax1 = self.vag_sonify_stream.subplots()
        self.ax1.set_title(f"VAG Signal 100Hz - 1000Hz")
        self.ax1.set_ylim(-2, 2)
        self.ax1.set_xlabel("packet count", fontsize=8)
        self.ax1.set_ylabel("(g)", fontsize=8)
        self.ax1.xaxis.set_ticks_position('bottom')
        self.ax1.yaxis.set_ticks_position('left')
        self.ax1.autoscale(True)
        self.ax1.set_facecolor("black")
        self.ax1.spines['bottom'].set_color('white')
        self.ax1.spines['left'].set_color('white')
        self.ax1.set_xlabel("packet count", fontsize=8, color="white")
        self.ax1.set_ylabel("acceleration (g)", fontsize=8, color="white")
        self.ax1.xaxis.set_ticks_position('bottom')
        self.ax1.yaxis.set_ticks_position('left')
        self.ax1.tick_params(axis='x', colors='white')
        self.ax1.tick_params(axis='y', colors='white')

        # power spectrum
        self.vag_spectrum_stream = Figure(facecolor='black')
        self.ax2 = self.vag_spectrum_stream.subplots()
        self.ax2.set_title(f"VAG Spectrum")
        self.ax2.set_xlabel("t", fontsize=8)
        self.ax2.set_ylabel("Sxx", fontsize=8)
        self.ax2.set_facecolor("black")
        self.ax2.spines['bottom'].set_color('white')
        self.ax2.spines['left'].set_color('white')
        self.ax2.set_xlabel("packet count", fontsize=8, color="white")
        self.ax2.set_ylabel("acceleration (g)", fontsize=8, color="white")
        self.ax2.xaxis.set_ticks_position('bottom')
        self.ax2.yaxis.set_ticks_position('left')
        self.ax2.tick_params(axis='x', colors='white')
        self.ax2.tick_params(axis='y', colors='white')

        # graph frame
        self.output_frame = Frame(self.operations_frame, bg="black")
        self.output_frame.grid(row=3, column=0, columnspan=1, sticky="nsew", padx=5, pady=5)
        self.output_frame.grid_columnconfigure(0, weight=1)
        self.output_frame.grid_columnconfigure(1, weight=1)
        self.output_frame.grid_columnconfigure(2, weight=1)

        self.vag_stream_canvas = FigureCanvasTkAgg(self.vag_stream, master=self.output_frame)
        self.vag_stream_canvas.get_tk_widget().grid(row=0, column=0,  sticky='nesw', padx=5, pady=5)

        self.vag_sonify_stream_canvas = FigureCanvasTkAgg(self.vag_sonify_stream, master=self.output_frame)
        self.vag_sonify_stream_canvas.get_tk_widget().grid(row=0, column=1, sticky='nsew', padx=5, pady=5)

        self.vag_heatmap_stream_canvas = FigureCanvasTkAgg(self.vag_spectrum_stream, master=self.output_frame)
        self.vag_heatmap_stream_canvas.get_tk_widget().grid(row=0, column=2, sticky='nsew', padx=5, pady=5)

        self.ani_is_running = False
        self.ani = None
        self.ani1 = None
        self.ani2 = None
        self.data_streamer = None
        self.serial_int = None
        self.sensor_name = ""

    def identify(self):
        message = f"IDENTIFY 1\n"
        #self.serial_int.send_message(message)

    def set_log(self):
        if(self.log_var.get() == 0):
            print("setting to not log data")
            self.s.set_log(0)
           
        elif(self.log_var.get() == 1):
            print("setting to log data")
            self.s.set_log(1)

    def set_sonify(self):
        if(self.sonify_var.get() == 0):
            self.s.set_sonify_select(0)
           
        elif(self.sonify_var.get() == 1):
            self.s.set_sonify_select(1)
            
    # will only detect the sensor when it is connected
    # move this to serial_internface.py
    def get_usb_ports(self):
        ports = serial.tools.list_ports.comports()
        # Create a list to store all USB ports
        usb_ports = []

        # Cross-platform port detection
        for port in ports:
            # Append Linux ACM ports and all ports for Windows/others
            if 'ACM' in port.device or any(platform_key in port.description.lower() for platform_key in ['usb', 'serial']):
                usb_ports.append(port.device)

        # Remove duplicates and update the combo box
        self.usb_port_combo['values'] = list(set(usb_ports))

        # Debug output for verification
        print("USB ports added to combo box:", self.usb_port_combo['values'])
            

    def on_usb_port_combo_select(self, event):
        selected_usb_port = self.usb_port_combo.get()
        self.s.set_usb_port(selected_usb_port)
        self.serial_int = si.SerialInterface(selected_usb_port, self.s.get_baud_rate())
        self.serial_int.open_serial_port()
        message = f"GET_SENSOR_NAME 1\n"
        #self.sensor_name = self.serial_int.send_message(message, rsp=1)
        #self.sensor_name_label.configure(text=self.sensor_name)
        self.start_button.config(state=NORMAL)

    def reset_buffers(self):
        self.time_index.clear()
        self.x_data.clear()
        self.y_data.clear()
        self.z_data.clear()
        self.mag_data.clear()
        self.vag_signal.clear()

    def start_animation(self):
        self.meter.start_level_meter() # starts the level meter
        if not self.ani_is_running:
            # Stop existing animation if any
            if self.ani:
                self.stop_animation()

            print("starting a new animation")
            
            self.ani = animation.FuncAnimation(
                self.vag_stream,
                self.animate,
                cache_frame_data=True,
                save_count = 10,
                fargs=(self.time_index, self.x_data, self.y_data, self.z_data, self.mag_data),
                interval=10,
                blit=False, # Turning on Blit
            )
            

            self.ani1 = animation.FuncAnimation(
                self.vag_sonify_stream,
                self.animate1,
                cache_frame_data=True,
                save_count = 10,
                fargs=( self.vag_signal, ),
                interval=10,
                blit=False, # Turning on Blit
            )
            
            # spectogram
            self.ani2 = animation.FuncAnimation(
               self.vag_spectrum_stream,  # graph to update
               self.animate2, # function callback
               cache_frame_data=True,
               save_count = 10,
               fargs=( self.spectrograms, ),
               interval=10,
               blit=False, # Turning on Blit
            )

            # these are required for the graph to show
            self.vag_sonify_stream_canvas.draw()
            self.vag_heatmap_stream_canvas.draw()
            self.vag_stream_canvas.draw()
            
            
            self.ani_is_running = True

            return "Animation started"
        else:
            return "Animation already running"

    def stop_animation(self):
        # ani1 is the filter vag signal and so should always be present
        if self.ani1 and self.ani_is_running:

            # stop the level meter
            self.meter.stop_level_meter()
            
            if(self.ani):
                self.ani.event_source.stop()  # Stop the event source
                self.ani = None  # Clear the animation instance

            # this is the vag signal 
            self.ani1.event_source.stop()  # Stop the event source
            self.ani1 = None  # Clear the animation instance
            
            # this is the heatmap
            self.ani2.event_source.stop()  # Stop the event source
            self.ani2 = None  # Clear the animation instance
            self.ani_is_running = False

            return "Animation stopped"
        
        return "No animation to stop"
    
    def start_stream(self):
        
        message = f"START_STREAM 1\n"
        #self.serial_int.send_message(message)
        print("Starting a new thread...")
        if(self.s.get_usb_port()):
            print(f"sonify select: {self.s.get_sonify_select()}")

            # create an audio processor
            self.audio_processor = ap.AudioProcessor(self.s)

            if(self.s.get_sonify_select()==1):    
                self.audio_processor.start()

            # conversion factor should be accessed and passed
            # may need a UI component to alter this in the future
            # VAG is 4G 3.3kHz
            self.data_streamer = ds.DataStreamer(self.s, self.s.get_conversion_4g(), self.s.get_stream_frame_length(), 
                                                self.stream_data_callback, self.vag_stream_callback,
                                                self.serial_int.get_serial(),
                                                  self.s.get_sonify_select(), self.audio_processor)
            self.data_streamer.start()

            res = self.start_animation()

    def stop_stream(self):
        if(self.s.get_sonify_select()==1): 
            self.audio_processor.stop()
            self.audio_processor.join()
        message = f"STOP_STREAM 0\n"
        #self.serial_int.send_message(message)
        self.data_streamer.stop()
        self.data_streamer.join() 
        self.stop_animation()
        self.reset_buffers()
        

    def vag_stream_callback(self, vag):
        self.vag_signal.extend(vag)
        
        # compute spectogram 
        if len(self.vag_signal) >= self.spec_data_size:
            signal_data = np.array(self.vag_signal)[-self.spec_data_size:]
            spec_image = self.data_streamer.compute_spectrogram(signal_data)
            self.spectrograms.append(spec_image)

    # make a callback - not used now as this is computed on a thread in data_streamer
    def compute_spectrogram(self):
        print("i am called but shouldnt be")
        signal_data = np.array(self.vag_signal)[-self.spec_data_size:]

        #Compute the STFT (using scipy's stft function)
        f, t, Zxx = stft(signal_data, fs=3300, nperseg=self.segment_length,  noverlap=self.overlap)

        # Convert the complex STFT to magnitude for the spectrogram
        Sxx = np.abs(Zxx)

        # Store the spectrogram in the deque (limit the number of stored spectrograms)
        self.spectrograms.append((f, t, Sxx))
        #self.spectrograms.append(spectrogram)


    def stream_data_callback(self, acc_x, acc_y, acc_z, mag, t_index):
        self.x_data.append(acc_x)
        self.y_data.append(acc_y)
        self.z_data.append(acc_z)
        self.mag_data.append(mag)
        self.time_index.append(t_index)

    # animate functions that may be blocking.
    def animate(self, i, tx, accel_x, accel_y, accel_z, mag):
        self.ax.clear()
        self.ax.plot(tx, accel_x, label="x accel", linewidth=1)
        self.ax.plot(tx, accel_y, label="y accel", linewidth=1)
        self.ax.plot(tx, accel_z, label="z accel", linewidth=1)
        self.ax.plot(tx, mag, label="mag", linewidth=1)
        self.ax.legend()
        self.ax.grid(True)
        self.ax.set_ylim(-10, 10)

    def animate1(self, i,  vag):
        self.ax1.clear()
        self.ax1.plot(vag, label="vag signal", linewidth=1)
        self.ax1.legend()
        self.ax1.grid(True)
        self.ax1.set_ylim(-4, 4)
    
    def animate2(self, i,  spectrograms):
        #self.ax2.clear()
        if not spectrograms:
            return

        # Get the last spectrogram (most recent one)
        f, t, Sxx = spectrograms[-1]

        # Update the plot with the new spectrogram
        if self.im is None:
            self.im = self.ax2.imshow(Sxx, aspect='auto', origin='lower', cmap='inferno', 
                                     extent=[t[0], t[-1], f[0], f[-1]])
            self.ax2.set_xlabel("Time [s]")
            self.ax2.set_ylabel("Frequency [Hz]")
        else:
            self.im.set_data(Sxx)

        # Optionally, adjust the plot to fit more spectrograms as new ones come in
        self.ax2.set_xlim([t[0], t[-1]])  # Adjust to the time limits of the latest spectrogram
        self.ax2.set_ylim([f[0], f[-1]])  # Adjust to the frequency limits of the latest spectrogram

