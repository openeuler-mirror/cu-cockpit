import request from '/@/utils/request';
type logParams = {
    since?: string,
    until?: string,
    priority?: string | number,
    service?: string,
    identifier?: string,
    keyword?: string,
    limit?: number | string,
    boot?: string,
    cursor?: string,
    output_format?: string,
}
export const logs = (params: logParams) => {
    return request({
        url: '/logs/logs/',
        method: 'get',
        params
    });
}

export const getBoot = () => {
    return request({
        url: '/logs/boot/',
        method: 'get',
    });
}