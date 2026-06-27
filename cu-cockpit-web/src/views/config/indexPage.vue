<template>
    <div class="box-container config-container">
        <el-card>
            <div class="card-box">
                <el-card v-for="item in desc" :key="item.key" class="card-item">
                    <div class="icon">
                        <i class="font32 iconfont" :class="item.icon"></i>
                    </div>
                    <div class="label">
                        {{ item.label }}
                    </div>
                    <div class="content">
                        {{ state[item.key] }}
                        <el-tooltip :content="item.edit ? '编辑' : '查看'" placement="bottom" effect="light"
                            :show-arrow="false">
                            <el-icon @click="showDetail(item.key)">
                                <Edit v-if="item.edit" />
                                <View v-else />
                            </el-icon>
                        </el-tooltip>
                    </div>
                </el-card>
            </div>
        </el-card>
        <el-card class="mt20">
            <el-select v-model="fileName" placeholder="请选择配置文件" style="width: 20%">
                <el-option v-for="item in options" :key="item.value" :label="item.value" :value="item.value" />
            </el-select>
            <el-button type="primary" style="margin-left: 10px;" @click="changeFile(false)"
                :disabled="!fileName">查询</el-button>
            <el-button type="warning" @click="changeFile(true)" :disabled="!fileName">修改</el-button>
            <el-input v-model="fileContent" :rows="21" type="textarea" spellcheck="false"
                :disabled="!updateFile || !isAdmin" :class="{ 'textarea-update': updateFile && isAdmin }" />
            <div class="save-btn" v-show="updateFile && isAdmin">
                <el-button type="primary" @click="saveFile" :loading="btnLoading">保存</el-button>
                <el-button @click="cancelFile">取消</el-button>
            </div>
        </el-card>
        <el-drawer v-model="hostDrawer" title="修改主机名" direction="rtl">
            <el-form ref="hostFormRef" label-position="top" label-width="100px" :model="hostForm" :rules="hostRules"
                class="drawer-content">
                <el-form-item label="主机名" prop="hostname">
                    <el-input v-model="hostForm.hostname" placeholder="请输入主机名" clearable spellcheck="false" />
                </el-form-item>
                <el-form-item class="btn-row">
                    <el-button type="primary" @click="submitHostForm(hostFormRef)" :loading="btnLoading">保存</el-button>
                    <el-button @click="hostDrawer = false">取消</el-button>
                </el-form-item>
            </el-form>
        </el-drawer>
        <el-drawer v-model="timeDrawer" title="修改系统时间" direction="rtl">
            <el-form ref="timeFormRef" label-position="top" label-width="100px" :model="timeForm" :rules="timeRules"
                class="drawer-content">
                <el-form-item label="时区" prop="zone">
                    <el-input v-model="timeForm.zone" disabled />
                </el-form-item>
                <el-form-item label="设置时间" prop="type">
                    <el-select v-model="timeForm.type" @change="handleType">
                        <el-option v-for="item in timeTypeOptions" :key="item.value" :label="item.label"
                            :value="item.value" />
                    </el-select>
                </el-form-item>
                <el-form-item v-if="timeForm.type === 'settime'" prop="time">
                    <el-date-picker v-model="timeForm.time" type="datetime" placeholder="请选择时间" style="width: 100%;"
                        value-format="YYYY-MM-DD HH:mm:ss" />
                </el-form-item>
                <el-form-item class="btn-row">
                    <el-button type="primary" @click="submitTimeForm(timeFormRef)" :loading="btnLoading">保存</el-button>
                    <el-button @click="timeDrawer = false">取消</el-button>
                </el-form-item>
            </el-form>
        </el-drawer>
        <el-drawer v-model="keyDrawer" title="主机 SSH 密钥指纹" direction="rtl">
            <div class="drawer-content">
                <el-card v-for="(item, index) in state.sshkeys" :key="index" class="mb10">
                    <template #header>
                        <span>{{ item.name }}</span>
                    </template>
                    <el-descriptions direction="vertical" :column="1" border>
                        <el-descriptions-item>
                            <template #label>
                                <div class="cell-item">MD5</div>
                            </template>
                            {{ item.md5 }}
                        </el-descriptions-item>
                        <el-descriptions-item>
                            <template #label>
                                <div class="cell-item">SHA256</div>
                            </template>
                            {{ item.sha256 }}
                        </el-descriptions-item>
                    </el-descriptions>
                </el-card>
            </div>
        </el-drawer>
    </div>
