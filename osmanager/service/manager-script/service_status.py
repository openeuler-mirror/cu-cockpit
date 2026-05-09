import sys
import subprocess
import re
import json

def run_command(cmd):
    """运行 shell 命令并返回输出行列表"""
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        error_msg = f'命令执行失败: {cmd}\n返回码: {e.returncode}\n错误输出: {e.stderr}'
        raise RuntimeError(error_msg) from e
    except FileNotFoundError as e:
        error_msg = f'命令不存在: {cmd}'
        raise RuntimeError(error_msg) from e
    except Exception as e:
        error_msg = f'执行命令时发生未知错误: {cmd}\n错误: {str(e)}'
        raise RuntimeError(error_msg) from e

def parse_unit_files(lines):
    """解析 systemctl list-unit-files 输出，返回 {服务名: 注册状态}"""
    services = {}
    for line in lines:
        parts = re.split('\\s+', line.strip())
        if len(parts) >= 2:
            name = parts[0]
            status = parts[1].strip()
            services[name] = status
    return services

def parse_units(lines):
    """解析 systemctl list-units 输出，返回 {服务名: 运行状态}"""
    services = {}
    for line in lines:
        parts = re.split('\\s+', line.strip(), maxsplit=4)
        if len(parts) >= 4:
            name = parts[0]
            run_state = parts[2].strip()
            description = ' '.join(parts[4:]) if len(parts) > 4 else ''
            services[name] = {'运行状态': run_state, '描述': description}
    return services

def merge_and_print(unit_files, units):
    """合并两者并打印结果：服务名 + 运行状态 + 注册状态"""
    all_services = sorted(set(unit_files.keys()).union(set(units.keys())), key=lambda x: x.lower())
    result = []
    for name in all_services:
        run_state = units.get(name, {}).get('运行状态', 'N/A')
        description = units.get(name, {}).get('描述', '')
        reg_state = unit_files.get(name, 'N/A')
        if run_state == 'N/A' and reg_state != 'alias' and (reg_state != 'N/A'):
            run_state = 'inactive'
        name = name.removesuffix('.service')
        result.append({'服务名称': name, '运行状态': run_state, '注册状态': reg_state, '描述': description})
    print(json.dumps(result, ensure_ascii=False, indent=2))

def get_service_files_with_status():
    raw_lines = run_command("systemctl list-unit-files --type=service --no-legend | grep -vE '@.service'")
    services = []
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
