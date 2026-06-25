<template>
    <div class="box-container">
        <el-card class="box-card">
            <el-table :data="storageTableData" class="hover-text-table" row-key="name" default-expand-all size="large"
                v-loading="storageLoading" @row-click="toDetail" :header-cell-style="{ background: '#f5f7fa' }">
                <el-table-column prop="name" label="ID" min-width="300" />
                <el-table-column prop="type" label="类型" min-width="300" />
                <el-table-column prop="mountpoint" label="位置" min-width="300" />
                <el-table-column prop="size" label="大小" min-width="300" align="right" />
            </el-table>
        </el-card>
    </div>
</template>

<script lang="ts" setup name="storageIndex">
import { onMounted, ref } from 'vue';
import { hardInfo } from '/@/api/run/run';
import { useRouter } from 'vue-router';

const router = useRouter();

const storageTableData = ref([]);
const storageLoading = ref(false);

const getStorageInfo = () => {
    storageLoading.value = true;
    hardInfo('storage').then((res) => {
        storageTableData.value = res.blockdevices;
        storageLoading.value = false;
    });
};

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
}
</style>
