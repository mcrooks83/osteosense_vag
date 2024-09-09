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

class AnalyseFrame(Frame):
    def __init__(self, master,  s, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.s = s
        # set up a data reader (note: pass in the get_test_file)
        self.data_reader = dr.DataReader(s.get_mount_path(), s.get_frame_length(), s.get_export_dir(), self.exported_data)

        self.grid(row=1, column=0,rowspan=1,columnspan=1, sticky='news',padx=5,pady=5)
        self.grid_columnconfigure((0,1), weight=1)
        self.grid_rowconfigure((4,5), weight=1)
        # operations frame
        self.operations_frame = Frame(self)
        self.operations_frame.grid(row=1, column=0, columnspan=5, sticky="nsew")
        #self.operations_frame.config(bg="blue")

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

        
        self.file_select_combo_label = Label(self.operations_frame, text="select a file to analyse:")
        self.file_select_combo_label.grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.file_select = Combobox(self.operations_frame, values=[])
        self.file_select.grid(row=0, column=5, padx=10, pady=10)
        self.file_select.bind("<<ComboboxSelected>>", self.on_file_selected)

        # read the files in exports directories as part of the UX flow for analysing captured data
        current_directory = os.getcwd()
        parent = os.path.abspath(os.path.join(current_directory, os.pardir))
        target_directory = os.path.join(parent, "app/exports")
        csv_files = glob.glob(os.path.join(target_directory, '*.csv'))
        
        for f in csv_files:
            self.file_select['values'] = (*self.file_select['values'], f.split('/')[-1])

        self.selected_file = csv_files[0].split('/')[-1]
        self.analyse_button = Button(self.operations_frame, text="Analyse", command= lambda: self.analyse())
        self.analyse_button.grid(row=0, column=6, padx=5,pady=5, sticky="w")
        self.analyse_button.configure(bg="blue", fg="white")

        # information frame
        self.info_frame = Frame(self)
        self.info_frame.grid(row=2, column=0, columnspan=1, sticky="nsew")
        
        self.file_label = Label(self.info_frame, text="file:")
        self.file_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.test_label = Label(self.info_frame, text="")
        self.test_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        self.poll_duration = 5
        self.polling_label = Label(self.info_frame, text="")
        self.polling_label.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # figure 1
        self.f_band_percent = Figure()
        self.f_ax = self.f_band_percent.subplots()
        self.f_ax.set_title(f"Frequency Band Power Contribution")
        self.f_ax.set_ylim(0, 100)
        
        self.f_ax.set_xlabel("frequency bands", fontsize=8)
        self.f_ax.set_ylabel("% power [a*2/Hz]", fontsize=8)

        self.f_ax.xaxis.set_ticks_position('bottom')
        self.f_ax.yaxis.set_ticks_position('left')
        self.f_ax.autoscale(True)
        
        self.f_band_canvas = FigureCanvasTkAgg(self.f_band_percent, master=self)
        self.f_band_canvas.get_tk_widget().grid(row=4, column=0,  sticky='nsew', padx=5, pady=5)

        # figure 2
        self.spectogram = Figure()
        self.s_ax = self.spectogram.subplots()
        self.s_ax.set_title(f"Spectogram")
        
        self.s_ax.set_xlabel("time", fontsize=8)
        self.s_ax.set_ylabel("frequency", fontsize=8)

        self.s_ax.xaxis.set_ticks_position('bottom')
        self.s_ax.yaxis.set_ticks_position('left')
        self.s_ax.autoscale(True)
        
        self.spectogram_canvas = FigureCanvasTkAgg(self.spectogram, master=self)
        self.spectogram_canvas.get_tk_widget().grid(row=4, column=1,  sticky='nsew', padx=5, pady=5)
        self.spectogram_cb = None

        # figure 3
        self.f_band1_spectogram = Figure()
        self.f_band1_ax = self.f_band1_spectogram.subplots()
        self.f_band1_ax.set_title(f"50-250 Hz Spectogram")
        
        self.f_band1_ax.set_xlabel("time", fontsize=8)
        self.f_band1_ax.set_ylabel("frequency", fontsize=8)

        self.f_band1_ax.xaxis.set_ticks_position('bottom')
        self.f_band1_ax.yaxis.set_ticks_position('left')
        self.f_band1_ax.autoscale(True)
        
        self.f_band1_spectogram_canvas = FigureCanvasTkAgg(self.f_band1_spectogram, master=self)
        self.f_band1_spectogram_canvas.get_tk_widget().grid(row=5, column=0, columnspan=1, sticky='nsew', padx=5, pady=5)
        self.f_band1_cb = None

        # figure 4
        self.f_band2_spectogram = Figure()
        self.f_band2_ax = self.f_band2_spectogram.subplots()
        self.f_band2_ax.set_title(f"250-500 Hz Spectogram")
        
        self.f_band2_ax.set_xlabel("time", fontsize=8)
        self.f_band2_ax.set_ylabel("frequency", fontsize=8)

        self.f_band2_ax.xaxis.set_ticks_position('bottom')
        self.f_band2_ax.yaxis.set_ticks_position('left')
        self.f_band2_ax.autoscale(True)
        self.f_band2_cb = None
        
        self.f_band2_spectogram_canvas = FigureCanvasTkAgg(self.f_band2_spectogram, master=self)
        self.f_band2_spectogram_canvas.get_tk_widget().grid(row=5, column=1, columnspan=1, sticky='nsew', padx=5, pady=5)


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

    def plot_spectogram(self,frequencies, times, Sxx):
        if(self.spectogram_cb != None):
            self.spectogram_cb.remove()

        cax = self.s_ax.pcolormesh(times, frequencies, 10 * np.log10(Sxx), shading='auto', cmap="viridis")
        self.spectogram_cb = self.spectogram.colorbar(cax, ax=self.s_ax, label="Intensity")
        self.spectogram_canvas.draw()

    # probably could reduce to one plot function
    def plot_f_band1_spectogram(self, frequencies, times, Zxx):
        if(self.f_band1_cb != None):
            self.f_band1_cb.remove()

        cax = self.f_band1_ax.pcolormesh(times, frequencies, Zxx, shading='gouraud', cmap="viridis")
        self.f_band1_cb = self.f_band1_spectogram.colorbar(cax, ax=self.f_band1_ax, label="Intensity")
        self.f_band1_ax.set_ylim(self.s.get_f_band1()[0], self.s.get_f_band1()[1])
        self.f_band1_spectogram_canvas.draw()
        
    
    def plot_f_band2_spectogram(self, frequencies, times, Zxx):
        if(self.f_band2_cb != None):
            self.f_band2_cb.remove()

        cax = self.f_band2_ax.pcolormesh(times, frequencies, Zxx, shading='gouraud', cmap="viridis")
        self.f_band2_cb = self.f_band2_spectogram.colorbar(cax, ax=self.f_band2_ax, label="Intensity")
        self.f_band2_ax.set_ylim(self.s.get_f_band2()[0], self.s.get_f_band2()[1])
        self.f_band2_spectogram_canvas.draw()


    def plot_f_bands(self, intervals, f_percentages):
        self.f_ax.clear()
        print("plotting f bands")
        bars = self.f_ax.bar(intervals, f_percentages, color="c")
        self.f_ax.tick_params(axis='x', labelrotation=90, labelsize=6)

        for bar in bars:
            yval = round(bar.get_height(),2)
            self.f_ax.text(bar.get_x() + bar.get_width()/2, yval, f'{yval}', ha='center', va='bottom', fontsize=6)
        self.f_band_canvas.draw()

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
        path = f"{self.s.get_export_dir()}{file}"
        self.vag_df = pp.read_file(path)

        x,y,z,a_mag = pp.extract_axes(self.vag_df)
        bp_filter_settings = self.s.get_filter_settings_for_bandpass()
        spectogram_settings = self.s.get_spectogram_settings()
        intervals, f_percentages = pp.compute_frequency_band_percentages(50, a_mag, bp_filter_settings)
        frequencies, times, Sxx = pp.compute_spectogram(a_mag, bp_filter_settings, spectogram_settings)
        # these are very similar and could be multiprocessed
        f_band1, times_band1, Zxx_band1 = pp.compute_freq_band_spectogram_from_stft(a_mag, bp_filter_settings, spectogram_settings, self.s.get_f_band1())
        f_band2, times_band2, Zxx_band2 = pp.compute_freq_band_spectogram_from_stft(a_mag, bp_filter_settings, spectogram_settings, self.s.get_f_band2())
        self.plot_f_bands(intervals, f_percentages)
        self.plot_spectogram(frequencies, times, Sxx)
        self.plot_f_band1_spectogram(f_band1, times_band1, Zxx_band1)
        self.plot_f_band2_spectogram(f_band2, times_band2, Zxx_band2)
