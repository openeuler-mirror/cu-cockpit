import sys
import subprocess
import re
import json

def run_command(cmd):
    """运行 shell 命令并返回输出行列表"""
    pass

def parse_unit_files(lines):
    """解析 systemctl list-unit-files 输出，返回 {服务名: 注册状态}"""
    pass

def parse_units(lines):
    """解析 systemctl list-units 输出，返回 {服务名: 运行状态}"""
    pass

def merge_and_print(unit_files, units):
    """合并两者并打印结果：服务名 + 运行状态 + 注册状态"""
    pass

def get_service_files_with_status():
    pass
if __name__ == '__main__':
    try:
        unit_files_lines = run_command("systemctl list-unit-files --type=service --no-legend | grep -vE '@.service'")
        units_lines = run_command("systemctl list-units --type=service --all --no-legend | grep -vE 'not-found'")
        unit_files = parse_unit_files(unit_files_lines)
        units = parse_units(units_lines)
        merge_and_print(unit_files, units)
    except RuntimeError as e:
        print(f'错误: {e}', file=sys.stderr)
        exit(1)
    except KeyboardInterrupt:
        print('\n程序被用户中断')
        exit(0)
    except Exception as e:
        print(f'发生未预期的错误: {e}')
        exit(1)
