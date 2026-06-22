import { request } from '/@/utils/service';
import { UserPageQuery, AddReq, EditReq, InfoReq, PageQuery } from '@fast-crud/fast-crud';

export const apiPrefix = '/api/system/dept/';

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
