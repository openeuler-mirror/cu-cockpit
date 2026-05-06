import json
import subprocess
import sys

def get_hardware_info(device):
    """获取磁盘硬件信息"""
    try:
        udev_cmd = f'udevadm info --query=property --name=/dev/{device}'
        udev_info = subprocess.check_output(udev_cmd, shell=True, text=True)
        info = {'ID_VENDOR': '', 'ID_MODEL': '', 'ID_REVISION': '', 'ID_SERIAL_SHORT': ''}
        for line in udev_info.splitlines():
            if '=' in line:
                key, value = line.split('=', 1)
                if key in info:
                    info[key] = value
        return info
    except Exception:
        return {}

def process_device(dev):
    """递归处理设备及其子设备"""
    if dev['type'] in ['disk', 'rom']:
        dev['hardware'] = get_hardware_info(dev['name'])
    if 'children' in dev:
        for child in dev['children']:
            process_device(child)

def main():
    pass
if __name__ == '__main__':
    main()
