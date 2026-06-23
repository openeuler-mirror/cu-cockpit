import {request} from '/@/utils/service';
import {PageQuery, AddReq, DelReq, EditReq, InfoReq} from '@fast-crud/fast-crud';

export const apiPrefix = '/api/system/message_center/';

export function GetList(query: PageQuery) {
    return request({
        url: apiPrefix,
        method: 'get',
        params: query,
    });
}

export function GetObj(id: InfoReq) {
    return request({
        url: apiPrefix + id + '/',
        method: 'get',
    });
}
