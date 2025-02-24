from modules import convert as con
import threading
import queue
import os
from datetime import datetime
from scipy.signal import butter, filtfilt, detrend
import csv
import numpy as np
from scipy.signal import  stft
from collections import defaultdict, deque

# modules
from adapters import serial_adapter as sa
from modules import audio_processor as ap
from modules import events as events

""" 
    the DataStreamer handles the adapter
    It converts the raw binary rows and returns sensor packets and also a chunk of filtered data for VAG.
    It pass the chunk to an audio processor should it be set
    callbacks that must be registered 

    1. on_sensor_packet (raw data packet) 
    2. on_vag_block (chunk of vag data)
    3. on_adapter_status (connection status of the adatper)

"""
class DataStreamer():
    # the callbacks will be removed
    def __init__(self, settings ):
        super().__init__()
        self.daemon = True
        self.s = settings # application settings

        self.serial_adapter = sa.SerialAdapter(self.s.get_baud_rate(), self.on_serial_port_status, self.on_adpater_data) # this callback is wrong for now
        self.serial_port = None # this is the serial port that allows the polling 
        self.serial_port_status = False

        self.listeners = defaultdict(dict)

        self.conversion = self.s.get_conversion_4g() # this is a converstion constant 
        self.frame_length = self.s.get_stream_frame_length() 

        self.running = True

        self.row_count = 0
        self.audio_buffer = []  # Buffer for storing a chunk of vag data to pass to the audio_processor
        self.buffer_size = settings.get_audio_buffer_size()  # 1024

        # create a bandpass filter - potentiall want to do this on the fly
        filter_settings = self.s.get_filter_settings_for_bandpass()
        b, a = butter(filter_settings["filter_order"], [filter_settings["low_cut_off"], filter_settings["high_cut_off"]], btype='bandpass', fs=filter_settings["sampling_rate"])
        self.b = b
        self.a = a
        self.chunk = []

        # spectrogram 
        self.spec_data_size = self.s.get_spec_size()  
        self.spec_buffer = deque(maxlen=self.s.get_buffer_size()*2)

        # Queue for CSV writing
        self.csv_queue = queue.Queue()
        self.csv_thread = None  # Writer thread placeholder
        self.recording_active = False  # Tracking recording state (this is probably a duplicate of the record setting)
        self.file_path = None

        self.audio_processor = ap.AudioProcessor(self.s)   # assumes that there will be one created
        self.data_streamer_thread = None

    # register listeners function to add all the callbacks required for the datastreamer
    def add_listener(self, event_name: str, listener): # listener is a function and could be typed as a Callable
        self.listeners[event_name] = listener

    # on_serial_port_status_cb 
    def on_serial_port_status(self, value):
        self.serial_port_status = value
        self.listeners[events.EventName.ADAPTER_STATUS](self.serial_port_status)

    def start_csv_writer(self):
        """Start the CSV writing thread if not already running."""
        if not self.recording_active:
            self.recording_active = True
            #self.create_record_file()
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


    def get_audio_buffer_size(self):
        return self.buffer_size

    def filter_input_stream(self,data):
        return filtfilt(self.b, self.a, data)
    
    def create_record_file(self):
        current_directory = os.getcwd()
        parent = os.path.abspath(os.path.join(current_directory, os.pardir))
        self.target_directory = os.path.join(parent, "app/exports/recordings/")
        print(f"recordings will be output to {self.target_directory}")

        current_datetime = datetime.now()
        record_file_name = f"{current_datetime.strftime('%d%m%Y%H%M')}_recording.csv"
        self.file_path = os.path.join(self.target_directory, record_file_name)
        file_exists = os.path.isfile(self.file_path)

        try:
            # Open the file in append mode
            with open(self.file_path, "a", newline="") as file:
                writer = csv.writer(file)
                # Write the header only if the file does not exist
                if not file_exists:
                    writer.writerow(["packet_count", "acc_x", "acc_y", "acc_z", "a_mag"])
            # start csv writer thread
            self.start_csv_writer()
            return True

        except Exception as e:
            print(f"An error occurred: {e}")
            self.stop_csv_writer()
            return False

    def stream_data(self):
        while self.running:
            self.serial_adapter.read_serial_port(self.frame_length)
    # on_adapter_data
    def on_adpater_data(self, row):
        acc_x, acc_y, acc_z, mag = con.simple_convert(row, self.conversion)

        self.listeners[events.EventName.SENSOR_PACKET](acc_x, acc_y, acc_z, mag, self.row_count)
        self.row_count = self.row_count + 1

        self.audio_buffer.append(mag)  # Store the sample in the buffer
        if len(self.audio_buffer) >= self.buffer_size:
            self.chunk = np.array(self.audio_buffer[:self.buffer_size])  # Take the first buffer_size samples
            self.audio_buffer = self.audio_buffer[self.buffer_size:]  # Remove the processed samples

            self.chunk = self.process_stream_chunk(self.chunk)
            self.listeners[events.EventName.VAG_BLOCK](self.chunk)

            self.process_chunk_for_img(self.chunk)
           
            # only do this is sonfiy is selected
            if(self.s.get_sonify_select()==1):
                self.audio_processor.data_queue.put(self.chunk)

        # if the record flag is set the writer should have been started and so we can put data in the csv queue
        if self.s.get_record() == 1:
            self.csv_queue.put([self.row_count, acc_x, acc_y, acc_z, mag])

        # this is a slow and perhaps should be off loaded to a new thread?
        
        if(self.s.get_record() == 1):
            with open(self.file_path, "a", newline="") as file:
                writer = csv.writer(file)
                # Write new data to the CSV file
                writer.writerow([self.row_count, acc_x, acc_y, acc_z, mag])

    def process_stream_chunk(self, chunk ):
        f_chunk = self.filter_input_stream(chunk)
        d_chunk = detrend(f_chunk)
        return d_chunk
    
    def compute_spectrogram(self, signal_data):
        f, t, Zxx = stft(signal_data, fs=self.s.get_sampling_rate(), nperseg=self.s.get_spec_segment_length(),  noverlap=self.s.get_spec_overlap())
        Sxx = np.abs(Zxx)
        return ((f,t,Sxx))
    
    def process_chunk_for_img(self, chunk):
        self.spec_buffer.extend(chunk)
        if len(self.spec_buffer) >=  self.spec_data_size:
            signal_data = np.array(self.spec_buffer)[-self.spec_data_size:]
            img =  self.compute_spectrogram(signal_data)
            self.listeners[events.EventName.SPEC_IMG](img)

    def start_streamer(self):
        if(self.s.get_record() == 1):
            file_created = self.create_record_file()
            if(file_created):
                print("output file created")
            else:
                print("failed to create record file")
   
        if(self.s.get_sonify_select()==1): 
            self.audio_processor.start_audio_thread()
        
        self.running = True
        self.data_streamer_thread = threading.Thread(target=self.stream_data, daemon=True)
        self.data_streamer_thread.start()


    def stop_streamer(self):
        if(self.s.get_record() == 1):
            print("stopping recording")
            self.stop_csv_writer()
        if(self.s.get_sonify_select()==1): 
            print("stopping audio")
            self.audio_processor.stop_audio_thread()
        if self.data_streamer_thread:
            print("stopping stream")
            self.running = False
            self.data_streamer_thread.join()
            self.data_streamer_thread = None
        print("data stream thread stopped")