</template>

<script lang="ts" setup name="configIndex">
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue';
import { configGet, hostSet, timeSet, configUpdate } from '/@/api/config/config';
import type { FormInstance, FormRules } from 'element-plus';
import { ElMessage, ElMessageBox } from 'element-plus';
import dayjs from 'dayjs'
import { storeToRefs } from 'pinia';
import { userPermissiom } from '/@/stores/userPermissiom';
const storeUserPermissiom = userPermissiom();
const { u_Permission } = storeToRefs(storeUserPermissiom);

const isAdmin = computed(() => u_Permission.value === 'root');

interface State {
    hostname: string;
    time: string;
    zone: string;
    type: string;
    showssh: string;
    sshkeys: Array<{ name: string, md5: string, sha256: string }>;
    [key: string]: string | Array<{ name: string, md5: string, sha256: string }>;
}
const state = reactive<State>({
    hostname: '',
    time: '',
    zone: '',
    type: '',
    showssh: '显示指纹',
    sshkeys: []
});
const desc = [
    { label: '主机名', key: 'hostname', icon: 'icon-zhuji', edit: true },
    { label: '系统时间', key: 'time', icon: 'icon-yunhangshichang', edit: true },
    { label: '安全 shell 密钥', key: 'showssh', icon: 'icon-miyue', edit: false },
];



const getConfig = () => {
    configGet('gethostname').then((res) => {
        state.hostname = res.trim();
    });
    configGet('time').then((res) => {
        state.time = res.time;
        state.zone = res.zone;
        state.type = res.ntp == 'true' ? 'autotime' : 'settime';
    });
    configGet('sshkey').then((res) => {
        state.sshkeys = res.map((item) => {
            const name = Object.keys(item)[0]
            return {
                name: name,
                ...item[name]
            }
        });
    });
};
const getTime = () => {
    configGet('time').then((res) => {
        state.time = res.time;
        state.zone = res.zone;
        state.type = res.ntp == 'true' ? 'autotime' : 'settime';
    });
};

const options = [
    {
        value: '.bashrc',
    }
]
const fileName = ref('');
const updateFile = ref(false)
const fileContent = ref('');

const changeFile = (flag: boolean) => {
    if (flag && !isAdmin.value) {
        ElMessageBox.alert('被限制访问模式下不可操作，请切换到管理员模式', '提示', {
            confirmButtonText: '确定',
            callback: () => {
            }
        })
        return;
    }
    updateFile.value = flag;
    getFile(fileName.value);
}

const getFile = (name: string) => {
    configGet('get', name).then((res) => {
        fileContent.value = res as string;
    });
};

const saveFile = () => {
    btnLoading.value = true;
    ElMessageBox.confirm(
        '是否确认修改？',
        '温馨提示',
        {
            confirmButtonText: '确认',
            cancelButtonText: '取消',
            type: 'warning',
        }
    )
        .then(() => {
            configUpdate(fileContent.value, fileName.value, '').then((res) => {
                ElMessage.success(res.message)
                btnLoading.value = false;
                updateFile.value = false;
                getFile(fileName.value);
            });
        })
        .catch(() => {
            btnLoading.value = false;
        })
}
const cancelFile = () => {
    updateFile.value = false;
    getFile(fileName.value);
}

const hostDrawer = ref(false);
const timeDrawer = ref(false);
const keyDrawer = ref(false);
const btnLoading = ref(false);

const showDetail = (key: string) => {
    if (key === 'hostname') {
        if (!isAdmin.value) {
            ElMessageBox.alert('被限制访问模式下不可操作，请切换到管理员模式', '提示', {
                confirmButtonText: '确定',
                callback: () => {
                }
            })
            return;
        }
        hostDrawer.value = true;
        hostForm.hostname = state.hostname;
        // 重置表单校验状态
        if (hostFormRef.value) {
            hostFormRef.value.clearValidate();
        }
    } else if (key === 'time') {
        if (!isAdmin.value) {
            ElMessageBox.alert('被限制访问模式下不可操作，请切换到管理员模式', '提示', {
                confirmButtonText: '确定',
                callback: () => {
                }
            })
            return;
        }
        timeDrawer.value = true;
        timeForm.time = dayjs().format('YYYY-MM-DD HH:mm:ss');
        timeForm.zone = state.zone;
        timeForm.type = state.type;

        // 重置表单校验状态
        if (timeFormRef.value) {
            timeFormRef.value.clearValidate();
        }
    } else if (key === 'showssh') {
        keyDrawer.value = true;
    }
}

