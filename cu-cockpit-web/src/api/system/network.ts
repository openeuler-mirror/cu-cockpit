import request from '/@/utils/request';

export interface NetworkAddress { family: string; local: string; prefixlen: number; scope: string; dynamic: boolean; }
export interface NetworkInterface { ifindex: number; name: string; type: string; state: string; up: boolean; lower_up: boolean; mtu: number; mac: string; master: number | null; addresses: NetworkAddress[]; }
export interface NetworkRoute { dst?: string; gateway?: string; dev?: string; protocol?: string; scope?: string; prefsrc?: string; metric?: number; table?: string | number; flags?: string[]; }
export interface ListenerProcess { name: string; pid: number; }
export interface NetworkListener { protocol: string; state: string; recv_q: number; send_q: number; local_address: string; local_port: string; peer_address: string; peer_port: string; processes: ListenerProcess[]; }
export interface FirewallZone { name: string; default: boolean; services: string[]; ports: string[]; rich_rules: string[]; interfaces: string[]; sources: string[]; }
export interface FirewallStatus { installed: boolean; active: boolean; writable: boolean; reason: string; default_zone: string; zones: FirewallZone[]; available_services: string[]; }
export interface NetworkOverview {
	interfaces: NetworkInterface[];
	routes: NetworkRoute[];
	default_routes: NetworkRoute[];
	dns: { nameservers: string[]; search: string[]; options: string[]; path: string; symlink: boolean };
	listeners: NetworkListener[];
	firewall: FirewallStatus;
	summary: { interfaces: number; interfaces_up: number; addresses: number; routes: number; listeners: number };
}

export const getNetworkOverview = (): Promise<NetworkOverview> => request({ url: '/system/network/overview', method: 'get' });
export const updateFirewallRule = (data: { action: 'add' | 'remove'; zone: string; rule_type: 'service' | 'port'; value: string; protocol?: 'tcp' | 'udp' }) => request({ url: '/system/network/firewall/rules/update', method: 'post', data });