from tkinter import  Frame,Label, Button, NORMAL, DISABLED, IntVar, Checkbutton
from tkinter.ttk import Combobox
from matplotlib.pyplot import Figure
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,NavigationToolbar2Tk)
from matplotlib import style
import collections
from modules import data_streamer as ds
from modules import serial_interface as si
import serial.tools.list_ports


class StreamFrame(Frame):
    def __init__(self, master,  s, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.s = s
        
        self.grid(row=1, column=0,rowspan=1,columnspan=1, sticky='news',padx=5,pady=5)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((3,4), weight=1)

        # operations frame
        self.operations_frame = Frame(self)
        self.operations_frame.grid(row=2, column=0, columnspan=1, sticky="nsew")

        # Create a combobox
        self.usb_port_combo = Combobox(self.operations_frame, values=[])
        self.usb_port_combo.grid(row=0, column=0, padx=10, pady=10)
        self.usb_port_combo.bind("<<ComboboxSelected>>", self.on_usb_port_combo_select)
        self.get_usb_ports()

        self.log_var = IntVar()
        
        # Create radio buttons to switch frames
        self.log_rb = Checkbutton(self.operations_frame, text="log", onvalue=1, offvalue=0, variable = self.log_var, command=self.set_log)
        self.log_rb.grid(row=0,column=1,pady=5, sticky="w")

        # start stream button
        self.start_button = Button(self.operations_frame, text="Start Streaming", state=DISABLED, command= lambda: self.start_stream())
        self.start_button.grid(row=0, column=2, padx=5,pady=5, sticky="w")
        self.start_button.configure(bg="blue", fg="white")

        #stop stream button
        self.stop_button = Button(self.operations_frame, text="Stop Streaming", command= lambda: self.stop_stream())
        self.stop_button.grid(row=0, column=3, padx=5,pady=5, sticky="w")
        self.stop_button.configure(bg="orange", fg="white")

        self.identify_button = Button(self.operations_frame, text="Identify", command= lambda: self.identify())
        self.identify_button.grid(row=0, column=4, padx=5,pady=5, sticky="w")
        self.identify_button.configure(bg="purple", fg="white")

        self.sensor_name_label = Label(self.operations_frame, text="")
        self.sensor_name_label.grid(row=0, column=5, padx=5, pady=5, sticky="w")


        # set up the data buffers
        self.x_data = collections.deque(maxlen=self.s.get_buffer_size())
        self.y_data = collections.deque(maxlen=self.s.get_buffer_size())
        self.z_data = collections.deque(maxlen=self.s.get_buffer_size())
        self.time_index = collections.deque(maxlen=self.s.get_buffer_size())

        self.gyr_x_data = collections.deque(maxlen=self.s.get_buffer_size())
        self.gyr_y_data = collections.deque(maxlen=self.s.get_buffer_size())
        self.gyr_z_data = collections.deque(maxlen=self.s.get_buffer_size())
        

        # Acceleration
        self.vag_stream = Figure()
        self.ax = self.vag_stream.subplots()
        self.ax.set_title(f"Osteosense VAG Accleration")
        self.ax.set_ylim(-10, 10)
        self.ax.set_xlabel("packet count", fontsize=8)
        self.ax.set_ylabel("acceleration (g)", fontsize=8)

        self.ax.xaxis.set_ticks_position('bottom')
        self.ax.yaxis.set_ticks_position('left')
        self.ax.autoscale(True)
        
        self.vag_stream_canvas = FigureCanvasTkAgg(self.vag_stream, master=self)
        self.vag_stream_canvas.get_tk_widget().grid(row=3, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)

        # Angular Velocity
        self.vag_gry_stream = Figure()
        self.ax1 = self.vag_gry_stream.subplots()
        self.ax1.set_title(f"Osteosense VAG Angular Velocity")
        self.ax1.set_ylim(-10, 10)
        self.ax1.set_xlabel("packet count", fontsize=8)
        self.ax1.set_ylabel("angular velocity (deg/s)", fontsize=8)

        self.ax1.xaxis.set_ticks_position('bottom')
        self.ax1.yaxis.set_ticks_position('left')
        self.ax1.autoscale(True)
        
        self.vag_gry_stream_canvas = FigureCanvasTkAgg(self.vag_gry_stream, master=self)
        self.vag_gry_stream_canvas.get_tk_widget().grid(row=4, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)

        self.ani_is_running = False
        self.ani = None
        self.ani1 = None
        self.data_streamer = None
        self.serial_int = None
        self.sensor_name = ""
        self.start_animation()

    def identify(self):
        message = f"IDENTIFY 1\n"
        self.serial_int.send_message(message)

    def set_log(self):
        if(self.log_var.get() == 0):
            print("setting to not log data")
            self.s.set_log(0)
           
        elif(self.log_var.get() == 1):
            print("setting to log data")
            self.s.set_log(1)
            
    def get_usb_ports(self):
        ports = serial.tools.list_ports.comports()

        for port in ports:
            self.usb_port_combo['values'] = (*self.usb_port_combo['values'], port.device)

    def on_usb_port_combo_select(self, event):
        selected_usb_port = self.usb_port_combo.get()
        self.s.set_usb_port(selected_usb_port)
        self.serial_int = si.SerialInterface(selected_usb_port, self.s.get_baud_rate())
        self.serial_int.open_serial_port()
        message = f"GET_SENSOR_NAME 1\n"
        self.sensor_name = self.serial_int.send_message(message, rsp=1)
        self.sensor_name_label.configure(text=self.sensor_name)
        self.start_button.config(state=NORMAL)

    def reset_buffers(self):
        self.time_index.clear()
        self.x_data.clear()
        self.y_data.clear()
        self.z_data.clear()
        self.gyr_x_data.clear()
        self.gyr_y_data.clear()
        self.gyr_z_data.clear()

    def start_animation(self):
        print(self.ani_is_running)
        if not self.ani_is_running:
            # Stop existing animation if any
            if self.ani:
                self.stop_animation()

            print("starting a new animation")
           
            self.ani = animation.FuncAnimation(
                self.vag_stream,
                self.animate,
                fargs=(self.time_index, self.x_data, self.y_data, self.z_data),
                interval=10
            )

            if(self.s.get_gyr_select()): # if the gyro is selected

                self.ani1 = animation.FuncAnimation(
                    self.vag_gry_stream,
                    self.animate1,
                    fargs=(self.time_index, self.gyr_x_data, self.gyr_y_data, self.gyr_z_data),
                    interval=10
                )

            self.vag_gry_stream_canvas.draw()
            self.vag_stream_canvas.draw()
            self.ani_is_running = True
            return "Animation started"
        else:
            return "Animation already running"

    def stop_animation(self):
        if self.ani and self.ani_is_running:
            self.ani.event_source.stop()  # Stop the event source
            self.ani = None  # Clear the animation instance

            if(self.s.get_gyr_select()):
                self.ani1.event_source.stop()  # Stop the event source
                self.ani1 = None  # Clear the animation instance
            self.ani_is_running = False
            return "Animation stopped"
        return "No animation to stop"
    
    ## TODO:
    ## when the stream is stopped run the analysis pipeline and switch to the analyse component
    def start_stream(self):
        message = f"START_STREAM 1\n"
        self.serial_int.send_message(message)
        print("Starting a new thread...")
        if(self.s.get_usb_port()):
            self.data_streamer = ds.DataStreamer( self.s.get_stream_frame_length(), self.stream_data_callback, self.serial_int.get_serial())
            self.data_streamer.start()
            res = self.start_animation()

    def stop_stream(self):
        message = f"STOP_STREAM 0\n"
        self.serial_int.send_message(message)
        self.data_streamer.stop()
        self.data_streamer.join() 
        self.stop_animation()
        self.reset_buffers()

    def stream_data_callback(self, acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z, t_index):
        self.x_data.append(acc_x)
        self.y_data.append(acc_y)
        self.z_data.append(acc_z)
        if(self.s.get_gyr_select()):
            self.gyr_x_data.append(gyr_x)
            self.gyr_y_data.append(gyr_y)
            self.gyr_z_data.append(gyr_z)
        self.time_index.append(t_index)

    def animate(self, i, tx, accel_x, accel_y, accel_z):
        self.ax.clear()
        self.ax.plot(tx, accel_x, label="x accel", linewidth=1)
        self.ax.plot(tx, accel_y, label="y accel", linewidth=1)
        self.ax.plot(tx, accel_z, label="z accel", linewidth=1)
        self.ax.legend()
        self.ax.grid(True)
        self.ax.set_ylim(-10, 10)
    
    def animate1(self, i, tx, gry_x, gry_y, gry_z):
        self.ax1.clear()
        self.ax1.plot(tx, gry_x, label="x gyr", linewidth=1)
        self.ax1.plot(tx, gry_y, label="y gyr", linewidth=1)
        self.ax1.plot(tx, gry_z, label="z gyr", linewidth=1)
        self.ax1.legend()
        self.ax1.grid(True)
        self.ax1.set_ylim(-10, 10)
