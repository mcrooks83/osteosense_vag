# app settings 
# can be configured from the UI in a future update

import os

class Settings:
    def __init__(self):

        self.test_file = "mc_test_2_60bpm.csv"
        self.usb_port = "/dev/ttyACM0"
        self.mount_path = "/media/mike/641A-F4BD"
        self.baud_rate = 256000
        self.frame_length = 11 # bytes
        self.stream_frame_length = 8

        self.export_dir = "exports/"

        self.BUFFER_SIZE = 10000

        self.default_frame = 0 # 0 = stream, 1 = analyse
        self.log = 0

        # filter settings 
        self.sampling_rate = 6000 # 6kHz
        self.filter_type = "high"
        self.low_cut_off = 100 # removes muscle artifacts and baseline wander
        self.high_cut_off = -1
        self.filter_order = 5   # 9th order has been used in literature?

        # spectogram settings
        self.segment_length = 256  # Length of each segment
        self.overlap = self.segment_length // 2  # 50% overlap
        self.window = 'hann'

        self.make_dirs()


    def make_dirs(self):
        if not os.path.exists(self.export_dir):
            os.mkdir(self.export_dir)

        log_dir = os.path.join(self.export_dir, "logs")
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

    def get_log(self):
        return self.log
    
    def set_log(self, log):
        self.log = log
        
    def get_test_file(self):
        return self.test_file
    
    def get_spectogram_settings(self):
        spectogram_settings = {
            "segment_length" : self.segment_length,
            "overlap": self.overlap,
            "window": self.window
        }
        return spectogram_settings

    def get_filter_settings_for_highpass(self):
        filter_settings = {
            "sampling_rate": self.sampling_rate,
            "low_cut_off": self.low_cut_off,
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