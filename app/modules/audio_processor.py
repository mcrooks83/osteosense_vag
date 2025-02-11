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
        self.audio_audio_chunk = []

    def pink_noise(self, length, gain=0.1):
        uneven = length % 2
        X = np.random.randn(length // 2 + 1 + uneven) + 1j * np.random.randn(length // 2 + 1 + uneven)
        S = np.fft.irfft(X / np.sqrt(np.arange(len(X)) + 1))  # Pink noise spectrum
        S = np.real(S[:length])
        return S / np.max(np.abs(S)) * gain  # Normalize and scale
    

    ''' 
       an attempt at audification 
    '''
    def audify_signal(self, base, max, gamma, use_quadratic=False, use_log=False):
        # new attempt to play actual sounds
        self.audio_audio_chunk = np.abs(self.audio_chunk)
        self.audio_chunk /= np.max(self.audio_chunk)  # Scale between 0 and 1)

        if(use_quadratic):
            dynamic_freq = base + (self.audio_chunk ** gamma) * (max - base)
        elif(use_log):
            dynamic_freq = base * (max / base) ** (self.audio_chunk ** gamma)
        else:
            dynamic_freq = base + self.audio_chunk * (max - base)
            #dynamic_freq = base * (max / base) ** np.power(self.audio_chunk, gamma * 2)

        #dynamic_freq = np.maximum(dynamic_freq, base + 10)  # Ensure we don't go below 110 Hz
        # Generate sound wave
        #out_audio = np.sin(2 * np.pi * np.cumsum(dynamic_freq / self.audio_sampling_rate))

        #dynamic_freq = np.clip(dynamic_freq, base + 10, max)  # Keep in valid range
        #dynamic_freq = np.power(dynamic_freq, 2)  # Exponentiate to amplify variations


        # Compute instantaneous phase without cumulative smoothing
        #phase = np.cumsum(2 * np.pi * dynamic_freq / self.audio_sampling_rate)
        out_audio = np.sin(2 * np.pi * np.cumsum(dynamic_freq / self.audio_sampling_rate))
        #out_audio = np.sin(phase)

        return out_audio

    """
        attempt at sonfificaton
        the zero or no signal plays a low sound
        changes in acceleration are mapped to higher frequencies 
        there are ways to map but here it uses the max amplitude of the chunk
        it could use the mean 
        rate of change (this causes issues)

    """

    def sonify_signal(self, frames):
        avg_amplitude = np.max(np.abs(self.audio_chunk))  # Use max amplitude instead of mean
        #avg_amplitude = np.mean(np.abs(self.audio_chunk))
        
        #delta_signal = np.diff(self.audio_chunk) * self.audio_sampling_rate  # Scale by sample rate to get the rate of change

        # Get the maximum rate of change (this could also be mean or some other statistic)
        #max_change = np.max(np.abs(delta_signal))

        # 100 is the base and 900 is the difference in the scale (1000 - 100)
        # 100 shifts values to a minimum of 100 hz
        # this can be experimented with
        frequency = 100 + (avg_amplitude * 1800)  # Map amplitude to frequency range 100-1000 Hz

        # Step 3: Generate sound for the entire chunk
        time = np.arange(len(self.audio_chunk)) / self.audio_sampling_rate
        output_signal = 0.1 * np.sin(2 * np.pi * frequency * time)

        return output_signal

    # callback is called 
    def _audio_callback(self, outdata, frames, time, status):
        if status:
            print(f"Stream error: {status}")

        # we will have a buffer on the queue
        while not self.data_queue.empty():
            self.audio_chunk = self.data_queue.get()

        if len(self.audio_chunk) >= self.buffer_size:
            
            #base max gamma use_quadratic use_log - note: quadratic doesnt seem as good
            # this is essentiall a frequency mapping on a base frequency
            #out_audio = self.audify_signal(100, 1500, 0.5, False, False)
            out_audio = self.sonify_signal( frames)
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
                sd.sleep(100)  # Sleep for 0.5 second

    def stop(self):
        self.running = False