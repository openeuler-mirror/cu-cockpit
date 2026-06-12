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
