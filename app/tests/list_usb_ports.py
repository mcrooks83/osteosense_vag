

import serial.tools.list_ports

def list_serial_ports():
    ports = serial.tools.list_ports.comports()
    usb_ports = []

    for port in ports:
        port_info = {
            'device': port.device,
            'name': port.name,
            'description': port.description,
            'hwid': port.hwid,
            'manufacturer': port.manufacturer,
            'product': port.product,
            'serial_number': port.serial_number,
            'location': port.location,
            'vid': port.vid,
            'pid': port.pid,
            'interface': port.interface
        }
        usb_ports.append(port_info)

    return usb_ports


ports = list_serial_ports()
print(ports)