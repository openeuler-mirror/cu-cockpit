import { request } from "/@/utils/service";
// 2025-0904
export function login(params: object) {
    return request({
        url: '/auth/login/',
        method: 'post',
        data: params
    });
}