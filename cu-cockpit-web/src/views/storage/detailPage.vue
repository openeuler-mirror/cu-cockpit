<template #header>

                    <div class="card-header">
                        <span>{{ device.pttype ? device.pttype.toUpperCase() + ' 分区' : '分区' }}</span>
                    </div>
                
</template>
<script lang="ts" setup name="storageDetail">

import { onMounted, ref } from 'vue';
import { hardInfo } from '/@/api/run/run';
import { useRouter } from 'vue-router';

const props = defineProps({
    name: {
        type: String,
        required: true
    }
});
const router = useRouter();

const loading = ref(false);

interface Hardware {
    ID_MODEL: string;
    ID_REVISION: string;
    ID_SERIAL_SHORT: string;
    ID_VENDOR: string;
}
interface Device {
    name: string;
    type: string;
    fstype: string;
    pttype: string;
    size: string;
    mountpoint: string;
    partuuid: string;
    uuid: string;
    children: Device[];
    hardware: Hardware;
}
const device = ref<Device>({
    name: '',
    type: '',
    fstype: '',
    pttype: '',
    size: '',
    mountpoint: '',
    partuuid: '',
    uuid: '',
    children: [],
    hardware: {
        ID_MODEL: '',
        ID_REVISION: '',
        ID_SERIAL_SHORT: '',
        ID_VENDOR: '',
    }
});
const breadcrumbs = ref<string[]>([])
const getStorageInfo = () => {
    loading.value = true;
    hardInfo('storage').then((res) => {
        const blockDevices = res.blockdevices;
        device.value = findDeviceByName(blockDevices, props.name, [])!;
        loading.value = false;
    });
};
const findDeviceByName = (devices: Device[], targetName: string, currentPath: string[]): Device | null => {
    for (const device of devices) {
        const newPath = [...currentPath, device.name];
        if (device.name === targetName) {
            breadcrumbs.value = newPath;
            return device;
        }
        if (device.children?.length) {
            const found = findDeviceByName(device.children, targetName, newPath);
            if (found) return found;
        }
    }
    return null;
};

// 分区
const ptDesc = [
    { label: '名称', key: 'name', icon: 'icon-mingcheng', color: '--el-color-success' },
    { label: '分区UUID', key: 'partuuid', icon: 'icon-fuwenben', color: '--el-color-success' },
    { label: '分区类型', key: 'pttype', icon: 'icon-shebeileixing', color: '--el-color-success' },
    { label: '大小', key: 'size', icon: 'icon-cunchudaxiao', color: '--el-color-success' },
];
// 文件系统
const fsDesc = [
    { label: '名称', key: 'name', icon: 'icon-mingcheng', color: '--el-color-success' },
    { label: 'UUID', key: 'uuid', icon: 'icon-fuwenben', color: '--el-color-success' },
    { label: '文件系统类型', key: 'fstype', icon: 'icon-shebeileixing', color: '--el-color-success' },
    { label: '挂载点', key: 'mountpoint', icon: 'icon-guazaidian', color: '--el-color-success' },
];
// 硬件信息
const hwDesc = [
    { label: '厂商', key: 'ID_VENDOR', icon: 'icon-mingcheng', color: '--el-color-success' },
    { label: '型号', key: 'ID_MODEL', icon: 'icon-shebeileixing', color: '--el-color-success' },
    { label: 'Firmware version', key: 'ID_REVISION', icon: 'icon-lishibanben', color: '--el-color-success' },
    { label: 'Serial number', key: 'ID_SERIAL_SHORT', icon: 'icon-bianhao1', color: '--el-color-success' },
    { label: '大小', key: 'size', icon: 'icon-cunchudaxiao', color: '--el-color-success' },
];

const toDetail = (row: { name: string }) => {
    router.push({
        name: 'storageDetail',
        params: {
            name: row.name,
        },
    });
};

onMounted(() => {
    getStorageInfo();
});
</script>
<style scoped lang="scss">
</style>
