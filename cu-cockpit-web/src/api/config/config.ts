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
