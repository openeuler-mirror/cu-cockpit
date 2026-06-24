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

.login-container {
    height: 100%;
    background-image: url('/src/assets/login-back.jpg');
    background-repeat: no-repeat;
    background-size: cover;
    background-attachment: scroll;
    background-position: center;

    .login-left,
    .login-right {
        flex: 1;
        position: relative;
    }
}


.login-cnt {
    width: 460px;
    background-color: #fff;
    border-radius: 14px;
    overflow: hidden;
    padding: 12px 0 0;
    margin: auto;
    position: absolute;
    top: calc(50% - 240px);
    left: calc(75% - 230px);

    .login-title {
        align-items: center;
        justify-content: center;
        text-align: center;
        font-weight: 600;
        font-size: 24px;
        color: #333333;
        line-height: 1.5;
        margin-top: 28px;

        .logo-img {
            width: 46px;
        }

        .title-text {
            margin-left: 14px;
            font-weight: 600;
        }
    }

    .form-div {
        margin: auto;
        margin-top: 40px;
        max-width: 360px;
    }
}

.login-content-submit {
    width: 100%;
    letter-spacing: 2px;
    font-weight: 800;
    margin-top: 15px;
}

.el-form-zinput {
    margin-bottom: 26px;
}

.form-input {
    ::v-deep .el-input__wrapper {
        background-color: #fcf9f9;
        border-radius: 8px;
    }
}

.login-foot {
    border-top: 1px solid #f7f7f7;
    margin: auto;
    background: #ededed;
    padding: 20px 0;

    .login-foot-text {
        max-width: 360px;
        font-size: 18px;
        color: #333333;
        line-height: 1.5;
        margin: auto;
    }
}
</style>