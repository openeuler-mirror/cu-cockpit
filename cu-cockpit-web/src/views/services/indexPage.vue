<template>
    <div>
        <div class="table-div" style="height: calc(100vh - 130px);overflow: hidden;">
            <el-affix :offset="76">
                <div class="top-tabs">
                    <!-- <div class="top-l">
                        <div class="item">服务</div>
                    </div> -->
                    <div class="sift">
                        <div class="flex gap-4 items-center">
                            <el-input v-model="searchName" style="width: 240px" size="default" placeholder="根据名称或描述进行过滤"
                                prefix-icon="Search" clearable @input="searchInput" />
                            <el-select v-model="value" multiple clearable @change="startChange" :reserve-keyword="false"
                                placeholder="运行状态" style="width: 190px">
                                <el-option v-for="item in options" :key="item.value" :label="item.label"
                                    :value="item.value" />
                            </el-select>
                            <el-select v-model="fileType" multiple collapse-tags collapse-tags-tooltip clearable
                                @change="fileChange" :reserve-keyword="false" placeholder="注册状态" style="width: 300px">
                                <el-option v-for="item in fileOptions" :key="item.value" :label="item.label"
                                    :value="item.value" />
                            </el-select>
                        </div>
                    </div>
                </div>
            </el-affix>
            <div style="height: calc(100vh - 222px);">
                <el-table :data="tableData.data" v-loading="tableData.loading" ref="tableRef" height="100%"
                    :header-cell-style="{ background: '#f5f7fa' }" size="large"
                    style="width: 100%;line-height: 1.5;"  :key="tablekey">
                    <el-table-column prop="服务名称" width="350" label="服务名称">
                        <template #default="scope">
                            <div style="color:#0066cc;line-height: 1.5;padding-top:14px;padding-bottom: 14px; cursor: default;">
                                {{ scope.row.服务名称 }}</div>
                        </template>
                    </el-table-column>
                    <el-table-column prop="描述" label="描述">
                        <template #default="scope">
                            <div style="width: 90%;cursor: default" >{{ scope.row.描述 }}</div>
                        </template>
                    </el-table-column>
                    <el-table-column prop="运行状态" width="110" label="运行状态"  align="center">
                        <template #default="scope">
                            <div v-if="scope.row.运行状态 != 'N/A'" style="cursor: default"> 
                                <el-tag v-if="scope.row.运行状态 == 'inactive'" type="info">未运行</el-tag> 
                                <el-tag  v-else-if="scope.row.运行状态 == 'active'" type="success">运行中</el-tag> 
                            </div>
                            <div v-else>
                            </div>
                        </template>
                    </el-table-column>
                    <el-table-column prop="注册状态" width="130" label="注册状态" align="center">
                        <template #default="scope">
                            <div v-if="scope.row.注册状态 != 'N/A'" style="cursor: default">
                                <el-tag  v-if="isDisabled(scope.row.注册状态)" type="info" round style="width: 90px;font-size: 14px;">禁用</el-tag>
                                <el-tag  v-else-if="isEnabled(scope.row.注册状态)" round style="width: 90px;font-size: 14px;">启用</el-tag>
                                <div v-else style="text-align: center;">{{ getRegisterStatusLabel(scope.row.注册状态) }}</div>
                            </div>
                            <div v-else>
                            </div>
                        </template>
                    </el-table-column>
                    <el-table-column label="操作" width="160" align="center">
                        <template #default="scope">
                            <div style="margin: auto;">
                                <template v-if="canOperate(scope.row)">
                                    <el-button link type="primary" @click="setStatus('start', scope.row)"
                                        :disabled="scope.row.运行状态 == 'active'">启动</el-button>
                                    <el-button link type="primary"
                                        @click="setStatus('restart', scope.row)">重启</el-button>
                                    <el-button link type="danger" @click="setStatus('stop', scope.row)"
                                        :disabled="scope.row.运行状态 != 'active'">停止</el-button>
                                </template>
                                <template v-else>
                                </template>
                            </div>
                        </template>
                    </el-table-column>
                </el-table>
            </div>
        </div>

    </div>
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
<style scoped lang="scss">
.top-tabs {
    background: var(--el-color-white);
    position: relative;
    display: flex;
    flex-wrap: wrap;
    margin-bottom: 20px;
    //文字不可选
    -moz-user-select: none;
    -webkit-user-select: none;
    -ms-user-select: none;
    -khtml-user-select: none;
    user-select: none;

}

.top-l {
    display: flex;
    align-items: center;
    max-width: 50%;

    .item {
        position: relative;
        font-size: 14px;
        line-height: 1.5;
        margin-right: 16px;
        padding-left: 4px;

        .title {
            padding-left: 4px;
            cursor: pointer;
        }
    }

}

.sift {
    width: 100%;
    margin-top: 10px;
}

.table-div {
    margin: 20px 16px 0;
    padding: 10px 16px;
    background: var(--el-color-white);
    border-radius: 8px;
}
</style>
<style>
.d-message .el-message-box__content .el-message-box__container .el-message-box__message {

    font-size: 18px;
    line-height: 1.5;
    padding: 20px 0;
    color: #000;

}
 
</style>