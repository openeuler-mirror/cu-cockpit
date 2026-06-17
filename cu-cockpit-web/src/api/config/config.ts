import request from '/@/utils/request';
type ModeType = 'sshkey' | 'gethostname' | 'time' | 'get';

interface SshKeyItem {
    [algorithm: string]: {
        sha256: string;
        md5: string;
    };
}

interface TimeResponse {
    time: string;
    zone: string;
    ntp: string;
}

// 函数重载
export function configGet(mode: 'sshkey'): Promise<SshKeyItem[]>;
export function configGet(mode: 'gethostname' | 'get'): Promise<string>;
export function configGet(mode: 'time'): Promise<TimeResponse>;
export function configGet(mode: ModeType, key?: string): Promise<unknown>;
export function configGet(mode: ModeType, key?: string): Promise<unknown> {
    return request({
        url: '/config/get/config.sh',
        method: 'get',
        params: { mode, key }
    });
}


type TimeType = {
    type: string,
    time: string
}
/**
 * 修改系统时间
 * @param data
 * @returns 
 */
export const timeSet = (data: TimeType) => {
    return request({
        url: '/config/set/set_time.sh',
        method: 'post',
        data
    });
}

type hostType = {
    hostname: string,
}
/**
 * 修改主机名
 * @param data
 * @returns 
 */
export const hostSet = (data: hostType) => {
    return request({
        url: '/config/set/config.sh',
        method: 'post',
        data
    });
}

/**
 * 修改文件
 * @param data
 * @returns 
 */
export const configUpdate = (data: string, file_path: string, dir_path: string) => {
    return request({
        url: '/config/update/',
        method: 'post',
        headers: {
            'Content-Type': 'text/plain'
        },
        params: {
            file_path,
            dir_path
        },
        data
    });
}
