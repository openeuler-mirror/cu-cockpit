import { request } from '/@/utils/service';
import { UserPageQuery, AddReq, DelReq, EditReq, InfoReq } from '@fast-crud/fast-crud';
import XEUtils from 'xe-utils';

export const apiPrefix = '/api/system/system_config/';
export function GetList(query: UserPageQuery) {
	return request({
		url: apiPrefix,
		method: 'get',
		params: query,
	});
}
export function GetObj(id: InfoReq) {
	return request({
		url: apiPrefix + id,
		method: 'get',
	});
}
