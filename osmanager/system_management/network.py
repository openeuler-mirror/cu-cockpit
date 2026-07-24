import ipaddress
import json
import re
from pathlib import Path

from .command import CommandResult, run_safe
from .config_center import OperationConflict, SystemOperationError


RESOLV_CONF = Path('/etc/resolv.conf')
ZONE_PATTERN = re.compile(r'^[A-Za-z0-9_-]{1,64}$')
SERVICE_PATTERN = re.compile(r'^[A-Za-z0-9_-]{1,64}$')


def _run_json(args):
    result = run_safe(args, {args[0]}, timeout=8)
    if not result.success:
        raise SystemOperationError(result.stderr.strip() or f'{args[0]} 命令执行失败')
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise SystemOperationError(f'{args[0]} 返回无效 JSON') from error


def interface_type(name, link_type='', info_kind=''):
    if name == 'lo':
        return 'loopback'
    if info_kind:
        return info_kind
    if name.startswith('veth'):
        return 'veth'
    if name.startswith(('br-', 'docker')):
        return 'bridge'
    if link_type and link_type != 'ether':
        return link_type
    return 'ethernet'


def merge_interfaces(links, addresses):
    address_by_index = {item.get('ifindex'): item for item in addresses}
    items = []
    for link in links:
        address = address_by_index.get(link.get('ifindex'), {})
        info_kind = (link.get('linkinfo') or {}).get('info_kind', '')
        ip_items = []
        for item in address.get('addr_info', []):
            ip_items.append({
                'family': item.get('family', ''),
                'local': item.get('local', ''),
                'prefixlen': item.get('prefixlen'),
                'scope': item.get('scope', ''),
                'dynamic': bool(item.get('dynamic', False)),
                'preferred_life_time': item.get('preferred_life_time'),
                'valid_life_time': item.get('valid_life_time'),
            })
        flags = link.get('flags', [])
        items.append({
            'ifindex': link.get('ifindex'),
            'name': link.get('ifname', ''),
            'type': interface_type(link.get('ifname', ''), link.get('link_type', ''), info_kind),
            'state': link.get('operstate', 'UNKNOWN'),
            'up': 'UP' in flags,
            'lower_up': 'LOWER_UP' in flags,
            'mtu': link.get('mtu'),
            'mac': link.get('address', ''),
            'master': link.get('master'),
            'addresses': ip_items,
        })
    return items


def read_dns(path=RESOLV_CONF):
    result = {'nameservers': [], 'search': [], 'options': [], 'path': str(path), 'symlink': path.is_symlink()}
    try:
        content = path.read_text(encoding='utf-8')
    except OSError:
        return result
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        parts = stripped.split()
        if parts[0] == 'nameserver' and len(parts) >= 2:
            result['nameservers'].append(parts[1])
        elif parts[0] == 'search':
            result['search'].extend(parts[1:])
        elif parts[0] == 'options':
            result['options'].extend(parts[1:])
    return result


def _split_endpoint(value):
    if value.startswith('[') and ']:' in value:
        address, port = value[1:].rsplit(']:', 1)
        return address, port
    if ':' in value:
        return value.rsplit(':', 1)
    return value, ''


def parse_listeners(output):
    items = []
    process_pattern = re.compile(r'"([^"]+)",pid=(\d+)')
    for line in output.splitlines():
        parts = line.split(None, 6)
        if len(parts) < 6:
            continue
        local_address, local_port = _split_endpoint(parts[4])
        peer_address, peer_port = _split_endpoint(parts[5])
        processes = [{'name': match[0], 'pid': int(match[1])} for match in process_pattern.findall(parts[6] if len(parts) > 6 else '')]
        items.append({
            'protocol': parts[0],
            'state': parts[1],
            'recv_q': int(parts[2]) if parts[2].isdigit() else 0,
            'send_q': int(parts[3]) if parts[3].isdigit() else 0,
            'local_address': local_address,
            'local_port': local_port,
            'peer_address': peer_address,
            'peer_port': peer_port,
            'processes': processes,
        })
    return items


def _listeners():
    result = run_safe(['ss', '-H', '-lntup'], {'ss'}, timeout=8)
    if not result.success:
        raise SystemOperationError(result.stderr.strip() or '无法读取监听端口')
    return parse_listeners(result.stdout)


def _firewalld_active():
    result = run_safe(['systemctl', 'is-active', 'firewalld'], {'systemctl'}, timeout=3)
    return result.stdout.strip() == 'active'


