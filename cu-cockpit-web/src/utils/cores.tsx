import mitt, { Emitter } from 'mitt';

export interface TaskProps {
	name: string;
	custom?: any;
}

// 定义自定义事件类型
export type BusEvents = {
	onNewTask: TaskProps | undefined;
};

export interface Task {
	id: number;
	handle: string;
	data: any;
	createTime: Date;
	custom?: any;
}

export interface Core {
	bus: Emitter<BusEvents>;
	// eslint-disable-next-line no-unused-vars
	showNotification(body: string, title?: string): Notification | undefined;
	taskList: Map<String, Task>;
}

const bus = mitt<BusEvents>();
export function getSystemNotification(body: string, title?: string) {
	if (!title) {
		title = '通知';
	}
	return new Notification(title ?? '通知', {
		body: body,
	});
}
