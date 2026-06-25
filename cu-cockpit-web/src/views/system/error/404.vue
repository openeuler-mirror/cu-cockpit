<template>

	<div class="error layout-view-bg-white" :style="{ height: `calc(100vh - ${initTagViewHeight}` }">
		<div class="error-flex">
			<div class="left">
				<div class="left-item">
					<div class="left-item-animation left-item-num">404</div>
					<div class="left-item-animation left-item-title">{{ $t('message.notFound.foundTitle') }}</div>
					<div class="left-item-animation left-item-msg">{{ $t('message.notFound.foundMsg') }}</div>
					<div class="left-item-animation left-item-btn">
						<el-button type="primary" round @click="onGoHome">{{ $t('message.notFound.foundBtn') }}</el-button>
					</div>
				</div>
			</div>
			<div class="right">
				<img
					src="./img404.png"
				/>
			</div>
		</div>
	</div>
</template>
<script lang="ts">

import { defineComponent, computed } from 'vue';
import { useRouter } from 'vue-router';
import { storeToRefs } from 'pinia';
import { useThemeConfig } from '/@/stores/themeConfig';
import { useTagsViewRoutes } from '/@/stores/tagsViewRoutes';

export default defineComponent({
	name: '404',
	setup() {
		const storesThemeConfig = useThemeConfig();
		const storesTagsViewRoutes = useTagsViewRoutes();
		const { themeConfig } = storeToRefs(storesThemeConfig);
		const { isTagsViewCurrenFull } = storeToRefs(storesTagsViewRoutes);
		const router = useRouter();
		const onGoHome = () => {
			router.push('/');
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
			onGoHome,
			initTagViewHeight,
		};
	},
});
</script>
<style scoped lang="scss">
</style>
