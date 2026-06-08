import request from '/@/utils/request';
type monitorMode = "all" | "cpu" | "disk" | "memory" | "network";
type hardMode = 'cpu' | 'disk' | 'network' | 'system' | 'bios' | 'os_system' | 'storage';
/**
 * 监控系统的资源状态
 * @param mode 
 * @returns 
 */
export const monitorStatus = (mode: monitorMode) => {
    return request({
        url: '/rescrouce/monitor/monitor_status.sh',
        method: 'get',
        params: { mode },
    });
}


/**
 * 获取硬件静态信息
 * @param mode 
 * @returns 
 */
export const hardInfo = (mode: hardMode) => {
    return request({
        url: '/rescrouce/monitor/hard_info.sh',
        method: 'get',
        params: { mode },
    });
}

interface MemoryItem {
  ID: string;
  内存拓扑: string;
  类型: string;
  大小: string;
  状态: string;
  Rank: string;
  速度: string;
}
