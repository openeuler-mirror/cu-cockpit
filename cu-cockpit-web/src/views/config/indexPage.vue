<template #label>

                                <div class="cell-item">SHA256</div>
                            
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

</style>
