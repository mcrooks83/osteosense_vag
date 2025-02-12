from tkinter import  Frame, Button, NORMAL, DISABLED, IntVar, StringVar, Checkbutton, Radiobutton
from tkinter.ttk import Combobox, Style
from matplotlib.pyplot import Figure
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)
import collections
from modules import data_streamer as ds
from modules import serial_interface as si # serial port operations including sending messages to the device
import serial.tools.list_ports
from modules import audio_processor as ap
import numpy as np
from scipy.signal import  stft
from scipy.signal.windows import hann
from components.stream import dot_level_meter as lm

class StreamFrame(Frame):
    def __init__(self, master, s, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.s = s  # settings
        print("record flag state:", self.s.get_record()) # state of record flag
        self.configure(bg="black")
        self.grid(row=1, column=0, rowspan=1, columnspan=1, sticky='news', padx=5, pady=2)
        self.grid_columnconfigure(0, weight=1)

        # Create a frame for operations and controls (buttons)
        self.operations_frame = Frame(self, bg="black")
        self.operations_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=2)
        self.operations_frame.grid_columnconfigure(0, weight=1)
        self.operations_frame.grid_rowconfigure(0, weight=1) # operations frame
        self.operations_frame.grid_rowconfigure(1, weight=1) # output frame

        # create a frame for the control buttons
        self.ctl_buttons_frame = Frame(self.operations_frame, bg="black")
        self.ctl_buttons_frame.grid(row=0, column=0, sticky="ew")

        # Create a combobox for USB ports
        # Create a style for the Combobox
        style = Style()
        style.configure("TCombobox", 
                        fieldbackground="white",  # Background of the text field
                        background="white",       # Dropdown background
                        foreground="white",
                        font=("Montserrat", 12, "bold")
                        )
        style.configure("TCombobox.Listbox",
                background="white",       # Background of the dropdown list
                foreground="#616CAB",       # Text color of list items
                font=("Montserrat", 12, "bold")
                )

        self.usb_port_combo = Combobox(self.ctl_buttons_frame, values=[], style="TCombobox")
        #self.usb_port_combo = Combobox(self.ctl_buttons_frame, values=[])
        self.usb_port_combo.grid(row=0, column=0, padx=5, pady=2)
        self.usb_port_combo.bind("<<ComboboxSelected>>", self.on_usb_port_combo_select)
        self.get_usb_ports()

        #self.sensor_name_label = Label(self.operations_frame, text="")
        #self.sensor_name_label.grid(row=0, column=1, padx=5, pady=2, sticky="w")

        # Start and Stop buttons
        self.poll_device = Button(self.ctl_buttons_frame, text="Find Device", command=lambda: self.get_usb_ports(),
            borderwidth=0,             # Removes the border
            highlightthickness=0,      # Removes the highlight border  
            font=("Montserrat", 12, "bold")  # Bold font 
        )
        self.poll_device.grid(row=0, column=3, padx=5,  sticky="w")
        self.poll_device.configure(bg="#1BD3EA", fg="white")

        self.start_button = Button(self.ctl_buttons_frame, text="Start Streaming", state=DISABLED, command=lambda: self.start_stream(),
            borderwidth=0,             # Removes the border
            highlightthickness=0,      # Removes the highlight border  
            font=("Montserrat", 12, "bold")  # Bold font 
        )
        self.start_button.grid(row=0, column=4, padx=10, pady=2, sticky="e")
        self.start_button.configure(bg="#616CAB", fg="white")

        self.stop_button = Button(self.ctl_buttons_frame, text="Stop Streaming", command=lambda: self.stop_stream(), 
            borderwidth=0,             # Removes the border
            highlightthickness=0,      # Removes the highlight border  
            font=("Montserrat", 12, "bold")  # Bold font 
        )
        self.stop_button.grid(row=0, column=5, padx=10, pady=2, sticky="e")
        self.stop_button.configure(bg="#F3F2F7", fg="#5A72ED")

        self.sonify_var = IntVar(value=1)

         # starts on and if it is off there is no audio processed
        self.sonify_rb = Checkbutton(
            self.ctl_buttons_frame, 
            borderwidth=0,             # Removes the border
            highlightthickness=0,      # Removes the highlight border
            text="sonify", 
            bg="black", 
            fg="white",          # Text color
            font=("Montserrat", 12, "bold"),  # Bold font 
            activebackground="black",  # Prevents gray background on hover
            activeforeground="white",  # Keeps text white on hover
            selectcolor="#616CAB",  # Checkbox background color when selected
            onvalue=1, 
            offvalue=0, 
            variable=self.sonify_var, 
            command=self.set_sonify
        )
        self.sonify_rb.grid(row=0, column=6, padx=10, pady=2, sticky="e")

        self.record_var = IntVar(value=self.s.get_record())
        
        # this will be used to record - it should record the VAG signal rather than the raw data set    
        self.record_cb = Checkbutton(self.ctl_buttons_frame, 
                                   borderwidth=0,             # Removes the border
            highlightthickness=0,      # Removes the highlight border
            text="record", 
            bg="black", 
            fg="white",          # Text color
            font=("Montserrat", 12, "bold"),  # Bold font 
            activebackground="black",  # Prevents gray background on hover
            activeforeground="white",  # Keeps text white on hover
            selectcolor="#616CAB",  # Checkbox background color when selected
            onvalue=1, offvalue=0, variable=self.record_var, command=self.set_record)
        self.record_cb.grid(row=0, column=7, padx=10, pady=2, sticky="e")

        #self.identify_button = Button(self.operations_frame, text="Identify", command=lambda: self.identify())
        #self.identify_button.grid(row=0, column=6, padx=5, pady=2, sticky="w")
        #self.identify_button.configure(bg="purple", fg="white")

        # Create data buffers
        self.x_data = collections.deque(maxlen=self.s.get_buffer_size())
        self.y_data = collections.deque(maxlen=self.s.get_buffer_size())
        self.z_data = collections.deque(maxlen=self.s.get_buffer_size())
        self.mag_data = collections.deque(maxlen=self.s.get_buffer_size())
        self.time_index = collections.deque(maxlen=self.s.get_buffer_size())
        self.vag_signal = collections.deque(maxlen=self.s.get_buffer_size()*2) # twice the buffer size so that we can compute a spectrogram
        self.spectrograms = collections.deque(maxlen=10)  # Store a fixed number of spectrograms'

        # probably better in settings
        self.spec_data_size = 8192  # a number of samples to compute the spectrogtam over.
        self.segment_length = 1024
        self.hann_window = hann(self.segment_length)
        self.overlap = self.segment_length // 2  # 50% overlap
        self.im = None  # For storing the image object to update later

        self.meter = lm.LevelMeter(self.operations_frame)
        self.meter.grid(row=2,column=0, padx=10, columnspan=999, pady=20, sticky="nsew")

        """
        self.positions_frame = Frame(self.operations_frame, bg="black")
        self.positions_frame.grid(row=1, column=0, sticky="ew", pady=20,)


        self.position = StringVar(self, "")

        self.ml_rb = Radiobutton(self.positions_frame, text="medial", value="m", variable = self.position, 
                                     command=self.select_position, bg="black", fg="white",
                                     font=("Montserrat", 14), 
                                     selectcolor="#616CAB",
                                     anchor="w", 
                                     borderwidth=0,             # Removes the border
                                     highlightthickness=0,      # Removes the highlight border  
                                     )
        self.ml_rb.grid(row=0,column=0,pady=2, sticky="w", padx=5)

        self.pat_rb = Radiobutton(self.positions_frame, text="patella", value="p", variable = self.position, 
                                     command=self.select_position, bg="black", fg="white",
                                     font=("Montserrat", 14), 
                                     selectcolor="#616CAB",
                                     anchor="w", 
                                     borderwidth=0,             # Removes the border
                                     highlightthickness=0,      # Removes the highlight border  
                                     )
        self.pat_rb.grid(row=0,column=1,pady=2, sticky="w", padx=5)

        self.l_rb = Radiobutton(self.positions_frame, text="lateral", value="l", variable = self.position, 
                                     command=self.select_position, bg="black", fg="white",
                                     font=("Montserrat", 14), 
                                     selectcolor="#616CAB",
                                     anchor="w", 
                                     borderwidth=0,             # Removes the border
                                     highlightthickness=0,      # Removes the highlight border  
                                     )
        self.l_rb.grid(row=0,column=2,pady=2, sticky="w", padx=5)
        """
        self.output_frame = Frame(self, bg="black")
        self.output_frame.grid(row=3, column=0, columnspan=1, sticky="nsew", padx=5, pady=2)
        self.output_frame.grid_columnconfigure(0, weight=1)

        # figures
        self.fig = Figure(facecolor='black')
        self.ax, self.ax1, self.ax2 = self.fig.subplots(nrows=1, ncols=3)
        self.fig.subplots_adjust(wspace=0.5)  # Increase this value for more space

        """
            code to rearrange the figures 

            gs = self.fig.add_gridspec(nrows=2, ncols=2, height_ratios=[1, 1])  # Define grid with 2 rows, 2 columns

            # Top row: A single subplot spanning both columns
            self.top_ax = self.fig.add_subplot(gs[0, :])  # Span across both columns

            # Bottom row: Two separate subplots
            self.bottom_left_ax = self.fig.add_subplot(gs[1, 0])
            self.bottom_right_ax = self.fig.add_subplot(gs[1, 1])
        """

        # Acceleration Graph
        #""""
        self.ax.set_title(f"3D Raw Acceleration", color="white")
        self.ax.set_ylim(-6, 6)
        self.ax.set_facecolor("black")
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.set_xlabel("packet count", fontsize=10, color="white")
        self.ax.set_ylabel("acceleration (g)", fontsize=10, color="white")
        self.ax.xaxis.set_ticks_position('bottom')
        self.ax.yaxis.set_ticks_position('left')
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.autoscale(False)
        self.ax.grid(False)
        
        #"""
        # Vag signal
        self.ax1.set_title(f"VAG Signal 100Hz - 1000Hz")
        self.ax1.set_ylim(-2, 2)
        self.ax1.autoscale(True)
        self.ax1.set_facecolor("black")
        self.ax1.spines['bottom'].set_color('white')
        self.ax1.spines['left'].set_color('white')
        self.ax1.set_xlabel("time", fontsize=10, color="white")
        self.ax1.set_ylabel("acceleration (g)", fontsize=10, color="white")
        self.ax1.xaxis.set_ticks_position('bottom')
        self.ax1.yaxis.set_ticks_position('left')
        self.ax1.tick_params(axis='x', colors='white')
        self.ax1.tick_params(axis='y', colors='white')
        self.ax1.grid(False)

        # power spectrum
        self.ax2.set_title(f"VAG Spectrum")
        self.ax2.set_facecolor("black")
        self.ax2.spines['bottom'].set_color('white')
        self.ax2.spines['left'].set_color('white')
        self.ax2.set_xlabel("time", fontsize=10, color="white")
        self.ax2.set_ylabel("PSD", fontsize=10, color="white")
        self.ax2.xaxis.set_ticks_position('bottom')
        self.ax2.yaxis.set_ticks_position('left')
        self.ax2.tick_params(axis='x', colors='white')
        self.ax2.tick_params(axis='y', colors='white')

        self.fig_canvas = FigureCanvasTkAgg(self.fig, master=self.output_frame)
        self.fig_canvas.get_tk_widget().grid(row=0, column=0, sticky='new', padx=5, pady=2)

        """
        self.vag_stream_canvas = FigureCanvasTkAgg(self.vag_stream, master=self.output_frame)
        self.vag_stream_canvas.get_tk_widget().grid(row=0, column=0,  sticky='nesw', padx=5, pady=2)

        self.vag_sonify_stream_canvas = FigureCanvasTkAgg(self.vag_sonify_stream, master=self.output_frame)
        self.vag_sonify_stream_canvas.get_tk_widget().grid(row=0, column=1, sticky='nsew', padx=5, pady=2)

        self.vag_heatmap_stream_canvas = FigureCanvasTkAgg(self.vag_spectrum_stream, master=self.output_frame)
        self.vag_heatmap_stream_canvas.get_tk_widget().grid(row=0, column=2, sticky='nsew', padx=5, pady=2)
        """

        self.ani_is_running = False
        self.ani = None
        self.ani1 = None
        self.ani2 = None
        self.data_streamer = None
        self.serial_int = None
        self.sensor_name = ""

    def select_position(self):
        print("position selected:", self.position.get())

    def identify(self):
        message = f"IDENTIFY 1\n"
        #self.serial_int.send_message(message)

    def set_record(self):
        if(self.record_var.get() == 0):
            print("setting to not log data")
            self.s.set_record(0) # on settings class
           
        elif(self.record_var.get() == 1):
            print("setting to log data")
            self.s.set_record(1)

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
        #self.serial_int.open_serial_port()
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
            
            self.ani = animation.FuncAnimation(
                self.fig,
                self.animate,
                cache_frame_data=True,
                save_count = 10,
                fargs=(self.time_index, self.x_data, self.y_data, self.z_data, self.mag_data),
                interval=10,
                blit=False, # Turning on Blit
            )
            
            self.ani1 = animation.FuncAnimation(
                self.fig,
                self.animate1,
                cache_frame_data=True,
                save_count = 10,
                fargs=( self.vag_signal, ),
                interval=10,
                blit=False, # Turning on Blit
            )
            
            # spectogram
            self.ani2 = animation.FuncAnimation(
               self.fig,  # graph to update
               self.animate2, # function callback
               cache_frame_data=True,
               save_count = 10,
               fargs=( self.spectrograms, ),
               interval=10,
               blit=False, # Turning on Blit
            )

            self.fig_canvas.draw()
            
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
        self.start_button.config(state=DISABLED)
        
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
            
            # if the record flag is set then create a file and then start streaming
            # what happens if the file fails to create..do we stream still or alert user?
            if(self.s.get_record() == 1):
                file_created = self.data_streamer.create_record_file()
                if(file_created):
                    self.data_streamer.start()
                else:
                    print("failed to create record file")
            else:
                self.data_streamer.start()

            res = self.start_animation()

    def stop_stream(self):
        self.start_button.config(state=NORMAL)
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
        if len(self.vag_signal) >= self.spec_data_size: # spec_data_size is 8192 
            signal_data = np.array(self.vag_signal)[-self.spec_data_size:]
            spec_image = self.data_streamer.compute_spectrogram(signal_data)
            self.spectrograms.append(spec_image)

    def stream_data_callback(self, acc_x, acc_y, acc_z, mag, t_index):
        self.x_data.append(acc_x)
        self.y_data.append(acc_y)
        self.z_data.append(acc_z)
        self.mag_data.append(mag)
        self.time_index.append(t_index)

    # animate functions that may be blocking.
    def animate(self, i, tx, accel_x, accel_y, accel_z, mag):
        self.ax.clear()
        self.ax.plot(tx, accel_x, label="x accel", linewidth=1, color="#1C1F33")
        self.ax.plot(tx, accel_y, label="y accel", linewidth=1, color="#1BD3EA")
        self.ax.plot(tx, accel_z, label="z accel", linewidth=1, color="#616CAB")
        self.ax.plot(tx, mag, label="mag", linewidth=1, color="red")
        self.ax.legend()
        self.ax.set_ylim(-10, 10)

    def animate1(self, i,  vag):
        self.ax1.clear()
        self.ax1.plot(vag, label="vag signal", linewidth=1, color="#1BD3EA")
        self.ax1.legend()
        self.ax1.set_ylim(-4, 4)
    
    def animate2(self, i,  spectrograms):
        #self.ax2.clear()
        if not spectrograms:
            return
        
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

