export default interface socket {
  websocket: WebSocket | null;
  connectURL: string;
  socket_open: boolean;
  hearbeat_timer: number;
  hearbeat_interval: number;
  is_reconnect: boolean;
  reconnect_count: number;
  reconnect_current: number;
  reconnect_timer: number;
  reconnect_interval: number;
  init(receiveMessage: Function | null, closeCallback?: Function | null, wsUrl?: string): void;
  heartbeat(): void;
  send(data: any, callback?: Function | null): void;
  close(): void;
  reconnect(): void;
}