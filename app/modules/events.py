from enum import Enum 

''' events for listeners, perhaps can be written as an event i.e sensor_packet_recieved etc'''

class EventName(Enum):
    SENSOR_PACKET = "sensor_packet"
    VAG_BLOCK = "vag_block"
    SPEC_IMG = "spec_img"
    ADAPTER_STATUS = "adapter_status"
    USB_PORTs = "usb_ports"