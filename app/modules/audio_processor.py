import numpy as np
from scipy.signal import butter, filtfilt, resample
import sounddevice as sd
import threading
import queue # used to recieve data from the stream

class AudioProcessor(threading.Thread):
    def __init__(self, settings, cb):
        super().__init__()
        #self.port_name = port_name
        #self.baud_rate = baud_rate
        self.s = settings
        self.cb = cb
        self.audio_sampling_rate=3300  # same as sampling rate for the sensor
        self.buffer_size=512
        self.data_queue = queue.Queue()
        self.audio_buffer = []  # Buffer for storing magnitdue data

        self.running = False
   
        # create a bandpass filter
        filter_settings = self.s.get_filter_settings_for_bandpass()
        b, a = butter(filter_settings["filter_order"], [filter_settings["low_cut_off"], filter_settings["high_cut_off"]], btype='bandpass', fs=filter_settings["sampling_rate"])
        self.b = b
        self.a = a

    def get_audio_buffer_size(self):
        return self.buffer_size

    def filter_input_stream(self,data):
        return filtfilt(self.b, self.a, data)

    # callback is called 
    def _audio_callback(self, outdata, frames, time, status):
        if status:
            print(f"Stream error: {status}")

        while not self.data_queue.empty():
            mag_sample = self.data_queue.get()
            self.audio_buffer.append(mag_sample)  # Store the sample in the buffer  

        #print(f"Audio callback: outdata length = {len(outdata)}, audio_buffer length = {len(self.audio_buffer)}") 

        if len(self.audio_buffer) >= self.buffer_size:
            chunk = np.array(self.audio_buffer[:self.buffer_size])  # Take the first buffer_size samples
            self.audio_buffer = self.audio_buffer[self.buffer_size:]  # Remove the processed samples

            # band pass filter
            chunk = self.filter_input_stream(chunk)
            self.cb(chunk)

            # Normalize for audio playback
            chunk_norm = chunk / np.max(np.abs(chunk))

            # Send processed data to the output stream
            outdata[:len(chunk)] = chunk.reshape(-1, 1)


    def run(self):
        print("audio running")
        """Start audio processing in a separate thread."""
        self.running = True
        with sd.OutputStream(
            samplerate=self.audio_sampling_rate,
            blocksize=self.buffer_size,
            channels=2,
            callback=self._audio_callback
        ):
            print("Playing stream in real-time. Press stop to end.")
            while self.running:
                sd.sleep(1000)  # Sleep for 1 second

    def stop(self):
        self.running = False