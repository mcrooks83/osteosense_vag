
import sys
sys.path.append("..")
import pandas as pd
from modules import processing_pipeline as pp


from settings import settings as s
settings = s.Settings()

hp_filter_settings = settings.get_filter_settings_for_highpass()
spectogram_settings = settings.get_spectogram_settings()

data_path = "../exports/mc_test_2_60bpm.csv"
df = pd.read_csv(data_path)

x,y,z,a_mag = pp.extract_axes(df)

intervals, f_percentages = pp.compute_frequency_band_percentages(50, a_mag, hp_filter_settings)
print(intervals)

frequencies, times, sXX = pp.compute_spectogram(a_mag, hp_filter_settings, spectogram_settings)
print(sXX)