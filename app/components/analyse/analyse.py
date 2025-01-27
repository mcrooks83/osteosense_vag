from tkinter import Frame, Label, Button
from tkinter.ttk import Combobox

import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)
from modules import processing_pipeline as pp
from modules import data_reader as dr
import numpy as np
import time
import os
import glob

# this screen must replace the stream screen - previously it was a selection from the main canvas
class AnalyseFrame(Frame):
    def __init__(self, master,  s, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.s = s
        # set up a data reader (note: pass in the get_test_file)

        # the cb is to know if a file has been exported correctly (i.e read from the device.) - this will probably become redundant
        self.data_reader = dr.DataReader(s.get_mount_path(), s.get_frame_length(), s.get_export_dir(), self.exported_data)

        self.grid(row=1, column=0, sticky='news',padx=5,pady=5)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.config(bg="black")
        
        # operations frame
        self.operations_frame = Frame(self)
        self.operations_frame.grid(row=0, column=0,  sticky="nsew")
        self.operations_frame.config(bg="black")

        """
        # Create a combobox
        self.usb_combo_label = Label(self.operations_frame, text="select a device path:")
        self.usb_combo_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.usb_port_combo = Combobox(self.operations_frame, values=[])
        self.usb_port_combo.grid(row=0, column=1, padx=10, pady=10)
        self.usb_port_combo.bind("<<ComboboxSelected>>", self.on_usb_port_combo_select)

        self.start_button = Button(self.operations_frame, text="Poll device", command= lambda: self.poll_device())
        self.start_button.grid(row=0, column=2, padx=5,pady=5, sticky="w")
        self.start_button.configure(bg="blue", fg="white")
        self.get_usb_ports()

        self.read_data_button = Button(self.operations_frame, text="Read Data", command= lambda: self.read_device_data())
        self.read_data_button.grid(row=0, column=3, padx=5,pady=5, sticky="w")
        self.read_data_button.configure(bg="blue", fg="white")
        """

        self.file_select_combo_label = Label(self.operations_frame, text="select a file to analyse:", bg="black", fg="white")
        self.file_select_combo_label.grid(row=0, column=4, padx=5, pady=5, sticky="we")
        self.file_select = Combobox(self.operations_frame, values=[], width=50)
        self.file_select.set("Select a file to analyze")  # Set placeholder text
        self.file_select.grid(row=0, column=5, padx=10, pady=10)
        self.file_select.bind("<<ComboboxSelected>>", self.on_file_selected)

        # read the files in exports directories as part of the UX flow for analysing captured data
        current_directory = os.getcwd()
        parent = os.path.abspath(os.path.join(current_directory, os.pardir))
        target_directory = os.path.join(parent, "app", "exports", "recordings") # change to exports only for test data
        target_directory = os.path.normpath(target_directory)  # Normalize the path

        csv_files = glob.glob(os.path.join(target_directory, '*.csv'))
        
        for f in csv_files:
            self.file_select['values'] = (*self.file_select['values'], f.split('\\')[-1])

        #self.selected_file = csv_files[0].split('\\')[-1]
        self.analyse_button = Button(self.operations_frame, text="Analyse", command= lambda: self.analyse(),
                                     borderwidth=0,   
                                        highlightthickness=0,     
                                        font=("Montserrat", 12, "bold"))
        self.analyse_button.grid(row=0, column=6, padx=5,pady=5, sticky="w")
        self.analyse_button.configure(bg="#616CAB", fg="white")

        # information frame
        """
        self.info_frame = Frame(self)
        self.info_frame.grid(row=2, column=0, columnspan=1, sticky="nsew")
        
        self.file_label = Label(self.info_frame, text="file:")
        self.file_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.test_label = Label(self.info_frame, text="")
        self.test_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        self.poll_duration = 5
        self.polling_label = Label(self.info_frame, text="")
        self.polling_label.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        """

        # create a frame to hold outputs
        self.output_frame = Frame(self, bg="black")
        self.output_frame.grid(row=1, column=0,  sticky="nsew", padx=5, pady=5)
        self.output_frame.grid_columnconfigure(0, weight=1)
        self.output_frame.grid_rowconfigure(0, weight=1)

        # figures
        self.fig = Figure(facecolor='black')
        self.f_ax, self.s_ax = self.fig.subplots(nrows=2, ncols=1)
        self.fig.subplots_adjust(hspace=1)  # Increase this value for more space

        # Configure first subplot (Frequency Band Power Contribution)
        self.f_ax.set_title("Frequency Band Power Contribution", color="white")
        self.f_ax.set_ylim(0, 100)
        self.f_ax.set_xlabel("frequency bands", fontsize=8, color="white")
        self.f_ax.set_ylabel("% power [a*2/Hz]", fontsize=8, color="white")
        self.f_ax.xaxis.set_ticks_position('bottom')
        self.f_ax.yaxis.set_ticks_position('left')
        self.f_ax.autoscale(True)
        self.f_ax.set_facecolor("black")
        self.f_ax.spines['bottom'].set_color('white')
        self.f_ax.spines['left'].set_color('white')
        self.f_ax.tick_params(axis='x', colors='white')
        self.f_ax.tick_params(axis='y', colors='white')

        # Configure second subplot (Spectrogram)
        self.s_ax.set_title("Spectrogram", color="white")
        self.s_ax.set_xlabel("time", fontsize=8, color="white")
        self.s_ax.set_ylabel("frequency", fontsize=8, color="white")
        self.s_ax.xaxis.set_ticks_position('bottom')
        self.s_ax.yaxis.set_ticks_position('left')
        self.s_ax.autoscale(False)
        self.s_ax.set_facecolor("black")
        self.s_ax.spines['bottom'].set_color('white')
        self.s_ax.spines['left'].set_color('white')
        self.s_ax.tick_params(axis='x', colors='white')
        self.s_ax.tick_params(axis='y', colors='white')

        # Add the figure to the Tkinter canvas
        self.fig_canvas = FigureCanvasTkAgg(self.fig, master=self.output_frame)
        self.fig_canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        self.spectrogram_cb = None



        #self.read_and_process_test_file()
    def read_device_data(self):
        #check there is a mount path first
        self.data_reader.poll_and_convert()

    def analyse(self):
        self.read_and_process_test_file(self.selected_file)
    
    def on_file_selected(self, event):
        self.selected_file = self.file_select.get()

    def get_usb_ports(self):
        mount_points = self.data_reader.get_usb_mount_points()
        for m in mount_points:
            self.usb_port_combo['values'] = (*self.usb_port_combo['values'], m)
            
    def on_usb_port_combo_select(self, event):
        selected_usb_port = self.usb_port_combo.get()
        self.s.set_mount_path(selected_usb_port)
        print(selected_usb_port)

    def exported_data(self, data, path_to_csv):
        self.file_select['values'] = (*self.file_select['values'], path_to_csv)

    def plot_spectrogram(self, frequencies, times, Sxx):
        #if self.spectrogram_cb is not None:
        #    self.spectrogram_cb.remove()

        #print(Sxx.shape)
        print("Sxx min:", np.min(Sxx), "Sxx max:", np.max(Sxx))
        print("fmax", np.max(frequencies), "fmin", np.min(frequencies))

        # Plot the spectrogram using imshow
        self.im = self.s_ax.imshow(Sxx, aspect='auto', origin='lower', cmap='inferno', extent=[times[0], times[-1], frequencies[0], frequencies[-1]])
        self.s_ax.set_xlim([times[0], times[-1]])  # Adjust to the time limits of the latest spectrogram
        self.s_ax.set_ylim([frequencies[0], frequencies[-1]])  # Adjust to the frequency limits of the latest spectrogram
        
        # Add a colorbar to the spectrogram
        self.spectrogram_cb = self.fig.colorbar(self.im, ax=self.s_ax, label="Intensity (dB)")

        # Redraw the figure canvas to update the plot
        self.fig_canvas.draw()

    # probably could reduce to one plot function
    """
    def plot_f_band1_spectogram(self, frequencies, times, Zxx):
        if(self.f_band1_cb != None):
            self.f_band1_cb.remove()

        cax = self.f_band1_ax.pcolormesh(times, frequencies, Zxx, shading='gouraud', cmap="viridis")
        self.f_band1_cb = self.f_band1_spectogram.colorbar(cax, ax=self.f_band1_ax, label="Intensity")
        self.f_band1_ax.set_ylim(self.s.get_f_band1()[0], self.s.get_f_band1()[1])
        self.fig_canvas.draw()
        
    
    def plot_f_band2_spectogram(self, frequencies, times, Zxx):
        if(self.f_band2_cb != None):
            self.f_band2_cb.remove()

        cax = self.f_band2_ax.pcolormesh(times, frequencies, Zxx, shading='gouraud', cmap="viridis")
        self.f_band2_cb = self.f_band2_spectogram.colorbar(cax, ax=self.f_band2_ax, label="Intensity")
        self.f_band2_ax.set_ylim(self.s.get_f_band2()[0], self.s.get_f_band2()[1])
        self.f_band2_spectogram_canvas.draw()
    """

    def plot_f_bands(self, intervals, f_percentages):
        self.f_ax.clear()
        bars = self.f_ax.bar(intervals, f_percentages, color="c")
        self.f_ax.tick_params(axis='x', labelrotation=90, labelsize=6)

        for bar in bars:
            yval = round(bar.get_height(),2)
            self.f_ax.text(bar.get_x() + bar.get_width()/2, yval, f'{yval}', ha='center', va='bottom', fontsize=6)
        self.fig_canvas.draw()

    def update_poll(self):
        self.usb_port_combo['values'] = []
        self.usb_port_combo.set('')
        devices = self.data_reader.get_usb_mount_points()
        print(f"devices found: {devices}")
        for m in devices:
           self.usb_port_combo['values'] = (*self.usb_port_combo['values'], m)

        # call itself after one seconds
        self.poll_duration = self.poll_duration - 1
        if(self.poll_duration > 0):
            print(self.poll_duration)
            self.after(1000, self.update_poll)
        else:
            self.polling_label.config(text="")
        
    def poll_device(self):
        self.poll_duration = 5
        self.polling_label.config(text="polling for 5 seconds")
        print("polling for devices")
        self.after(1000, self.update_poll)

    # manual read of file
    def read_and_process_test_file(self, file):
        #self.test_label["text"]= self.s.get_test_file()
        self.test_label = file
        #path = f"{self.s.get_export_dir()}{file}"
        path = f"{self.s.get_export_dir()}/recordings/{file}"
        self.vag_df = pp.read_file(path)

        x,y,z,a_mag = pp.extract_axes(self.vag_df)
        bp_filter_settings = self.s.get_filter_settings_for_bandpass()
        spectogram_settings = self.s.get_spectogram_settings()
        intervals, f_percentages = pp.compute_frequency_band_percentages(50, a_mag, bp_filter_settings)
        frequencies, times, Sxx = pp.compute_spectogram(a_mag, bp_filter_settings, spectogram_settings)
        # these are very similar and could be multiprocessed
        #f_band1, times_band1, Zxx_band1 = pp.compute_freq_band_spectogram_from_stft(a_mag, bp_filter_settings, spectogram_settings, self.s.get_f_band1())
        #f_band2, times_band2, Zxx_band2 = pp.compute_freq_band_spectogram_from_stft(a_mag, bp_filter_settings, spectogram_settings, self.s.get_f_band2())
        self.plot_f_bands(intervals, f_percentages)
        self.plot_spectrogram(frequencies, times, Sxx)
        #self.plot_f_band1_spectogram(f_band1, times_band1, Zxx_band1)
        #self.plot_f_band2_spectogram(f_band2, times_band2, Zxx_band2)
