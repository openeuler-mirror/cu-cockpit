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

</script>
<style scoped lang="scss">
</style>
