import pandas as pd
import os
import time
import glob
from settings import settings as s
import modules.convert as con
from datetime import datetime


class DataReader():
    def __init__(self, mount_point, frame_length, output_dir, cb):
        super().__init__()
        self.mount_point = mount_point
        self.frame_length = frame_length
        self.output_file_name = f"{datetime.now().strftime('%d%m%Y%H%M')}"
        self.output_dir = output_dir
        self.cb = cb
        self.path_to_csv = ""

    def export_to_csv(self, data_to_export, ):
        # set target dir as the exports dir
        current_directory = os.getcwd()
        parent = os.path.abspath(os.path.join(current_directory, os.pardir))
        print(f"parent {parent}")
        target_directory = os.path.join(parent, f"app/{self.output_dir}")

        columns = ['x', 'y', 'z', 'mag']
        df = pd.DataFrame(data_to_export[0], columns=columns)
        df.to_csv(f"{target_directory}{self.output_file_name}.csv", index=False)
        
        return f"{target_directory}{self.output_file_name}.csv"
    
    def poll_for_devices(self):
        seconds = 5
        devices = []
        while seconds > 0: 
            time.sleep(1)  # Wait for 1 second
            seconds = seconds - 1
            devices = self.get_usb_mount_points()
        return devices

    def poll_and_convert(self):
        try:
            # poll the mount_point until it is ready
            # this could be redundant if the user is required to selected a mount point
            while not os.path.ismount(self.mount_point):
                print(f"waiting for device to mount")
                time.sleep(1)
            
            data_files = glob.glob(os.path.join(self.mount_point, '*.HIG'))
            
            print(f"Files in {self.mount_point}:")

            for file in data_files:
                print(f"converting data file {file}")
                converted_data = con.get_results_v2_format(file)
                written_csv = self.export_to_csv(converted_data)
                self.path_to_csv = written_csv
                self.cb(written_csv, self.path_to_csv)

                # delete the file from the device as to free up the device for a new capture
                os.remove(file)

        except Exception as e:
            print(f"Error: {e}")   
    
    def load_csv(self):
        df = pd.read_csv(self.path_to_csv)
        print(df.head(5))

    # these are devices that are already mounted
    def get_usb_mount_points(self):
        mount_points = []
        try:
            with open('/proc/mounts', 'r') as f:
                for line in f.readlines():
                    if '/dev/sd' in line or '/dev/mmcblk' in line:  # Typically USB devices
                        parts = line.split()
                        if len(parts) > 1:
                            mount_points.append(parts[1])
        except Exception as e:
            print(f"An error occurred: {e}")
        return mount_points



