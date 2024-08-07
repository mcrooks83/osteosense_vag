
import serial
import time
import cmd



port_name = "/dev/ttyACM0"
baud_rate = 256000

ser = serial.Serial(port=port_name, baudrate=baud_rate, timeout=1)
ser.flush()
print(f"Serial port {ser.portstr} opened successfully.")

# this doesnt work as there is data on the wire when streaming is started that needs to be ignored
def read_serial_lines(ser, num_lines=3):
    """Reads a specified number of lines from the serial port."""
    lines = []
    for _ in range(num_lines):
        line = ser.readline().decode('utf-8').strip()
        if line:
            lines.append(line)
        else:
            break
    return lines

def send_message(ser, message):
    ser.flushInput()
    ser.write(message.encode())
    time.sleep(0.1)

class MyCLI(cmd.Cmd):
    prompt = 'ost: '  # Change the prompt text
    intro = 'Welcome to Osteosense Test CLI. Type "help" for available commands.' 

    def do_identify(self, arg):
        """Identify Sensor"""
        print("identifying sensor")
        message = f"IDENTIFY 1\n"
        send_message(ser, message)
        #response = read_serial_lines(ser)
        #print(f"Response: {response}")

    def do_start_stream(self, line):
        """Start Streaming"""
        print("starting stream")
        message = f"START_STREAM 1\n"
        send_message(ser, message)
        #response = read_serial_lines(ser)
        #print(f"Response: {response}")
        

    def do_stop_stream(self, line):
        """Stop Streaming"""
        print("stopping stream")
        message = f"STOP_STREAM 0\n"
        send_message(ser,message)
        #response =  read_serial_lines(ser)
        #print(f"Response: {response}")
        


    def do_quit(self, line):
        """Exit the CLI."""
        return True
    
    def postcmd(self, stop, line):
        print()  # Add an empty line for better readability
        return stop


MyCLI().cmdloop()

# Close the serial port
ser.close()