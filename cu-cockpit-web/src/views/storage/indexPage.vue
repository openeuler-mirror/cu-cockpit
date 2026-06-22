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
</script>
<style scoped lang="scss">
</style>
