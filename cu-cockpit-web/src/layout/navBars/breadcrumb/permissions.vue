<template>
    <div class="layout-permissions-dialog">
        <el-dialog
            v-model="state.isShowSearch"
            align-center
            class="layout-permissions-z"
            modal-class="layout-permissions-overlay"
            width="520px"
            :close-on-click-modal="false"
            @closed="resetDialog"
        >
            <template #header="{ titleId, titleClass }">
                <div class="permission-dialog__header">
                    <span class="permission-dialog__mark" :class="{ 'is-restricted': !state.isInput }">
                        <el-icon><Unlock v-if="state.isInput" /><Lock v-else /></el-icon>
                    </span>
                    <div>
                        <h2 :id="titleId" :class="[titleClass, 'permission-dialog__title']">{{ title }}</h2>
                        <div class="permission-dialog__meta">
                            {{ state.isInput ? '当前会话 · 权限提升认证' : '当前会话 · 访问级别调整' }}
                        </div>
                    </div>
                </div>
            </template>

            <div v-if="state.isInput" class="permission-dialog__auth">
                <el-alert
                    v-if="errloading"
                    class="permission-dialog__alert"
                    title="密码错误，请重新输入"
                    type="error"
                    show-icon
                    :closable="false"
                />
                <div class="permission-dialog__account">
                    <span class="permission-dialog__account-icon"><el-icon><User /></el-icon></span>
                    <div>
                        <small>当前账号</small>
                        <strong>{{ userInfos.username }}</strong>
                    </div>
                </div>
                <label class="permission-dialog__label" for="permission-password">账号密码</label>
                <el-input
                    id="permission-password"
                    v-model="inputPassword"
                    class="permission-dialog__input"
                    type="password"
                    show-password
                    :prefix-icon="Key"
                    placeholder="请输入当前账号密码"
                    autocomplete="current-password"
                    size="large"
                    @input="errloading = false"
                    @keyup.enter="setPermissiom"
                />
                <div class="permission-dialog__hint">
                    <el-icon><Lock /></el-icon>
                    <span>密码仅用于本次权限认证</span>
                </div>
            </div>
            <div v-else class="permission-dialog__restriction">
                <span class="permission-dialog__restriction-icon"><el-icon><WarningFilled /></el-icon></span>
                <div>
                    <strong>启用限制访问模式</strong>
                    <p>管理员操作将被限制，浏览器会记住当前访问级别。</p>
                </div>
            </div>
            <template v-if="username != 'root'" #footer>
                <div class="permission-dialog__footer">
                    <el-button class="permission-dialog__cancel" size="large" @click="state.isShowSearch = false">取消</el-button>
                    <el-button
                        class="permission-dialog__confirm"
                        :type="state.isInput ? 'primary' : 'warning'"
                        :icon="state.isInput ? Unlock : Lock"
                        size="large"
                        :loading="loading"
                        :disabled="state.isInput && !inputPassword"
                        @click="setPermissiom"
                    >
                        {{ btnName }}
                    </el-button>
                </div>
            </template>
        </el-dialog>
    </div>
