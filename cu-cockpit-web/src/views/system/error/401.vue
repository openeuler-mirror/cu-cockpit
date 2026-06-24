<template>

	<div class="error layout-view-bg-white" :style="{ height: `calc(100vh - ${initTagViewHeight}` }">
		<div class="error-flex">
			<div class="left">
				<div class="left-item">
					<div class="left-item-animation left-item-num">401</div>
					<div class="left-item-animation left-item-title">{{ $t('message.noAccess.accessTitle') }}</div>
					<div class="left-item-animation left-item-msg">{{ $t('message.noAccess.accessMsg') }}</div>
					<div class="left-item-animation left-item-btn">
						<el-button type="primary" round @click="onSetAuth">{{ $t('message.noAccess.accessBtn') }}</el-button>
					</div>
				</div>
			</div>
			<div class="right">
			</div>
		</div>
	</div>
</template>
<script lang="ts">

import { defineComponent, computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useThemeConfig } from '/@/stores/themeConfig';
import { useTagsViewRoutes } from '/@/stores/tagsViewRoutes';
import { Session } from '/@/utils/storage';

export default defineComponent({
	name: '401',
	setup() {
		const storesThemeConfig = useThemeConfig();
		const storesTagsViewRoutes = useTagsViewRoutes();
		const { themeConfig } = storeToRefs(storesThemeConfig);
		const { isTagsViewCurrenFull } = storeToRefs(storesTagsViewRoutes);
		const onSetAuth = () => {
			// 清除缓存/token等
			Session.clear();
			// 使用 reload 时，不需要调用 resetRoute() 重置路由
			window.location.reload();
		};
		// 设置主内容的高度
		const initTagViewHeight = computed(() => {
			let { isTagsview } = themeConfig.value;
			if (isTagsViewCurrenFull.value) {
				return `30px`;
			} else {
				if (isTagsview) return `114px`;
				else return `80px`;
			}
		});
		return {
			onSetAuth,
			initTagViewHeight,
		};
	},
});
</script>
<style scoped lang="scss">
</style>
