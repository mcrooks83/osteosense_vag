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
    

    ''' 
        change the gamma value to see what happens -> higher value will shift the frequency output more 
        rapidly with changes in accleration

        Try: (comes before generating the sound)
        # Control the amplitude based on the acceleration signal
        amplitude_env = self.chunk  # Linear envelope from 0 to 1 based on chunk
        amplitude_env = np.clip(amplitude_env, 0.1, 1)  # Avoid completely silent (no volume) sound

        (comes after generating the sound)
        # Apply volume envelope to the sound wave
        out_audio *= amplitude_env  # Scale by the envelope
    '''
    def sonify_signal(self, base, max, gamma, use_quadratic=False, use_log=True):
        # new attempt to play actual sounds
        self.chunk = np.abs(self.chunk)
        self.chunk /= np.max(self.chunk)  # Scale between 0 and 1)
        if(use_quadratic):
            dynamic_freq = base + (self.chunk ** gamma) * (max - base)
        elif(use_log):
            dynamic_freq = base * (max / base) ** (self.chunk ** gamma)
        else:
            dynamic_freq = base + self.chunk * (max - base)

        dynamic_freq = np.maximum(dynamic_freq, base + 10)  # Ensure we don't go below 110 Hz

        # Generate sound wave
        out_audio = np.sin(2 * np.pi * np.cumsum(dynamic_freq) / self.audio_sampling_rate)
        return out_audio


    # callback is called 
    def _audio_callback(self, outdata, frames, time, status):
        if status:
            print(f"Stream error: {status}")

        # we will have a buffer on the queue
        while not self.data_queue.empty():
            self.chunk = self.data_queue.get()

        if len(self.chunk) >= self.buffer_size:
            
            #base max gamma use_quadratic use_log - note: quadratic doesnt seem as good
            # this is essentiall a frequency mapping on a base frequency
            out_audio = self.sonify_signal(200, 1500, 0.5, False, False)
            # Send processed data to the output stream
            outdata[:len(out_audio)] = out_audio.reshape(-1, 1)


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