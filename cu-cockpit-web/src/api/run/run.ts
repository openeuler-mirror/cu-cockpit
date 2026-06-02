import request from '/@/utils/request';
type monitorMode = "all" | "cpu" | "disk" | "memory" | "network";
type hardMode = 'cpu' | 'disk' | 'network' | 'system' | 'bios' | 'os_system' | 'storage';
/**
 * 监控系统的资源状态
 * @param mode 
 * @returns 
 */
