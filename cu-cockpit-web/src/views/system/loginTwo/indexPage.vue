<template #suffix>

                                <i class="iconfont el-input__icon login-content-password"
                                    :class="isShowPassword ? 'icon-yincangmima' : 'icon-xianshimima'"
                                    @click="isShowPassword = !isShowPassword">
                                </i>
                            
</template>
<script setup lang="ts">

import { onMounted, reactive, ref, toRefs } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { NextLoading } from '/@/utils/loading';
import logoMini from '/@/assets/logo-mini.png';
import { Action, ElMessageBox, FormRules } from 'element-plus';
import { login } from '/@/views/system/loginTwo/api'
import Cookies from 'js-cookie';
import { Session, Local } from '/@/utils/storage';
import { initFrontEndControlRoutes } from '/@/router/frontEnd';
import { useUserInfo } from '/@/stores/userInfo';
import { userPermissiom } from '/@/stores/userPermissiom';
const route = useRoute();
const router = useRouter();
const formRef = ref();
const state = reactive({
    isShowPassword: false,
    ruleForm: {
        username: '',
        password: '',
    },
    loading: {
        signIn: false,
    },
});

const { ruleForm, isShowPassword, loading } = toRefs(state);
const rules = reactive<FormRules>({
    username: [
        { required: true, message: '请填写账号', trigger: 'blur' },
    ],
    password: [
        {
            required: true,
            message: '请填写密码',
            trigger: 'blur',
        },
    ],
})
const loginClick = async () => {
    if (!formRef.value) return;
    await formRef.value.validate((valid: string|boolean) => {
        if (valid) {
            loading.value.signIn = true;
            login({
                ...state.ruleForm,
                'username': state.ruleForm.username.trim(),
            }).then(res => {
                if (res.code == 200) {
                    // 登录成功
                    Cookies.set('user', res.user);
                    Session.set('token', res.user);
                    Local.set("username", res.user);
                    useUserInfo().setUserName(res.user);
                    userPermissiom().getUserPermissionStore(res.user);
                    initFrontEndControlRoutes();
                    if (route.query?.redirect) {
                        router.push({
                            path: <string>route.query?.redirect,
                            query: Object.keys(<string>route.query?.params).length > 0 ? JSON.parse(<string>route.query?.params) : '',
                        });
                    } else {
                        router.push('/');
                    }
                } else {
                   loading.value.signIn = false;
                }

            }, error => {
                let message =error.message;
                ElMessageBox.alert(message, '提示', {
                    confirmButtonText: 'OK',
                    callback: (action: Action) => {
                        console.log(action);
                    },
                });
                loading.value.signIn = false;
            })
        }

    });
}
// 页面加载时
onMounted(() => {
    NextLoading.done();
});
</script>
<style scoped lang="scss">
</style>