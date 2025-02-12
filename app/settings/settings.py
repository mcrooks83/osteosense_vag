# app settings 
# can be configured from the UI in a future update

import os

class Settings:
    def __init__(self):

        self.test_file = "TT_test_1.csv"
        self.usb_port = "/dev/ttyACM0"
        self.mount_path = "/media/mike/641A-F4BD"
        self.baud_rate = 256000
        self.frame_length = 11 # bytes - should be 11 if only acceleration
        self.stream_frame_length = 8 # when streaming just acceleration
        self.sonify = 1 # sonfigy select
        #self.g_level = 9.8

        self.conversion_4g = 0.000122
        self.conversion_32g = 0.0009765625
        self.conversion_16g = 0.000488

        self.export_dir = "exports/"

        self.BUFFER_SIZE = 4096 # this is an optimal buffer size for general

        self.audio_buffer_size = 512 # previously 1024

        self.default_frame = 0 # 0 = stream, 1 = analyse

        self.record = 0 #flag to set if recording

        # filter settings 
        self.sampling_rate = 3000 # 3Khz
        self.filter_type = "bandpass" # high

        # these could be settable in the UI
        self.low_cut_off = 100 # removes muscle artifacts and baseline wander
        self.high_cut_off = 1000  # 
        self.filter_order = 4   # 9th order has been used in literature?

        # spectogram settings
        self.segment_length = 1024  # Length of each segment
        self.overlap = self.segment_length // 2  # 50% overlap
        self.window = 'hann'
        self.f_band1 = (50, 250)
        self.f_band2 = (250, 500)

        self.make_dirs()

    def get_audio_buffer_size(self):
        return self.audio_buffer_size

    def get_sampling_rate(self):
        return self.sampling_rate
        
    def get_conversion_16g(self):
        return self.conversion_16g

    def get_conversion_4g(self):
        return self.conversion_4g
    
    def get_conversion_32g(self):
        return self.conversion_32g
    
    def get_f_band1(self):
        return self.f_band1
    
    def get_f_band2(self):
        return self.f_band2
    
    def get_sonify_select(self):
        return self.sonify

    def set_sonify_select(self, value):
        self.sonify = value

    def make_dirs(self):
        if not os.path.exists(self.export_dir):
            os.mkdir(self.export_dir)

        log_dir = os.path.join(self.export_dir, "recordings")
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

    def get_record(self):
        return self.record
    
    def set_record(self, record):
        self.record = record
        
    def get_test_file(self):
        return self.test_file
    
    def get_spectogram_settings(self):
        spectogram_settings = {
            "segment_length" : self.segment_length,
            "overlap": self.overlap,
            "window": self.window
        }
        return spectogram_settings

    def get_filter_settings_for_bandpass(self):
        filter_settings = {
            "sampling_rate": self.sampling_rate,
            "low_cut_off": self.low_cut_off,
            "high_cut_off": self.high_cut_off,
            "filter_order": self.filter_order,
            "filter_type": self.filter_type
        }
        return filter_settings
    
    def get_default_frame(self):
        return self.default_frame
    
    def set_default_frame(self, default_frame):
        self.default_frame = default_frame

    def set_usb_port(self, usb_port):
        self.usb_port = usb_port

    def get_usb_port(self):
        return self.usb_port

    def set_mount_path(self, path):
        self.mount_path = path

    def get_mount_path(self):
        return self.mount_path
    
    def set_baud_rate(self, baud):
        self.baud_rate = baud

    def get_baud_rate(self):
        return self.baud_rate
    
    def set_frame_length(self, bytes):
        self.frame_length = bytes

    def get_frame_length(self):
        return self.frame_length
    
    def set_stream_frame_length(self, bytes):
        self.stream_frame_length = bytes

    def get_stream_frame_length(self):
        return self.stream_frame_length
    
    def get_export_dir(self):
        return self.export_dir
    
    def get_buffer_size(self):
        return self.BUFFER_SIZE