interface HostRuleForm {
    hostname: string
}
const hostForm = reactive<HostRuleForm>({
    hostname: '',
})
const hostFormRef = ref<FormInstance>()
const hostRules = reactive<FormRules<HostRuleForm>>({
    hostname: [
        { required: true, message: '请输入主机名', trigger: 'blur' },
    ],
});
const submitHostForm = async (formEl: FormInstance | undefined) => {
    if (!formEl) return
    await formEl.validate((valid) => {
        if (valid) {
            btnLoading.value = true;
            hostSet(hostForm).then((res) => {
                ElMessage.success(res.message)
                btnLoading.value = false;
                hostDrawer.value = false;
                getConfig();
            }).catch(() => {
                btnLoading.value = false;
            })
        }
    })
}

const timeTypeOptions = [
    { value: 'settime', label: '手动的' },
    { value: 'autotime', label: '自动使用NTP' },
]

interface TimeRuleForm {
    zone: string,
    type: string,
    time: string,
}
const timeForm = reactive<TimeRuleForm>({
    zone: '',
    type: '',
    time: '',
})
const timeFormRef = ref<FormInstance>()
const timeRules = reactive<FormRules<TimeRuleForm>>({
    zone: [
        { required: true, message: '请输入时区', trigger: 'blur' },
    ],
    type: [
        { required: true, message: '请选择时间类型', trigger: 'change' },
    ],
    time: [
        { required: true, message: '请选择时间', trigger: 'change' },
    ],
});
const submitTimeForm = async (formEl: FormInstance | undefined) => {
    if (!formEl) return
    await formEl.validate((valid) => {
        if (valid) {
            btnLoading.value = true;
            timeForm.time = timeForm.time + ' +0800';
            timeSet(timeForm).then((res) => {
                ElMessage.success(res.message)
                btnLoading.value = false;
                timeDrawer.value = false;
                getConfig();
                setTimeout(() => {
                    getConfig();
                }, 7000);
            }).catch(() => {
                btnLoading.value = false;
            })
        }
    })
}

const handleType = (value: string) => {
    if (value === 'settime') {
        timeForm.time = dayjs().format('YYYY-MM-DD HH:mm:ss');
    }
}
const timer = ref();
onMounted(() => {
    getConfig();
    timer.value = setInterval(() => {
        getTime();
    }, 30000);
});
onUnmounted(() => {
    clearInterval(timer.value);
});
</script>

<style scoped lang="scss">
.box-container {
    padding: 15px 20px;

    .card-box {
        display: flex;
        gap: 20px;

        .card-item {
            flex: 1 1 calc(33.33% - 20px);
            background: linear-gradient(to right, #f4f5f5, #e0ebf7);

            &:hover {
                box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.2);
                transition: all ease 0.3s;
            }

            .icon {
                width: 50px;
                height: 50px;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 10px;
                background: #E4EAF5;

                .iconfont {
                    color: #548DFE;
                }
            }

            .label {
                font-size: 14px;
                color: #333333;
                margin-bottom: 10px;
            }

            .content {
                font-size: 16px;
                color: #585858;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .el-icon {
                font-size: 20px;
                color: var(--el-color-primary);
                cursor: pointer;
            }
        }
    }

    .mt20 {
        margin-top: 20px;
    }

    .el-textarea {
        margin-top: 20px;

        ::v-deep .el-textarea__inner {
            resize: none;
            box-shadow: none;
            border: none;
        }
    }

    .textarea-update ::v-deep .el-textarea__inner {
        color: #fff;
        border: none;
        background-color: #000;
    }

    .textarea-update :deep(.el-textarea__inner)::-webkit-scrollbar-thumb {
        background: #b3b3b3;
    }

    .save-btn {
        margin-top: 20px;
        text-align: right;
    }

    .drawer-content {
        margin: 20px;

        .btn-row ::v-deep .el-form-item__content {
            display: flex;
            justify-content: flex-end;
        }

        .ntp-item ::v-deep .el-form-item__content {
            display: flex;
            justify-content: space-between;

            .el-input {
                flex: 1;
            }

            .el-button {
                margin-left: 10px;

                .el-icon {
                    margin-right: 0;
                }
            }
        }

        .add-ntp {
            text-align: right;
            margin-bottom: 10px;

            ::v-deep .el-icon {
                margin-right: 0;
            }
        }
    }
}
</style>
