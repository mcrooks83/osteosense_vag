import numpy as np
from scipy.signal import butter, filtfilt, resample
import sounddevice as sd
import threading
import queue # used to recieve data from the stream

class AudioProcessor(threading.Thread):
    def __init__(self, settings):
        super().__init__()
        self.s = settings
        self.audio_sampling_rate=3300  # same as sampling rate for the sensor
        self.buffer_size=512
        self.data_queue = queue.Queue()
        self.audio_buffer = []  # Buffer for storing magnitdue data
        self.running = False
        self.chunk = []

    # callback is called 
    def _audio_callback(self, outdata, frames, time, status):
        if status:
            print(f"Stream error: {status}")

        # we will have a buffer on the queue
        while not self.data_queue.empty():
            self.chunk = self.data_queue.get()

        if len(self.chunk) >= self.buffer_size:
            # Normalize for audio playback
            self.chunk = self.chunk / np.max(np.abs(self.chunk))

            # Send processed data to the output stream
            outdata[:len(self.chunk)] = self.chunk.reshape(-1, 1)


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
                sd.sleep(500)  # Sleep for 0.5 second

    def stop(self):
        self.running = False