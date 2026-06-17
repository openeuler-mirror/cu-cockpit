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

/**
 * 获取内存插槽列表
 * @returns 
 */
export const memorySlot = (): Promise<MemoryItem[]> => {
    return request({
        url: '/rescrouce/monitor/memory_slot.sh',
        method: 'get',
    });
}

interface PciItem {
  等级: string;
  型号: string;
  厂商: string;
  插槽: string;
}

/**
 * 获取PCI列表信息
 * @returns 
 */
export const pciInfo = (): Promise<PciItem[]> => {
    return request({
        url: '/rescrouce/monitor/pci_info.sh',
        method: 'get',
    });
}
type operationType = 'start' | 'stop' | 'restart';
type ServiceManageType = {
    service_name: string,
    operation: operationType
}
/**
 * 用于服务启动、停止、重启等操作
 * @param data
 * @returns 
 */
export const runServiceManage = (data: ServiceManageType) => {
    return request({
        url: '/service/manage',
        method: 'post',
        data: JSON.stringify(data)
    });
}

export const serviceStatus = () => {
    return request({
        url: '/service/status',
        method: 'get',
    });
}
