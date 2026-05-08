import json
import subprocess
import sys

def get_hardware_info(device):
    """获取磁盘硬件信息"""
    try:
        # 使用 udevadm 获取硬件属性
        udev_cmd = f"udevadm info --query=property --name=/dev/{device}"
        udev_info = subprocess.check_output(udev_cmd, shell=True, text=True)

        # 初始化所有四个字段为空字符串
        info = {
            'ID_VENDOR': '',
            'ID_MODEL': '',
            'ID_REVISION': '',
            'ID_SERIAL_SHORT': ''
        }
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
        # 为磁盘设备添加硬件信息
        dev['hardware'] = get_hardware_info(dev['name'])

    # 递归处理子设备
    if 'children' in dev:
        for child in dev['children']:
            process_device(child)



def main():
    # 解析 lsblk 输出
    lsblk_output = sys.argv[1]
    try:
        data = json.loads(lsblk_output)
        for device in data['blockdevices']:
            process_device(device)

        # 输出处理后的 JSON
        print(json.dumps(data, indent=2))
    except json.JSONDecodeError:
        print("Error: Failed to parse lsblk output", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
