import numpy as np
from scipy.signal import butter, filtfilt, resample
import sounddevice as sd
import threading
import queue # used to recieve data from the stream

class AudioProcessor(threading.Thread):
    def __init__(self, settings):
        super().__init__()
        self.s = settings
        self.audio_sampling_rate=3000  # same as sampling rate for the sensor
        self.buffer_size = settings.get_audio_buffer_size()
        self.data_queue = queue.Queue()
        self.audio_buffer = []  # Buffer for storing magnitdue data
        self.running = False
        self.chunk = []

    def pink_noise(self, length, gain=0.1):
        uneven = length % 2
        X = np.random.randn(length // 2 + 1 + uneven) + 1j * np.random.randn(length // 2 + 1 + uneven)
        S = np.fft.irfft(X / np.sqrt(np.arange(len(X)) + 1))  # Pink noise spectrum
        S = np.real(S[:length])
        return S / np.max(np.abs(S)) * gain  # Normalize and scale

    # callback is called 
    def _audio_callback(self, outdata, frames, time, status):
        if status:
            print(f"Stream error: {status}")

        # we will have a buffer on the queue
        while not self.data_queue.empty():
            self.chunk = self.data_queue.get()

        if len(self.chunk) >= self.buffer_size:

            self.chunk += self.pink_noise(len(self.chunk), gain=0.3)
            self.chunk = np.convolve(self.chunk, np.array([0.6, 0.3, 0.1]), mode='same')
            # Normalize for audio playback
            #self.chunk = self.chunk / np.max(np.abs(self.chunk))

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