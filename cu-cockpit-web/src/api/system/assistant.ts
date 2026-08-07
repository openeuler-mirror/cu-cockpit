import request from '/@/utils/request';


export const assistantRequest = <T = any>(
	url: string,
	method: 'get' | 'post' = 'get',
	data?: Record<string, unknown>,
	params?: Record<string, unknown>,
): Promise<T> => request({ url, method, data, params });
