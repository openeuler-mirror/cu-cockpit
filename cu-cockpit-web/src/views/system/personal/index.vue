<template #footer>

				<span class="dialog-footer">
					<el-button type="primary" @click="settingPassword"> <i class="fa fa-check"></i>提交 </el-button>
				</span>
			
</template>
<script setup lang="ts" name="personal">

import { reactive, computed, onMounted, ref, defineAsyncComponent } from 'vue';
import { formatAxis } from '/@/utils/formatTime';
import * as api from './api';
import { ElMessage } from 'element-plus';
import { getBaseURL } from '/@/utils/baseUrl';
import { Session } from '/@/utils/storage';
import { useRouter } from 'vue-router';
import { useUserInfo } from '/@/stores/userInfo';
import { successMessage } from '/@/utils/message';
import { dictionary } from '/@/utils/dictionary';
import { Md5 } from 'ts-md5';
const router = useRouter();

// 头像裁剪组件
const avatarSelector = defineAsyncComponent(() => import('/@/components/avatarSelector/index.vue'));
const avatarSelectorRef = ref(null);
// 当前时间提示语
const currentTime = computed(() => {
	return formatAxis(new Date());
});
const userInfoFormRef = ref();
const rules = reactive({
	name: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
	mobile: [{ pattern: /^1[3-9]\d{9}$/, message: '请输入正确手机号' }],
});

let selectImgVisible = ref(false);

const state = reactive<PersonalState>({
	newsInfoList: [],
	personalForm: {
		avatar: '',
		username: '',
		name: '',
		email: '',
		mobile: '',
		gender: '',
		dept_info: {
			dept_id: 0,
			dept_name: '',
		},
		role_info: [
			{
				id: 0,
				name: '',
			},
		],
	},
});

/**
 * 跳转消息中心
 */
const route = useRouter();
const msgMore = () => {
	route.push({ path: '/messageCenter' });
};

const genderList = ref();
/**
 * 获取用户个人信息
 */
const getUserInfo = function () {
	api.GetUserInfo({}).then((res: any) => {
		const { data } = res;
		genderList.value = dictionary('gender');
		state.personalForm.avatar = data.avatar || '';
		state.personalForm.username = data.username || '';
		state.personalForm.name = data.name || '';
		state.personalForm.email = data.email || '';
		state.personalForm.mobile = data.mobile || '';
		state.personalForm.gender = data.gender;
		state.personalForm.dept_info.dept_name = data.dept_info.dept_name || '';
		state.personalForm.role_info = data.role_info || [];
	});
};

/**
 * 更新用户信息
 * @param formEl
 */
const submitForm = async () => {
	if (!userInfoFormRef.value) return;
	await userInfoFormRef.value.validate((valid, fields) => {
		if (valid) {
			api.updateUserInfo(state.personalForm).then((res: any) => {
				ElMessage.success('更新成功');
				getUserInfo();
			});
		} else {
			ElMessage.error('表单验证失败,请检查~');
		}
	});
};

/**
 * 获取消息通知
 */
const getMsg = () => {
	api.GetSelfReceive({}).then((res: any) => {
		const { data } = res;
		state.newsInfoList = data || [];
	});
};
onMounted(() => {
	getUserInfo();
	getMsg();
});

/**************************密码修改部分************************/
const passwordFormShow = ref(false);
const userPasswordFormRef = ref();
const userPasswordInfo = reactive({
	oldPassword: '',
	newPassword: '',
	newPassword2: '',
});

const validatePass = (rule, value, callback) => {
	const pwdRegex = new RegExp('(?=.*[0-9])(?=.*[a-zA-Z]).{8,30}');
	if (value === '') {
		callback(new Error('请输入密码'));
	} else if (value === userPasswordInfo.oldPassword) {
		callback(new Error('原密码与新密码一致'));
	} else if (!pwdRegex.test(value)) {
		callback(new Error('您的密码复杂度太低(密码中必须包含字母、数字)'));
	} else {
		if (userPasswordInfo.newPassword2 !== '') {
			userPasswordFormRef.value.validateField('newPassword2');
		}
		callback();
	}
};
const validatePass2 = (rule, value, callback) => {
	if (value === '') {
		callback(new Error('请再次输入密码'));
	} else if (value !== userPasswordInfo.newPassword) {
		callback(new Error('两次输入密码不一致!'));
	} else {
		callback();
	}
};

const passwordRules = reactive({
	oldPassword: [
		{
			required: true,
			message: '请输入原密码',
			trigger: 'blur',
		},
	],
	newPassword: [{ validator: validatePass, trigger: 'blur' }],
	newPassword2: [{ validator: validatePass2, trigger: 'blur' }],
});

/**
 * 重新设置密码
 */
const settingPassword = () => {
	userPasswordFormRef.value.validate((valid) => {
		if (valid) {
			api.UpdatePassword(userPasswordInfo).then((res: any) => {
				ElMessage.success('密码修改成功');
				setTimeout(() => {
					Session.remove('token');
					router.push('/login');
				}, 1000);
			});
		} else {
			// 校验失败
			// 登录表单校验失败
			ElMessage.error('表单校验失败，请检查');
		}
	});
};

const uploadImg = (data: any) => {
	let formdata = new FormData();
	formdata.append('file', data);
	api.uploadAvatar(formdata).then((res: any) => {
		if (res.code === 2000) {
			selectImgVisible.value = false;
			// state.personalForm.avatar = getBaseURL() + res.data.url;
			state.personalForm.avatar = res.data.url;
			api.updateUserInfo(state.personalForm).then((res: any) => {
				successMessage('更新成功');
				getUserInfo();
				useUserInfo().updateUserInfos();
				// @ts-ignore
				avatarSelectorRef.value.updateAvatar(state.personalForm.avatar);
			});
		}
	});
};
</script>
<style scoped lang="scss">

@use '/@/theme/mixins/index.scss' as mixins;
</style>