</template>
<script setup lang="ts">
import { reactive, ref } from 'vue';
import { Key, Lock, Unlock, User, WarningFilled } from '@element-plus/icons-vue';
import { storeToRefs } from 'pinia';
import { useUserInfo } from '/@/stores/userInfo';
import { userPermissiom } from '/@/stores/userPermissiom';
import { login } from '/@/views/system/loginTwo/api'
import { Local } from '/@/utils/storage';
interface LoginResponse {
    code?: number;
}
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
const resetDialog = () => {
    inputPassword.value = '';
    errloading.value = false;
    loading.value = false;
};
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
        if (!inputPassword.value || loading.value) return;
        loading.value = true;
        login({
            'username': userInfos.value.username,
            'password': inputPassword.value
        }).then((res: LoginResponse) => {
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
        }, () => {
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
<style lang="scss">
.layout-permissions-overlay.el-overlay {
    background: rgba(2, 8, 18, 0.74);
    backdrop-filter: blur(6px);

    .el-overlay-dialog {
        padding: 16px;
    }
}

.layout-permissions-z.el-dialog {
    position: relative;
    top: auto;
    max-width: calc(100vw - 32px);
    margin: 0;
    padding: 0;
    border: 1px solid rgba(34, 211, 238, 0.34);
    border-radius: 8px;
    background:
        linear-gradient(145deg, rgba(34, 211, 238, 0.055), transparent 42%),
        #0c172a;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.04),
        0 24px 64px rgba(0, 0, 0, 0.56),
        0 0 28px rgba(34, 211, 238, 0.12);
    overflow: hidden;

    &::before {
        content: '';
        position: absolute;
        inset: 0 18px auto;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--tech-cyan), transparent);
        opacity: 0.85;
    }

    .el-dialog__header {
        min-height: 76px;
        margin: 0;
        padding: 18px 56px 18px 22px;
        border-bottom: 1px solid rgba(90, 165, 255, 0.13);
        background: rgba(14, 27, 47, 0.66);
        box-sizing: border-box;
    }

    .el-dialog__headerbtn {
        top: 20px;
        right: 18px;
        width: 34px;
        height: 34px;
        border: 1px solid transparent;
        border-radius: 6px;

        .el-dialog__close {
            color: #8093ae;
            font-size: 18px;
        }

        &:hover {
            border-color: rgba(255, 77, 109, 0.34);
            background: rgba(255, 77, 109, 0.08);

            .el-dialog__close {
                color: #ff8da2;
            }
        }
    }

    .el-dialog__body {
        padding: 22px 24px 20px;
        color: #c7d2e5;
    }

    .el-dialog__footer {
        padding: 16px 24px 20px;
        border-top: 1px solid rgba(90, 165, 255, 0.11);
        background: rgba(7, 15, 29, 0.5);
    }

    .permission-dialog__header {
        display: flex;
        align-items: center;
        gap: 13px;
    }

    .permission-dialog__mark {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        flex: none;
        border: 1px solid rgba(34, 211, 238, 0.4);
        border-radius: 7px;
        color: var(--tech-cyan);
        background: rgba(34, 211, 238, 0.09);
        box-shadow: inset 0 0 14px rgba(34, 211, 238, 0.07), 0 0 16px rgba(34, 211, 238, 0.12);

        &.is-restricted {
            border-color: rgba(255, 176, 32, 0.42);
            color: var(--tech-amber);
            background: rgba(255, 176, 32, 0.09);
            box-shadow: inset 0 0 14px rgba(255, 176, 32, 0.06), 0 0 16px rgba(255, 176, 32, 0.1);
        }

        .el-icon {
            font-size: 20px;
        }
    }

    .permission-dialog__title.el-dialog__title {
        margin: 0;
        color: #eff8ff;
        font-size: 17px;
        font-weight: 800;
        line-height: 1.3;
        text-shadow: 0 0 14px rgba(34, 211, 238, 0.18);
    }

    .permission-dialog__meta {
        margin-top: 4px;
        color: #7488a5;
        font-size: 10px;
        font-weight: 700;
    }

    .permission-dialog__alert {
        margin-bottom: 16px;
        border: 1px solid rgba(255, 77, 109, 0.3);
        border-radius: 6px;
        background: rgba(255, 77, 109, 0.075);

        .el-alert__title,
        .el-alert__icon {
            color: #ff9aae;
        }
    }

    .permission-dialog__account {
        display: flex;
        align-items: center;
        gap: 11px;
        margin-bottom: 18px;
        padding-bottom: 16px;
        border-bottom: 1px dashed rgba(90, 165, 255, 0.16);

        > div {
            display: grid;
            gap: 3px;
        }

        small {
            color: #7488a5;
            font-size: 10px;
            font-weight: 700;
        }

        strong {
            color: #e7f5ff;
            font-size: 14px;
            font-weight: 800;
        }
    }

    .permission-dialog__account-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 34px;
        flex: none;
        border: 1px solid rgba(168, 85, 247, 0.32);
        border-radius: 6px;
        color: #c69aff;
        background: rgba(168, 85, 247, 0.08);
    }

    .permission-dialog__label {
        display: block;
        margin-bottom: 8px;
        color: #9eb0cc;
        font-size: 11px;
        font-weight: 700;
    }

    .permission-dialog__input .el-input__wrapper {
        min-height: 46px;
        padding: 0 13px;
        border-radius: 6px;
        background:
            linear-gradient(135deg, rgba(34, 211, 238, 0.05), transparent),
            rgba(7, 15, 29, 0.92);
        box-shadow:
            inset 0 0 0 1px rgba(34, 211, 238, 0.24),
            inset 0 1px 0 rgba(255, 255, 255, 0.025);

        &:hover {
            box-shadow: inset 0 0 0 1px rgba(34, 211, 238, 0.46), 0 0 14px rgba(34, 211, 238, 0.08);
        }

        &.is-focus {
            box-shadow: inset 0 0 0 1px rgba(34, 211, 238, 0.76), 0 0 18px rgba(34, 211, 238, 0.15);
        }
    }

    .permission-dialog__input .el-input__inner {
        color: #f2f8ff;
        font-size: 14px;
        font-weight: 700;
        -webkit-text-fill-color: #f2f8ff;

        &::placeholder {
            color: #7186a3;
            font-weight: 500;
            opacity: 1;
            -webkit-text-fill-color: #7186a3;
        }
    }

    .permission-dialog__input .el-input__prefix,
    .permission-dialog__input .el-input__suffix {
        color: #78dce8;
        font-size: 17px;
    }

    .permission-dialog__hint {
        display: flex;
        align-items: center;
        gap: 7px;
        margin-top: 10px;
        color: #6f829e;
        font-size: 10px;
        font-weight: 600;

        .el-icon {
            color: #7a91af;
        }
    }

    .permission-dialog__restriction {
        display: flex;
        align-items: flex-start;
        gap: 13px;
        padding: 4px 0;

        strong {
            color: #f4e4ba;
            font-size: 14px;
            font-weight: 800;
        }

        p {
            margin: 6px 0 0;
            color: #8fa2c2;
            font-size: 12px;
            line-height: 1.65;
        }
    }

    .permission-dialog__restriction-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 38px;
        height: 38px;
        flex: none;
        border: 1px solid rgba(255, 176, 32, 0.34);
        border-radius: 7px;
        color: var(--tech-amber);
        background: rgba(255, 176, 32, 0.08);
    }

    .permission-dialog__footer {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 10px;

        .el-button {
            min-width: 92px;
            min-height: 38px;
            margin: 0;
            border-radius: 6px;
            font-weight: 700;
        }
    }

    .permission-dialog__cancel.el-button {
        border-color: rgba(90, 165, 255, 0.24);
        color: #aebfd5;
        background: rgba(13, 27, 48, 0.72);

        &:hover,
        &:focus-visible {
            border-color: rgba(34, 211, 238, 0.48);
            color: #e9fbff;
            background: rgba(34, 211, 238, 0.08);
        }
    }

    .permission-dialog__confirm.el-button--primary {
        border-color: rgba(34, 211, 238, 0.66);
        color: #f2fdff;
        background: linear-gradient(135deg, #0ca5bd, #1677d2);
        box-shadow: 0 0 18px rgba(34, 211, 238, 0.18);

        &:hover,
        &:focus-visible {
            border-color: #7be9f6;
            background: linear-gradient(135deg, #12b9d2, #2589e5);
            box-shadow: 0 0 22px rgba(34, 211, 238, 0.28);
        }

        &.is-disabled {
            border-color: rgba(90, 165, 255, 0.16);
            color: #60738f;
            background: rgba(28, 49, 74, 0.7);
            box-shadow: none;
        }
    }
}

@media (max-width: 560px) {
    .layout-permissions-overlay.el-overlay .el-overlay-dialog {
        padding: 12px;
    }

    .layout-permissions-z.el-dialog {
        max-width: calc(100vw - 24px);

        .el-dialog__header {
            padding: 16px 52px 16px 18px;
        }

        .el-dialog__body {
            padding: 18px;
        }

        .el-dialog__footer {
            padding: 14px 18px 18px;
        }

        .permission-dialog__footer .el-button {
            flex: 1;
        }
    }
}
</style>