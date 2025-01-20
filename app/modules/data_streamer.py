import serial
from modules import convert as con
import threading
import os
from datetime import datetime
from scipy.signal import butter, filtfilt, resample, lfilter
import csv


class DataStreamer(threading.Thread):
    def __init__(self, settings,  conversion, frame_length, cb, ser, gyr, audio_processor):
        super().__init__()
        #self.port_name = port_name
        #self.baud_rate = baud_rate
        self.s = settings
        self.conversion = conversion
        self.frame_length = frame_length
        self.ser = ser
        self.running = True
        self.cb = cb # stream callback to display data
        self.row_count = 0
        self.log = 0
        self.log_filename = ""
        self.gyr = gyr
        self.audio_processor = audio_processor # so we can put data on it


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
                    
                    self.cb(acc_x, acc_y, acc_z, mag, self.row_count)

                    # send the magnitude to audio queue (this also filters like vag so is reproduced)
                    self.audio_processor.data_queue.put(mag)

                    self.row_count = self.row_count + 1

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
