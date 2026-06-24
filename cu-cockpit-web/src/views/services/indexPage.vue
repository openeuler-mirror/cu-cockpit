<template v-else>

                                
</template>
<script setup lang="ts">

import { reactive, ref, onMounted, nextTick, watch } from "vue"
import { serviceStatus, runServiceManage } from '/@/api/run/run'
import { ElMessageBox } from 'element-plus';
import { errorNotification, successNotification } from '/@/utils/message';
import { storeToRefs } from 'pinia';
import { userPermissiom } from '/@/stores/userPermissiom';
const storeUserPermissiom = userPermissiom();
const { u_Permission } = storeToRefs(storeUserPermissiom);
const tableRef = ref();
const tableData= reactive({
    loading: true,
    data: [],
    history: [],

});
const tablekey = ref(0);
const searchName = ref<string>("");
//精确搜索
const searchInput = () => {
    siftfunction();
}

const value = ref<string[]>([])
const options = [
    {
        value: 'active',
        label: '运行中',
    },
    {
        value: 'inactive',
        label: '未运行',
    },
]

const startChange = (value: string[]) => {
    siftfunction();
}


//文件状态
const fileType = ref<string[]>([]);
const fileOptions = [
    {
        value: 'enabled',
        label: '启用'
    },
    {
        value: 'disabled',
        label: '禁用'
    }, {
        value: 'static',
        label: '静态'
    },
    {
        value: 'alias',
        label: '别名'
    },
    {
        value: 'indirect',
        label: '间接的'
    },
    {
        value: 'masked',
        label: '已屏蔽'
    },
]

const getService = () => {
    serviceStatus().then(res => {
        tableData.data = res;
        tableData.history = res;
        tableData.loading = false;
        if (searchName.value != '' || value.value.length > 0 || fileType.value.length > 0) {
            siftfunction()
        }
    })
}

const fileChange = () => {
    siftfunction()
}

onMounted(() => {
    getService();
})
type statusType = 'start' | 'stop' | 'restart';
//修改状态
</script>
<style>
</style>