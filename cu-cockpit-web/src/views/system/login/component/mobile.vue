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
</style>
