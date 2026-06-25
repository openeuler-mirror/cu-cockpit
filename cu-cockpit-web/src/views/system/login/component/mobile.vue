<template #prefix>

						<el-icon class="el-input__icon"><ele-Position /></el-icon>
					
</template>
<script lang="ts">

import { toRefs, reactive, defineComponent } from 'vue';

// 定义接口来定义对象的类型
interface LoginMobileState {
	username: any;
	code: string | number | undefined;
}

// 定义对象与类型
const ruleForm: LoginMobileState = {
	username: '',
	code: '',
};

export default defineComponent({
	name: 'loginMobile',
	setup() {
		const state = reactive({ ruleForm });
		return {
			...toRefs(state),
		};
	},
});
</script>
<style scoped lang="scss">

.login-content-form {
	margin-top: 20px;
	@for $i from 1 through 4 {
		.login-animation#{$i} {
			opacity: 0;
			animation-name: error-num;
			animation-duration: 0.5s;
			animation-fill-mode: forwards;
			animation-delay: calc($i/10) + s;
		}
	}
	.login-content-code {
		width: 100%;
		padding: 0;
	}
	.login-content-submit {
		width: 100%;
		letter-spacing: 2px;
		font-weight: 300;
		margin-top: 15px;
	}
	.login-msg {
		color: var(--el-text-color-placeholder);
	}
}
</style>
