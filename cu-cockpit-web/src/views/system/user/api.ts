import { request,downloadFile } from '/@/utils/service';
import { PageQuery, AddReq, DelReq, EditReq, InfoReq } from '@fast-crud/fast-crud';

export const apiPrefix = '/api/system/user/';

export function GetDept(query: PageQuery) {
    return request({
        url: "/api/system/dept/all_dept/",
        method: 'get',
        params: query,
    });
}

export function GetList(query: PageQuery) {
    return request({
        url: apiPrefix,
        method: 'get',
        params: query,
    });
}
