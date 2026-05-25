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
