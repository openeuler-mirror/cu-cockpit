import mitt, { Emitter } from 'mitt';

export interface TaskProps {
	name: string;
	custom?: any;
}
