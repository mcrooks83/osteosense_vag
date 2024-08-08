
import serial
import time

class SerialInterface():
    def __init__(self, port_name, baud_rate):
        super().__init__()
        self.port_name = port_name
        self.baud_rate = baud_rate
        self.ser =None 
        self.open_serial_port()

    def get_serial(self):
        return self.ser
    
    def open_serial_port(self):
        try:
            self.ser = serial.Serial(port=self.port_name, baudrate=self.baud_rate, timeout=1)
            print(f"Serial port {self.ser.portstr} opened successfully.")
        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")

    def close_serial_port(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f"Serial port {self.ser.portstr} closed successfully.")
        else:
            print("Serial port is already closed or was never opened.")

    def send_message(self, message, rsp=0):
        self.ser.flushInput()
        self.ser.write(message.encode())
        time.sleep(0.1)
        if(rsp):
            line = self.ser.readline().decode('utf-8',  errors='ignore').strip()
            return line

