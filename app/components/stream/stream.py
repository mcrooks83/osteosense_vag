from customtkinter import CTkFrame, CTkButton, NORMAL, DISABLED, IntVar, CTkCheckBox, CTkComboBox

from matplotlib.pyplot import Figure
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)
import collections
from modules import data_streamer as ds
import serial.tools.list_ports
from components.stream import dot_level_meter as lm
from modules import events as e

class StreamFrame(CTkFrame):
    def __init__(self, master, s, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.s = s  # settings

        # create a data streamer
        self.data_streamer = ds.DataStreamer(self.s)
       
        # register listeners - NOTE: listeners could be associted to the same event like subscribing 
        self.data_streamer.add_listener(e.EventName.SENSOR_PACKET, self.on_sensor_packet)
        self.data_streamer.add_listener(e.EventName.VAG_BLOCK,  self.on_vag_block)
        self.data_streamer.add_listener(e.EventName.SPEC_IMG, self.on_spectrogram)
        self.data_streamer.add_listener(e.EventName.ADAPTER_STATUS, self.on_adapter_status)

        self.adapter_status = False
   
        self.master.sensor_status_label.configure(text="not connected", font=("Montserrat", 10, "bold"))
        #self.configure(bg="black")
        self.grid(row=1, column=0, rowspan=1, columnspan=1, sticky='news', padx=5, pady=2)
        self.grid_columnconfigure(0, weight=1)
        self.configure(fg_color="transparent")

        # Create a frame for operations and controls (buttons)
        self.operations_frame = CTkFrame(self, )
        self.operations_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=2)
        self.operations_frame.grid_columnconfigure(0, weight=1)
        self.operations_frame.grid_rowconfigure(0, weight=1) # operations frame
        self.operations_frame.grid_rowconfigure(1, weight=1) # output frame

        # create a frame for the control buttons
        self.ctl_buttons_frame = CTkFrame(self.operations_frame, border_width=0 )
        self.ctl_buttons_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        self.usb_port_combo = CTkComboBox(self.ctl_buttons_frame, values=[], 
                                          dropdown_font=("Montserrat", 12, "bold"),
                                          command=self.on_usb_port_combo_select
                                        )
        self.usb_port_combo.set("Select Port")
        self.usb_port_combo.grid(row=0, column=0, padx=5, pady=2)
        self.scan_usb_ports() # move to serial adapter

        # Start and Stop buttons
        self.poll_device = CTkButton(self.ctl_buttons_frame, text="Find Device", command=lambda: self.scan_usb_ports(),
            border_width=0, 
            corner_radius=10, 
            anchor="center",           # Removes the border 
            font=("Montserrat", 12, "bold")  # Bold font 
        )
        self.poll_device.grid(row=0, column=3, padx=5,  sticky="w")
        #self.poll_device.configure(bg="#1BD3EA", fg="white")

        self.start_button = CTkButton(self.ctl_buttons_frame, text="Start Streaming", state=DISABLED, command=lambda: self.start_stream(),
            border_width=0, 
            anchor="center",  
            font=("Montserrat", 12, "bold")  # Bold font 
        )
        self.start_button.grid(row=0, column=4, padx=10, pady=2, sticky="e")

        self.stop_button = CTkButton(self.ctl_buttons_frame, text="Stop Streaming", command=lambda: self.stop_stream(), 
            border_width=0,             # Removes the border
            font=("Montserrat", 12, "bold")  # Bold font 
        )
        self.stop_button.grid(row=0, column=5, padx=10, pady=2, sticky="e")

        self.sonify_var = IntVar(value=1)

         # starts on and if it is off there is no audio processed
        self.sonify_rb = CTkCheckBox(
            self.ctl_buttons_frame, 
            text="Audio", 
            font=("Montserrat", 12, "bold"),  # Bold font 
            onvalue=1, 
            offvalue=0, 
            variable=self.sonify_var, 
            command=self.set_sonify
        )
        self.sonify_rb.grid(row=0, column=6, padx=10, pady=2, sticky="e")

        self.record_var = IntVar(value=self.s.get_record())
        
        # this will be used to record - it should record the VAG signal rather than the raw data set    
        self.record_cb = CTkCheckBox(self.ctl_buttons_frame, 
            text="record", 
            font=("Montserrat", 12, "bold"),  # Bold font 
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
        self.vag_signal = collections.deque(maxlen=self.s.get_buffer_size()*2)
        self.spectrograms = collections.deque(maxlen=10)  # Store a fixed number of spectrograms'

        # probably better in settings
        self.spec_data_size = 8192  # a number of samples to compute the spectrogtam over.
        self.im = None  # For storing the image object to update later

        self.meter = lm.LevelMeter(self.operations_frame, self.s)
        self.meter.grid(row=2,column=0, padx=10, columnspan=999, pady=20, sticky="nsew")
        self.grid_rowconfigure(3, weight=1, minsize=200)  # Adjust minsize as needed for initial size

        self.output_frame = CTkFrame(self)
        self.output_frame.grid(row=3, column=0, columnspan=1, rowspan=2, 
                               sticky="nsew", padx=5, pady=2)
        self.output_frame.grid_rowconfigure(0, weight=1)  # Make sure the canvas inside expands
        self.output_frame.grid_columnconfigure(0, weight=1)
        
        # figures
        self.fig = Figure(facecolor='#292929') # gray16 like the theme
        
        gs = self.fig.add_gridspec(2, 2, height_ratios=[2, 1])  # First row gets 2x the height of the second row
        # Add subplots: 
        # First row (2 subplots in the first row)
        self.ax1= self.fig.add_subplot(gs[0, 0])  # First subplot
        self.ax2 = self.fig.add_subplot(gs[0, 1])  # Second subplot

        # Second row (1 subplot that spans the full width of the second row)
        self.ax = self.fig.add_subplot(gs[1, :])  # Spans all 3 columns

        # Adjust space between subplots
        self.fig.subplots_adjust(wspace=0.5, hspace=0.5)  # Increase vertical space with hspace

        # Acceleration Graph
        #""""
        self.ax.set_title(f"3D Raw Acceleration", color="#3a7ebf")
        self.ax.set_ylim(-6, 6)
        self.ax.set_facecolor("#292929")
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.spines['top'].set_color("none")
        self.ax.spines['right'].set_color('none')
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
        self.ax1.set_title(f"VAG Signal 100Hz - 1000Hz", color="#3a7ebf")
        self.ax1.set_ylim(-2, 2)
        self.ax1.autoscale(True)
        self.ax1.set_facecolor("#292929")
        self.ax1.spines['bottom'].set_color('white')
        self.ax1.spines['left'].set_color('white')
        self.ax1.spines['top'].set_color("none")
        self.ax1.spines['right'].set_color('none')
        self.ax1.set_xlabel("time", fontsize=10, color="white")
        self.ax1.set_ylabel("acceleration (g)", fontsize=10, color="white")
        self.ax1.xaxis.set_ticks_position('bottom')
        self.ax1.yaxis.set_ticks_position('left')
        self.ax1.tick_params(axis='x', colors='white')
        self.ax1.tick_params(axis='y', colors='white')
        self.ax1.grid(False)

        # power spectrum
        self.ax2.set_title(f"VAG Spectrum", color="#3a7ebf")
        self.ax2.set_facecolor("#292929")
        self.ax2.spines['bottom'].set_color('white')
        self.ax2.spines['left'].set_color('white')
        self.ax2.spines['top'].set_color("none")
        self.ax2.spines['right'].set_color('none')
        self.ax2.set_xlabel("time", fontsize=10, color="white")
        self.ax2.set_ylabel("PSD", fontsize=10, color="white")
        self.ax2.xaxis.set_ticks_position('bottom')
        self.ax2.yaxis.set_ticks_position('left')
        self.ax2.tick_params(axis='x', colors='white')
        self.ax2.tick_params(axis='y', colors='white')

        self.fig_canvas = FigureCanvasTkAgg(self.fig, master=self.output_frame)
        self.fig_canvas.get_tk_widget().grid(row=0, column=0, sticky='news', padx=5, pady=2)

        self.ani_is_running = False
        self.ani = None
        self.ani1 = None
        self.ani2 = None
        self.sensor_name = ""


    def select_position(self):
        print("position selected:", self.position.get())

    def identify(self):
        message = f"IDENTIFY 1\n"

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
    # move this to serial_internface.py? 
    def scan_usb_ports(self):
        ports = serial.tools.list_ports.comports()
        # Create a list to store all USB ports
        usb_ports = []
        # Cross-platform port detection
        for port in ports:
            # Append Linux ACM ports and all ports for Windows/others
            if 'ACM' in port.device or any(platform_key in port.description.lower() for platform_key in ['usb', 'serial']):
                usb_ports.append(port.device)
        self.usb_port_combo.configure(values=list(set(usb_ports)))

    # callback that should be registered with the data streamer
    def on_adapter_status(self, status):
        self.adapter_status = status  
        if(self.adapter_status == True):
            print("should update label")
            self.master.sensor_status_label.configure(text="connected", text_color="green", font=("Montserrat", 10, "bold"))
        else:
            self.master.sensor_status_label.configure(text="disconnected", font=("Montserrat", 10, "bold"))

    def on_usb_port_combo_select(self, event):
        print("combo selected")
        selected_usb_port = self.usb_port_combo.get()
        self.s.set_usb_port(selected_usb_port)
        self.data_streamer.serial_adapter.set_serial_port(self.s.get_usb_port())
        self.start_button.configure(state=NORMAL)

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
    
    ''' start and stop the data streamer'''
    def start_stream(self):
        self.start_button.configure(state=DISABLED)
        if(self.s.get_usb_port()):
            self.data_streamer.start_streamer()
            res = self.start_animation()
            

    def stop_stream(self):
        self.start_button.configure(state=NORMAL)
        self.stop_animation()
        self.reset_buffers()
        self.data_streamer.stop_streamer()
        
    ''' data callbacks '''
    def on_spectrogram(self, img):
        self.spectrograms.append(img)

    def on_vag_block(self, vag):
        self.vag_signal.extend(vag)

    def on_sensor_packet(self, acc_x, acc_y, acc_z, mag, t_index):
        self.x_data.append(acc_x)
        self.y_data.append(acc_y)
        self.z_data.append(acc_z)
        self.mag_data.append(mag)
        self.time_index.append(t_index)

    ''' Figure animation functions '''
    def animate(self, i, tx, accel_x, accel_y, accel_z, mag):
        self.ax.clear()
        self.ax.set_title(f"3D Raw Acceleration", color="#3a7ebf")
        self.ax.plot(tx, accel_x, label="x accel", linewidth=1, color="#1C1F33")
        self.ax.plot(tx, accel_y, label="y accel", linewidth=1, color="#1BD3EA")
        self.ax.plot(tx, accel_z, label="z accel", linewidth=1, color="#616CAB")
        self.ax.plot(tx, mag, label="mag", linewidth=1, color="red")
        self.ax.legend(loc="upper left")
        self.ax.set_ylim(-10, 10)

    def animate1(self, i,  vag):
        self.ax1.clear()
        self.ax1.set_title(f"VAG Signal 100Hz - 1000Hz", color="#3a7ebf")
        self.ax1.plot(vag, label="vag signal", linewidth=1, color="#1BD3EA")
        self.ax1.legend(loc='upper left')
        self.ax1.set_ylim(-4, 4)
    
    def animate2(self, i,  spectrograms):
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

