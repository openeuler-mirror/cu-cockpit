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
const setStatus = (status: statusType, data: {[key: string]: string}) => {
    //不是管理员权限
    if (u_Permission.value != 'root') {
        ElMessageBox.alert('被限制访问模式下不可操作，请切换到管理员模式', '提示', {
            confirmButtonText: '确定',
            callback: () => {
            }
        })
        return false;
    }
    let typeText:{[key: string]: string} = {
        'start': '启动',
        'stop': "停止",
        'restart': '重启',
    }

    ElMessageBox.confirm(`是否确定${typeText[status]} ${data['服务名称']} 服务`, '温馨提示', {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning',
        center: true,
        customClass: 'd-message'
    }).then(async (res) => {
        if (res == 'confirm') {
            await runServiceManage({
                service_name: data['服务名称'],
                operation: status
            }).then(res => {
                console.log(res);
                if (res.return_code == 0) {
                    successNotification(`${data['服务名称']}${typeText[status]}成功`)
                    getService();
                }else if(res.return_code == 4){
                    errorNotification(`${data['服务名称']}${typeText[status]}失败`)
                }
            }, err => {
                let tmpErr = JSON.parse(err.request.responseText);
                if(tmpErr.return_code == 4){
                    errorNotification(`${data['服务名称']}服务出现${tmpErr.error}导致${typeText[status]}失败`)
                }
             })
        }
    }, err => { console.log(err) })
}

const siftfunction = () => {
    let siftArray = tableData.history;
    if (searchName.value != '') {
        let tmp = searchName.value.toLowerCase();
        siftArray = siftArray.filter((item: { [x: string]: string; }) =>
            item['服务名称'].toLowerCase().indexOf(tmp) !== -1 || item['描述'].toLowerCase().indexOf(tmp) !== -1
        )
    }
    if (value.value.length > 0) {
        siftArray = siftArray.filter((item: { [x: string]: string; }) => {
            if (value.value.length == 1) {
                return item['运行状态'] == value.value[0];
            } else {
                return item['运行状态'] != "N/A";
            }
        })
    }
    if (fileType.value.length > 0) {
        let tmp = fileType.value;
        siftArray = siftArray.filter((item: { [x: string]: string; }) => {
            if (tmp.length < 6) {
                return tmp.indexOf(item['注册状态']) !== -1;
            } else {
                return item['注册状态'] != "N/A";
            }
        })
    }
    tableData.data =siftArray;   
    tablekey.value =Math.random();
}

watch(() => tableData.data, () => {
    nextTick(() => {
         if (tableRef.value) {
            // 先重新计算布局
            tableRef.value.doLayout();
            
            // 再重置滚动位置
            setTimeout(() => {
                try {
                    tableRef.value.setScrollTop(0);
                } catch (e) {
                    console.warn('Failed to reset scroll position:', e);
                }
            }, 50);
        }
    })
}, { deep: true });

// 工具函数
function isDisabled(status: string): boolean {
    return ['disabled'].includes(status);
}
function isEnabled(status: string): boolean {
    return ['enabled', 'enabled-runtime'].includes(status);
}

function getRegisterStatusLabel(status: string): string {
    const map: Record<string, string> = {
        static: '静态',
        alias: '别名',
        indirect: '间接的',
        masked: '屏蔽的'
    };
    return map[status];
}

function canOperate(row: {[key:string]: string}): boolean {
    const validStates = ['enabled', 'enabled-runtime', 'disabled'];
    return validStates.includes(row['注册状态']);
}
</script>
<style>

</style>