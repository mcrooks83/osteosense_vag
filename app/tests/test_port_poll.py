
def get_usb_mount_points():
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

usb_mount_points = get_usb_mount_points()
print("USB Mount Points:", usb_mount_points)