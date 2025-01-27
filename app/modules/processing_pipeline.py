from __future__ import division
import sys
sys.path.append("..")
import pandas as pd
import numpy as np
from scipy.signal import medfilt, butter, filtfilt, lfilter
from scipy.signal import welch,  get_window, stft
import math
import sys
from scipy.stats import linregress

def read_file(path):
    df = pd.read_csv(path)
    return df

def extract_axes(df):
    accel_x = df['acc_x']
    accel_y = df['acc_y']
    accel_z = df['acc_z']
    a_mag = df['a_mag'] 

    return accel_x, accel_y, accel_z, a_mag

def build_filter(frequency, sample_rate, filter_type, filter_order):
    #nyq = 0.5 * sample_rate
    if filter_type == "bandpass":
        #nyq_cutoff = (frequency[0] / nyq, frequency[1] / nyq)
        b, a = butter(filter_order, (frequency[0], frequency[1]), btype=filter_type, analog=False, output='ba', fs=sample_rate)
    elif filter_type == "low":
        #nyq_cutoff = frequency[1] / nyq
        b, a = butter(filter_order, frequency[1], btype=filter_type, analog=False, output='ba', fs=sample_rate)
    elif filter_type == "high":
        #nyq_cutoff = frequency[0] / nyq
        b, a = butter(filter_order, frequency[0], btype=filter_type, analog=False, output='ba', fs=sample_rate)

    return b, a
                 
def filter_signal(b, a, signal, filter):
    if(filter=="lfilter"):
        return lfilter(b, a, signal)
    elif(filter=="filtfilt"):
        return filtfilt(b, a, signal)

# previous version   
def compute_fft_mag(data):
    fftpoints = int(math.pow(2, math.ceil(math.log2(len(data)))))
    print(f"computing fft with {fftpoints} points")
    fft = np.fft.fft(data, n=fftpoints)
    mag = np.abs(fft) #/ (fftpoints/2)
    return mag

