from mmap import mmap, ACCESS_READ
from struct import unpack
from math import sqrt

### conversion of binary sensor data to x,y,z accleration ###
#
#   binary format
#   b'\x00\x01\xc4\xb9\xff\xcb\xfb\xe4\x00\x83\x0b'
#   divide by 1024 

def simple_convert(row, gyr=0):
    acc_x = (unpack('<h', bytes(row[2:4]))[0]  ) / 1024
    acc_y = (unpack('<h', bytes(row[4:6]))[0]  ) / 1024
    acc_z = (unpack('<h', bytes(row[6:8]))[0]  ) / 1024
    
    if(gyr):
        gyr_x = (unpack('<h', bytes(row[8:10]))[0]  ) / 1024
        gyr_y = (unpack('<h', bytes(row[10:12]))[0]  ) / 1024
        gyr_z = (unpack('<h', bytes(row[12:14]))[0]  ) / 1024

        return acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z
    else:
        return acc_x, acc_y, acc_z, 0, 0, 0 

def unpacking_v2_format_hig(row):
 
    list_values = []
    index = (unpack('>I', bytes(row[0:4]))[0]) 
    acc_x = (unpack('>h', bytes(row[4:6]))[0]) / 1024
    acc_y = (unpack('>h', bytes(row[6:8]))[0]) / 1024
    acc_z = (unpack('>h', bytes(row[8:10]))[0]) / 1024

    #index = (index / 6000)
    #list_values.append(index)
    acc_x = float(acc_x) / 1024
    list_values.append(acc_x)
    acc_y = acc_y / 1024
    list_values.append(acc_y)
    acc_z = acc_z / 1024
    list_values.append(acc_z)
    amag = round(sqrt(pow(acc_x, 2) + pow(acc_y, 2) + pow(acc_z, 2)),2)
    list_values.append(amag)
    return list_values

# pass in frame length
def read_row(mm,hig=1):
    count = 0
    while True:
        count += 1
        if(hig==1):
            row = mm.read(11) # packet length
            if not len(row) == 11: 
                break 
        yield row 

def get_results_v2_format(hig_filename):
    complete_results = []    
    if hig_filename:
        print("getting results for", hig_filename)
        with open(hig_filename,'rb') as file:
            mm = mmap(file.fileno(), 0, access=ACCESS_READ)
            results = [unpacking_v2_format_hig(row) for row in read_row(mm)]
            complete_results.append(results)
            mm.close()
            file.close() 
        
    print("completed conversion",flush=True)
    return complete_results