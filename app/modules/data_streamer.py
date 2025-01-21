import serial
from modules import convert as con
import threading
import os
from datetime import datetime
from scipy.signal import butter, filtfilt, resample, lfilter
import csv
import numpy as np


class DataStreamer(threading.Thread):
    def __init__(self, settings,  conversion, frame_length, cb, vag_cb, ser, gyr, audio_processor):
        super().__init__()
        #self.port_name = port_name
        #self.baud_rate = baud_rate
        self.s = settings
        self.conversion = conversion
        self.frame_length = frame_length
        self.ser = ser
        self.running = True
        self.cb = cb # stream callback to display data
        self.vag_cb = vag_cb
        self.row_count = 0
        self.log = 0
        self.log_filename = ""
        self.gyr = gyr
        self.audio_processor = audio_processor # so we can put data on it
        self.audio_buffer = []  # Buffer for storing a chunk of vag data to pass to the audio_processor
        self.buffer_size = 512
        # create a bandpass filter
        filter_settings = self.s.get_filter_settings_for_bandpass()
        b, a = butter(filter_settings["filter_order"], [filter_settings["low_cut_off"], filter_settings["high_cut_off"]], btype='bandpass', fs=filter_settings["sampling_rate"])
        self.b = b
        self.a = a
        self.chunk = []

    def get_audio_buffer_size(self):
        return self.buffer_size

    def filter_input_stream(self,data):
        return filtfilt(self.b, self.a, data)

    def create_log_file(self):
        current_directory = os.getcwd()
        parent = os.path.abspath(os.path.join(current_directory, os.pardir))
        self.target_directory = os.path.join(parent, "app/exports/logs/")
        print(f"log files will be output to {self.target_directory}")

        # set up the log file
        if(self.log == 1):
            current_datetime = datetime.now()
            self.log_filename = f"{current_datetime.strftime('%d%m%Y%H%M')}_log.csv"
            self.file_path = os.path.join(self.target_directory, self.log_filename)

            # Check if the file exists
            file_exists = os.path.isfile(self.file_path)

            try:
                # Open the file in append mode
                with open(self.file_path, "a", newline="") as file:
                    writer = csv.writer(file)
                    # Write the header only if the file does not exist
                    if not file_exists:
                        writer.writerow(["packet_count", "X", "Y", "Z"])
                print(f"File '{self.file_path}' created and header written.")

            except Exception as e:
                print(f"An error occurred: {e}")

    def set_logging(self, log):
        self.log = log   # 1 = log data to csv

    def set_log_filename(self, filename):
        self.log_filename = filename

    def run(self):
        #self.ser = self.open_serial_port()
        if self.ser:
            while self.running:
                self.poll_usb_port()
            #self.close_serial_port()

    def poll_usb_port(self):
            try:
                if self.ser.in_waiting > 0:
                    row = self.ser.read(self.frame_length)
                    acc_x, acc_y, acc_z, mag = con.simple_convert(row, self.conversion, self.gyr )
                    
                    # put raw data on UI
                    self.cb(acc_x, acc_y, acc_z, mag, self.row_count)
                    self.row_count = self.row_count + 1

                    self.audio_buffer.append(mag)  # Store the sample in the buffer

                    if len(self.audio_buffer) >= self.buffer_size:
                        self.chunk = np.array(self.audio_buffer[:self.buffer_size])  # Take the first buffer_size samples
                        self.audio_buffer = self.audio_buffer[self.buffer_size:]  # Remove the processed samples

                        # band pass filter
                        self.chunk = self.filter_input_stream(self.chunk)
                        self.vag_cb(self.chunk)

                    # send the magnitude to audio queue (this also filters like vag so is reproduced)
                    # only do this is sonfiy is selected
                    if(self.s.get_sonify_select()==1):
                        
                        self.audio_processor.data_queue.put(self.chunk)

                    # write data to csv if logging is set
                    if(self.log == 1):
                        with open(self.file_path, "a", newline="") as file:
                            writer = csv.writer(file)
                            # Write new data to the CSV file
                            writer.writerow([self.row_count, acc_x, acc_y, acc_z])


            except serial.SerialException as e:
                print(f"Error during polling: {e}")

    def stop(self):
        self.running = False
