

"""
the SerialAdapter class handles the core functions required to stream data

1. find a device (scan usb ports to find connected devices)
2. open / close a connection
3. start / stop stream

this is the same as a ble adpater that will

1. scan 
2. connect / disconnect
3. start / stop

Processing of data can be split into two parts

1. convert the packet recieved
2. process data - vag, spectrum, audio, etc

this might replace the DataStreamer class

"""
import serial
class SerialAdapter:
    
    @staticmethod
    def find_devices():
        ports = serial.tools.list_ports.comports()
        usb_ports = []
        # Cross-platform port detection
        for port in ports:
            # Append Linux ACM ports and all ports for Windows/others
            if 'ACM' in port.device or any(platform_key in port.description.lower() for platform_key in ['usb', 'serial']):
                usb_ports.append(port.device)

        return ports
    
    def __init__(self, baud_rate, status_cb, on_data_read_cb):
        super().__init__()
        """
            sets up a serial port and accepts a call back to update the status
            could wrap the serial.Serial functions (in waiting, read etc)
            should poll the port and return the binary data
        """
        self.port_name = None
        self.baud_rate = baud_rate
        self.ser = None 
        self.status_cb = status_cb
        self.on_data_read_cb = on_data_read_cb
        #self.connect_device() # open serial port 

    def set_serial_port(self, port_name):
        self.port_name = port_name
        # try to open it 
        self.open_serial_port()

    def get_serial_port(self):
        return self.ser

    def open_serial_port(self):
        try:
            self.ser = serial.Serial(port=self.port_name, baudrate=self.baud_rate, timeout=1)
            print(f"Serial port {self.ser.portstr} opened successfully.")
            self.status_cb(True)
        except serial.SerialException as e:
            self.status_cb(False)
            print(f"Error opening serial port: {e}")

    def close_serial_port(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f"Serial port {self.ser.portstr} closed successfully.")
            self.status_cb(False)
        else:
            print("Serial port is already closed or was never opened.")


    # starts a thread that polls the serial port?
    def start_stream(self):
        pass

    # polling of the usb port requires reading it at a given frame length
    def read_serial_port(self, frame_length):
        try:
            if self.ser.in_waiting > 0:
                row = self.ser.read(frame_length)
                self.on_data_read_cb(row)
        except serial.SerialException as e:
                print(f"Error during serial read: {e}")
