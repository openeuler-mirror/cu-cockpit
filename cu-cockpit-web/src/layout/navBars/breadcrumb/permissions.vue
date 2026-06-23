<template>
    <div class="layout-permissions-dialog">
        <el-dialog v-model="state.isShowSearch" align-center :title="title" class="layout-permissions-z" width="680">
            <div v-if="state.isInput">
                <el-alert title="密码输入错误请，重新输入！" type="error" show-icon :closable="false"
                    style="border: 0px;margin-bottom: 4px;" v-if="errloading" />
                <div>
                    <span class="title">请输入账号 <span>{{ userInfos.username }}</span>的密码 :</span>
                    <el-input v-model="inputPassword" type="password" show-password style="width:400px" />
                </div>
            </div>
            <div v-else>

                <div>
                    限制访问模式会限制管理员权限。Web 控制台部分功能将会减少。
                    您的浏览器将会在不同会话之间记住您的访问级别。
                </div>
            </div>
            <template #footer v-if="username != 'root'">
                <div class="dialog-footer" >
                    <el-button @click="state.isShowSearch = false">取消</el-button>
                    <el-button type="primary" @click="setPermissiom" :loading="loading">{{ btnName }}</el-button>
                </div>
            </template>
        </el-dialog>

    </div>
</template>
<script setup lang="ts">
import { reactive, ref } from 'vue';
import { storeToRefs } from 'pinia';
import { useUserInfo } from '/@/stores/userInfo';
import { userPermissiom } from '/@/stores/userPermissiom';
import { login } from '/@/views/system/loginTwo/api'
import { Local } from '/@/utils/storage';
const stores = useUserInfo();
const { userInfos } = storeToRefs(stores);
const storeUserPermissiom = userPermissiom();
const { u_Permission } = storeToRefs(storeUserPermissiom);
const inputPassword = ref("")
const btnName = ref("认证");
const title = ref("切换到管理权限");
const loading = ref<boolean>(false);
const errloading = ref<boolean>(false);
const state = reactive({
    isShowSearch: false,//是否显示弹窗
    isInput: true, //是否有显示输入框
    title: '',
});
const username = Local.get('username');
// 搜索弹窗打开
const openPermissions = () => {
    //初始话
    errloading.value = false;
    loading.value = false;
    state.isShowSearch = true;
    if (u_Permission.value == 'other') {
        inputPassword.value = '';
        state.isInput = true;
        title.value = "切换到管理权限";
        btnName.value = "认证";
    } else {
        state.isInput = false;
        title.value = "切换到限制权限";
        btnName.value = "限制访问";
    }
};
const setPermissiom = () => {
    if (u_Permission.value == 'other') {
        loading.value = true;
        login({
            'username': userInfos.value.username,
            'password': inputPassword.value
        }).then((res: any) => {
            if (res.code == 200) {
                //登录成功
                state.isShowSearch = false;
                userPermissiom().setUserPermissionStore(Local.get('username'),'root');
                Local.set("u_Permission", "root");
                loading.value = false;
            } else {
                errloading.value = true;
                loading.value = false;
            }
        }, (error: any) => {
            //为空时
            errloading.value = true;
            loading.value = false;
        });
    } else {
        //限制访问
        userPermissiom().setUserPermissionStore(Local.get('username'),'other');
        Local.set("u_Permission", "other");
        loading.value = false;
        state.isShowSearch = false;
    }
}
// 暴露变量
defineExpose({
    openPermissions,
});
</script>
<style scoped lang="scss">
.title {
    font-size: 16px;
    // font-weight: bolder;
    margin-right: 20px;
}
</style>
<style lang="css">
.layout-permissions-z {
    top: 20%;
}
</style>