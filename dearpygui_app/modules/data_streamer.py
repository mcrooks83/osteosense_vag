import serial
from modules import convert as con
import threading
import queue
import os
from datetime import datetime
from scipy.signal import butter, filtfilt
import csv
import numpy as np
from scipy.signal import stft
from scipy.signal.windows import hann
import pywt

"""
This class requires windows that use it to register callbacks.
To ensure that they are implemented an abstract class can be used in window creation
for now we will assume that the windows are setup correctly

the class uses the following:

settings
conversion (value to use in converting binary to readable values)
frame_lenght (stream frame length)
ser serial port (created from si.SerialInterface(selected_usb_port, self.s.get_baud_rate()))

"""
class DataStreamer(threading.Thread):
    def __init__(self, settings,  conversion, frame_length, ser, audio_processor):
        super().__init__()
        self.s = settings
        self.conversion = conversion
        self.frame_length = frame_length
        self.ser = ser # serial port

        self.running = True

        # callbacks
        self.raw_acceleration_cb = None
        self.vag_signal_cb = None

        self.row_count = 0
        self.gyr = 0 # this just means the gyr is not enabled (we dont need it for now)

        self.audio_processor = audio_processor # so we can put data on it
        self.audio_buffer = []  # Buffer for storing a chunk of vag data to pass to the audio_processor
        self.buffer_size = settings.get_audio_buffer_size()

        # create a bandpass filter
        filter_settings = self.s.get_filter_settings_for_bandpass()
        b, a = butter(filter_settings["filter_order"], [filter_settings["low_cut_off"], filter_settings["high_cut_off"]], btype='bandpass', fs=filter_settings["sampling_rate"])
        self.b = b
        self.a = a
        self.chunk = []

        # spectrogram
        # probably better in settings
        self.spec_data_size = 8192  # a number of samples to compute the spectrogtam over in the streaming 
        self.segment_length = 1024
        self.hann_window = hann(self.segment_length)
        self.overlap = self.segment_length // 2  # 50% overlap

        # Queue for CSV writing
        self.csv_queue = queue.Queue()
        self.csv_thread = None  # Writer thread placeholder
        self.recording_active = False  # Tracking recording state (this is probably a duplicate of the record setting)
        self.file_path = None

    # callbacks that are required to be registered
    def register_raw_acceleration_cb(self, cb):
        self.raw_acceleration_cb = cb

    def register_vag_signal_cb(self, cb):
        self.vag_signal_cb = cb

    def start_csv_writer(self):
        """Start the CSV writing thread if not already running."""
        if not self.recording_active:
            self.recording_active = True
            self.create_record_file()
            self.csv_thread = threading.Thread(target=self.csv_writer, daemon=True)
            self.csv_thread.start()
            print("CSV writer thread started.")

    def stop_csv_writer(self):
        """Stop the CSV writing thread if running."""
        if self.recording_active:
            self.recording_active = False
            self.csv_queue.put(None)  # Signal the writer thread to exit
            if self.csv_thread:
                self.csv_thread.join()
                self.csv_thread = None
            print("CSV writer thread stopped.")

    def csv_writer(self):
        """Background thread for writing CSV data."""
        while self.recording_active or not self.csv_queue.empty():
            try:
                row = self.csv_queue.get(timeout=1)
                with open(self.file_path, "a", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow(row)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"CSV writing error: {e}")

    def compute_spectrogram(self, signal_data):
        #Compute the STFT (using scipy's stft function)
        # get the samping rate from settings not hardcoded
        f, t, Zxx = stft(signal_data, fs=3000, nperseg=self.segment_length,  noverlap=self.overlap)

        # Convert the complex STFT to magnitude for the spectrogram
        Sxx = np.abs(Zxx)
        spectrogram_image = np.uint8(255 * (Sxx / np.max(Sxx)))  # Normalize to [0, 255]

        #return ((f,t,Sxx))
        return spectrogram_image

    def get_audio_buffer_size(self):
        return self.buffer_size

    def filter_input_stream(self,data):
        return filtfilt(self.b, self.a, data)
    
    # original settings = db4 soft
    def wavelet_denoise(self, signal, wavelet='db4', level=3, method="Default"):
        # wavelet db4 coif5 sym8 (not much difference)
        coeffs = pywt.wavedec(signal, wavelet, mode="per")

        # Estimate noise sigma using the MAD method (from the detail coefficients at the finest level)
        sigma = np.median(np.abs(coeffs[-1])) / 0.6745 
        # Use different thresholding strategies
        if method == 'BayesShrink':
            threshold = sigma
        elif method == 'Universal':
            threshold = np.sqrt(2 * np.log(len(signal))) * sigma
        elif method == 'Default':  # Default to manual std-based thresholding
            threshold = np.std(coeffs[-level])

        # mode hard soft
        coeffs = [pywt.threshold(c, threshold, mode="soft") for c in coeffs]
        return pywt.waverec(coeffs, wavelet, mode="per")

    # when a file is created the csv writer thread is also started
    def create_record_file(self):
        current_directory = os.getcwd()
        parent = os.path.abspath(os.path.join(current_directory, os.pardir))
        self.target_directory = os.path.join(parent, "app/exports/recordings/")
        print(f"recordings will be output to {self.target_directory}")

        current_datetime = datetime.now()
        record_file_name = f"{current_datetime.strftime('%d%m%Y%H%M')}_recording.csv"
        self.file_path = os.path.join(self.target_directory, record_file_name)

        # Check if the file exists
        file_exists = os.path.isfile(self.file_path)

        try:
            # Open the file in append mode
            with open(self.file_path, "a", newline="") as file:
                writer = csv.writer(file)
                # Write the header only if the file does not exist
                if not file_exists:
                    writer.writerow(["packet_count", "acc_x", "acc_y", "acc_z", "a_mag"])
            print(f"File '{self.file_path}' created and header written.")

            # start csv writer thread
            self.start_csv_writer()

            # return true if successful
            return True

        except Exception as e:
            print(f"An error occurred: {e}")
            self.stop_csv_writer()
            # return false on some error
            return False


    def run(self):
        if self.ser:
            while self.running:
                self.poll_usb_port()

    def poll_usb_port(self):
            try:
                if self.ser.in_waiting > 0:
                    row = self.ser.read(self.frame_length)
                    acc_x, acc_y, acc_z, mag = con.simple_convert(row, self.conversion, self.gyr )
                    self.raw_acceleration_cb(mag, acc_x, acc_y, acc_z, self.row_count)
                    
                    self.row_count = self.row_count + 1

                    self.audio_buffer.append(mag)  # Store the sample in the buffer

                    # deal with the vag signal
                    if len(self.audio_buffer) >= self.buffer_size:
                        self.chunk = np.array(self.audio_buffer[:self.buffer_size])  # Take the first buffer_size samples
                        self.audio_buffer = self.audio_buffer[self.buffer_size:]  # Remove the processed samples

                        # band pass filter
                        self.chunk = self.filter_input_stream(self.chunk) #* 10
                        #self.chunk = self.wavelet_denoise(self.chunk)
                        self.vag_signal_cb(self.chunk)

                        self.audio_processor.data_queue.put(self.chunk)

                    # write data to csv if logging is set
                    # do this based on settings
                    # this is a slow and perhaps should be off loaded to a new thread?
                    """
                    if(self.s.get_record() == 1):
                        with open(self.file_path, "a", newline="") as file:
                            writer = csv.writer(file)
                            # Write new data to the CSV file
                            writer.writerow([self.row_count, acc_x, acc_y, acc_z, mag])
                    """

            except serial.SerialException as e:
                print(f"Error during polling: {e}")

    def stop(self):
        self.running = False
        self.stop_csv_writer()
