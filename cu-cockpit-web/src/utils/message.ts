import { ElMessage, ElNotification, MessageOptions } from 'element-plus';

export function message(message: string, option?: MessageOptions) {
	ElMessage({ message, ...option });
}
export function successMessage(message: string, option?: MessageOptions) {
	ElMessage({ message, type: 'success' });
}
export function warningMessage(message: string, option?: MessageOptions) {
	ElMessage({ message, ...option, type: 'warning' });
}
