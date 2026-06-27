<template>
    <div class="box-container">
        <el-card v-loading="loading">
            <template #header>
                <el-breadcrumb separator="/">
                    <el-breadcrumb-item :to="{ path: '/storage' }">存储</el-breadcrumb-item>
                    <el-breadcrumb-item :to="{ path: '/storage/detail/' + item }" v-for="item in breadcrumbs"
                        :key="item">
                        {{ item }}
                    </el-breadcrumb-item>
                </el-breadcrumb>
            </template>
            <el-card v-if="device.type && device.type == 'disk' || device.type == 'rom'">
                <template #header>
                    <div class="card-header">
                        <span>Hard Disk Drive</span>
                    </div>
                </template>
                <div class="card-box">
                    <el-card v-for="item in hwDesc" :key="item.key" shadow="never" class="hard-card">
                        <div class="card-item">
                            <div class="left-text">
                                <div class="label">
                                    <i class="iconfont" :class="item.icon" :style="{ color: `var(${item.color})` }"></i>
                                    {{ item.label }}
                                </div>
                                <div class="content" v-if="item.key == 'size'">{{ device[item.key] || '-' }}</div>
                                <div class="content" v-else>{{ device.hardware[item.key as keyof Hardware] || '-' }}</div>
                            </div>
                        </div>
                    </el-card>
                </div>
            </el-card>
            <template v-if="device.type && device.type !== 'disk' && device.type !== 'rom'">
                <el-card>
                    <template #header>
                        <div class="card-header">
                            <span>{{ device.pttype ? device.pttype.toUpperCase() + ' 分区' : '分区' }}</span>
                        </div>
                    </template>
                    <div class="card-box">
                        <el-card v-for="item in ptDesc" :key="item.key" shadow="never">
                            <div class="card-item">
                                <div class="left-text">
                                    <div class="label">
                                        <i class="iconfont" :class="item.icon"
                                            :style="{ color: `var(${item.color})` }"></i>
                                        {{ item.label }}
                                    </div>
                                    <div class="content">{{ device[item.key as keyof Device] || '-' }}</div>
                                </div>
                            </div>
                        </el-card>
                    </div>
                </el-card>
                <el-card class="margin-top">
                    <template #header>
                        <div class="card-header">
                            <span>{{ device.fstype ? device.fstype + ' 文件系统' : 'Unformatted data' }}</span>
                        </div>
                    </template>
                    <div class="card-box">
                        <el-card v-for="item in fsDesc" :key="item.key" shadow="never">
                            <div class="card-item">
                                <div class="left-text">
                                    <div class="label">
                                        <i class="iconfont" :class="item.icon"
                                            :style="{ color: `var(${item.color})` }"></i>
                                        {{ item.label }}
                                    </div>
                                    <div class="content">{{ device[item.key as keyof Device] || '-' }}</div>
                                </div>
                            </div>
                        </el-card>
                    </div>
                </el-card>
            </template>
            <el-card class="margin-top" shadow="hover" v-if="device.children && device.children.length">
                <template #header>
                    <div class="card-header">
                        <span>{{ device.pttype ? device.pttype.toUpperCase() + ' 分区' : '分区' }}</span>
                    </div>
                </template>
                <el-table :data="device.children" class="hover-text-table" size="large" stripe @row-click="toDetail"
                    :header-cell-style="{ background: '#f5f7fa' }">
                    <el-table-column label="名称" prop="name" min-width="150" />
                    <el-table-column label="类型" prop="type" min-width="150" />
                    <el-table-column label="文件系统" prop="fstype" min-width="150" />
                    <el-table-column label="分区类型" prop="pttype" min-width="150" />
                    <el-table-column label="大小" prop="size" align="right" min-width="100" />
                    <el-table-column label="挂载点" prop="mountpoint" min-width="150" />
                    <el-table-column label="分区UUID" prop="partuuid" min-width="350" />
                    <el-table-column label="UUID" prop="uuid" min-width="350" />
                </el-table>
            </el-card>
        </el-card>
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
.box-container {
    padding: 15px 20px;

    .margin-top {
        margin-top: 20px;
    }

    /* 鼠标移入行时，所有文本变色 */
    .hover-text-table :deep(.el-table__body tr:hover td .cell) {
        color: #409eff !important;
        cursor: pointer;
    }

    .card-header {
        font-size: 15px;
        font-weight: 600;
    }

    .card-box {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;

        .el-card {
            flex: 1 1 calc(25% - 20px);
            min-width: 330px;

            /* 中等屏幕：2个一行 */
            @media (max-width: 1800px) {
                flex: 1 1 calc(50% - 20px);
            }

            &:hover {
                box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.2);
                transition: all ease 0.3s;
            }

            .card-item {
                display: flex;

                .left-text {
                    flex: 1;

                    .label {
                        font-size: 12px;
                        font-weight: 500;
                        color: #909399;
                        display: flex;
                        align-items: center;

                        .iconfont {
                            font-size: 22px;
                            margin-right: 10px;
                        }
                    }

                    .content {
                        margin-top: 10px;
                        font-size: 15px;
                        color: #585858;
                    }
                }
            }
        }

        .hard-card {
            flex: 1 1 calc(20% - 20px);
            min-width: 200px;
        }
    }
}
</style>