def _firewall_command(args, timeout=10):
    result = run_safe(['firewall-cmd', *args], {'firewall-cmd'}, timeout=timeout)
    if not result.success:
        raise SystemOperationError(result.stderr.strip() or result.stdout.strip() or 'firewall-cmd 执行失败')
    return result.stdout.strip()


def firewall_status():
    active = _firewalld_active()
    if not active:
        return {
            'installed': True,
            'active': False,
            'writable': False,
            'reason': 'firewalld 服务未运行',
            'default_zone': '',
            'zones': [],
            'available_services': [],
        }
    default_zone = _firewall_command(['--get-default-zone'])
    zones = _firewall_command(['--get-zones']).split()
    available_services = _firewall_command(['--get-services']).split()
    zone_items = []
    for zone in zones:
        services = _firewall_command(['--zone', zone, '--list-services']).split()
        ports = _firewall_command(['--zone', zone, '--list-ports']).split()
        rich_rules = [line for line in _firewall_command(['--zone', zone, '--list-rich-rules']).splitlines() if line]
        interfaces = _firewall_command(['--zone', zone, '--list-interfaces']).split()
        sources = _firewall_command(['--zone', zone, '--list-sources']).split()
        zone_items.append({
            'name': zone,
            'default': zone == default_zone,
            'services': services,
            'ports': ports,
            'rich_rules': rich_rules,
            'interfaces': interfaces,
            'sources': sources,
        })
    return {
        'installed': True,
        'active': True,
        'writable': True,
        'reason': '',
        'default_zone': default_zone,
        'zones': zone_items,
        'available_services': available_services,
    }


def network_overview():
    links = _run_json(['ip', '-j', 'link', 'show'])
    addresses = _run_json(['ip', '-j', 'address', 'show'])
    routes = _run_json(['ip', '-j', 'route', 'show', 'table', 'all'])
    interfaces = merge_interfaces(links, addresses)
    listeners = _listeners()
    default_routes = [route for route in routes if route.get('dst') == 'default']
    return {
        'interfaces': interfaces,
        'routes': routes,
        'default_routes': default_routes,
        'dns': read_dns(),
        'listeners': listeners,
        'firewall': firewall_status(),
        'summary': {
            'interfaces': len(interfaces),
            'interfaces_up': sum(1 for item in interfaces if item['up']),
            'addresses': sum(len(item['addresses']) for item in interfaces),
            'routes': len(routes),
            'listeners': len(listeners),
        },
    }


def _validate_zone(zone, valid_zones):
    value = str(zone or '').strip()
    if not ZONE_PATTERN.fullmatch(value) or value not in valid_zones:
        raise ValueError('防火墙 zone 不存在')
    return value


def _validate_rule(rule_type, value, protocol, available_services):
    normalized_type = str(rule_type or '').strip().lower()
    normalized_value = str(value or '').strip()
    if normalized_type == 'service':
        if not SERVICE_PATTERN.fullmatch(normalized_value) or normalized_value not in available_services:
            raise ValueError('防火墙 service 不可用')
        return 'service', normalized_value
    if normalized_type == 'port':
        normalized_protocol = str(protocol or '').strip().lower()
        if normalized_protocol not in ('tcp', 'udp'):
            raise ValueError('端口协议只允许 tcp 或 udp')
        try:
            port = int(normalized_value)
        except ValueError as error:
            raise ValueError('端口必须为整数') from error
        if not 1 <= port <= 65535:
            raise ValueError('端口范围必须为 1-65535')
        return 'port', f'{port}/{normalized_protocol}'
    raise ValueError('规则类型只允许 service 或 port')


def update_firewall_rule(payload):
    if not isinstance(payload, dict):
        raise ValueError('请求体必须为对象')
    status = firewall_status()
    if not status['active']:
        raise OperationConflict(status['reason'])
    action = str(payload.get('action', '')).strip().lower()
    if action not in ('add', 'remove'):
        raise ValueError('action 只允许 add 或 remove')
    zone = _validate_zone(payload.get('zone'), [item['name'] for item in status['zones']])
    rule_type, value = _validate_rule(payload.get('rule_type'), payload.get('value'), payload.get('protocol'), status['available_services'])
    operation = f'--{action}-{rule_type}'
    compensation = f'--{"remove" if action == "add" else "add"}-{rule_type}'
    runtime_args = ['--zone', zone, operation, value]
    _firewall_command(runtime_args)
    try:
        _firewall_command(['--permanent', '--zone', zone, operation, value])
    except Exception:
        try:
            _firewall_command(['--zone', zone, compensation, value])
        except Exception:
            pass
        raise
    return firewall_status()