export type TerminalAuthType = 'password' | 'key';
export type TerminalConnectionState = 'idle' | 'authenticating' | 'connecting' | 'connected' | 'closed' | 'failed';

export interface TerminalHistoryItem {
	hostname: string;
	port: number;
	username: string;
	authType: TerminalAuthType;
	connectedAt: string;
}

export interface TerminalSessionModel {
	id: string;
	title: string;
	hostname: string;
	port: number;
	username: string;
	authType: TerminalAuthType;
	password: string;
	privatekey: string;
	passphrase: string;
	term: string;
	state: TerminalConnectionState;
	error: string;
	cols: number;
	rows: number;
}