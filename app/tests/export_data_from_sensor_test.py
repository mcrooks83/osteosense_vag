
import sys

sys.path.append("..")

import time
from modules import data_reader as dr
from settings import settings as s


# create a settings class instance
settings = s.Settings()

# implment a callback function to recieve converted data
def exported_data(export_file):
    print(f"callback: {export_file}")

data_file_name = "test1"

data_r = dr.DataReader(settings.get_mount_path(), settings.get_frame_length(), data_file_name, settings.get_export_dir(), exported_data)

data_r.poll_and_convert()
time.sleep(1)
data_r.load_csv()