def compute_fft_mag_with_time(data, fs):
    T = 1/fs
    fftpoints = int(math.pow(2, math.ceil(math.log2(len(data)))))
    fft = np.fft.fft(data, n=fftpoints)
    mag = np.abs(fft) 
    N_r =len(mag)//2
    x = np.linspace(0.0, 1.0/(2.0*T), len(mag)//2).tolist()
    y = mag[:N_r]
    return x,y

def fft_graph_values(data, sample_rate):
    T = 1/sample_rate
    N_r =len(data)//2
    x = np.linspace(0.0, 1.0/(2.0*T), len(data)//2).tolist()
    y = data[:N_r]
    return [x,y]

# assumes a numpy arrray
def compute_power_spectrum(fft_mag):
    power = np.square(fft_mag)
    return power

def compute_frequency_band_percentages(f_interval, data, filter_settings):
    # filter was a high pass in this and now a bandpass
    b,a = build_filter((filter_settings["low_cut_off"], filter_settings["high_cut_off"]),  
                        filter_settings["sampling_rate"], 
                        filter_settings["filter_type"], 
                        filter_settings["filter_order"])

    f_a_mag = filter_signal(b,a, data, "filtfilt")

    fft_mag = compute_fft_mag(f_a_mag)
    fft_graph = fft_graph_values(fft_mag, filter_settings["sampling_rate"])
    f_power = compute_power_spectrum(fft_graph[1])
    total_power =  round(np.sum(f_power),2)

    fft_freq = np.array(fft_graph[0])
    # creates 50 hz bands which could be too small
    f_bands = [(f, f + f_interval) for f in range(filter_settings["low_cut_off"], int(filter_settings["sampling_rate"]/2), f_interval)]
    
    band_powers = []
    interval_axis = []
    for (low, high) in f_bands:
        interval_axis.append(f"{low}-{high}")
        band_power = np.sum(f_power[(fft_freq >= low) & (fft_freq < high)])
        band_powers.append(band_power)

    # computes the percentage contribution of each frequency band
    band_percentages = [(bp / total_power) * 100 for bp in band_powers]

    return interval_axis, band_percentages

def compute_spectogram(data, filter_settings, spectogram_settings):
    b,a = build_filter((filter_settings["low_cut_off"], filter_settings["high_cut_off"]), 
                        filter_settings["sampling_rate"], 
                        filter_settings["filter_type"], 
                        filter_settings["filter_order"])

    f_a_mag = filter_signal(b,a, data, "filtfilt")

    window = get_window(spectogram_settings['window'], spectogram_settings['segment_length']) 
    
    f, t, Zxx = stft(f_a_mag, fs=filter_settings["sampling_rate"], window=window,  nperseg=spectogram_settings["segment_length"],
                         noverlap=spectogram_settings['overlap'])
    Sxx = np.abs(Zxx)
    return f, t, Sxx

def compute_freq_band_spectogram_from_stft(data, filter_settings, spectogram_settings, band):
    b,a = build_filter((filter_settings["low_cut_off"], filter_settings["high_cut_off"]), 
                        filter_settings["sampling_rate"], 
                        filter_settings["filter_type"], 
                        filter_settings["filter_order"])

    f_a_mag = filter_signal(b,a, data, "filtfilt")
    window = get_window(spectogram_settings['window'], spectogram_settings['segment_length']) 

    f, t, Zxx = stft(f_a_mag, fs=filter_settings["sampling_rate"], window=window,  nperseg=spectogram_settings["segment_length"],
                         noverlap=spectogram_settings['overlap'])
    
    # compute power from stft
    op_pwr = np.abs(Zxx)**2
    p_Zxx = 10 * np.log10(np.abs(op_pwr))
    freq_mask = (f >= band[0]) & (f <= band[1])  # Create a boolean mask
    frequencies_filtered = f[freq_mask]  # Apply mask to frequencies
    Zxx_dB_filtered = p_Zxx[freq_mask, :]  # Apply mask to spectrogram data

    return frequencies_filtered, t, Zxx_dB_filtered


### compute the fractal dimension of the recording
# the only way this comes out is if the slope is made a positive value if negative
def apply_hanning(d):
    hanning_window = np.hanning(len(d))
    windowed_signal = d * hanning_window
    return windowed_signal

def amplitude_normal(signal):
    sig = np.array(signal)
    data_min = min(sig)
    data_max = max(sig)
    normal = (sig - data_min) / (data_max - data_min)
    return normal.tolist()

def compute_fd(slope):
    fd = (5 - abs(slope)) / 2
    return fd

def compute_fd_from_signal(s, fs, min_f, max_f):
    # apply hanning window
    hann = apply_hanning(s)
    dft_result = np.fft.fft(hann)

    # psd
    x_f = np.fft.fftfreq(len(hann), d=1/fs)
    psd = np.abs(dft_result) ** 2
    mask = x_f > 0
    #postive side of FFT / PSD
    pos_f = x_f[mask]
    pos_psd = psd[mask]  # Filter PSD using the same mask

    # log log
    log_f = np.log(pos_f)
    log_psd = np.log(pos_psd)

    # slope and best fit
    indices = np.where((pos_f >= min_f) & (pos_f <= max_f))[0]

    x = log_f[indices]
    y = log_psd[indices]
    m, b, r_value, p_value, std_err = linregress(x, y)

    #fractal dimension
    fd_n = compute_fd(m)
    return fd_n

### data must be normalised and filtered prior
### fd is computed from the magnitude
def compute_fractal_dimension(magnitdue, filter_settings):
    b,a = build_filter((filter_settings["low_cut_off"], filter_settings["high_cut_off"]), 
                        filter_settings["sampling_rate"], 
                        filter_settings["filter_type"], 
                        filter_settings["filter_order"])

    f_a_mag = filter_signal(b,a, magnitdue, "filtfilt")
    mag_norm = amplitude_normal(f_a_mag)

    fd = compute_fd_from_signal(mag_norm, filter_settings["sampling_rate"], filter_settings["low_cut_off"], filter_settings["high_cut_off"])
    print(fd)
    return fd

