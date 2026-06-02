<template>

	<div class="layout-navbars-close-full" v-if="isTagsViewCurrenFull">
		<div class="layout-navbars-close-full-icon">
			<SvgIcon name="ele-Close" :title="$t('message.tagsView.closeFullscreen')" @click="onCloseFullscreen" />
		</div>
	</div>
</template>
<script setup lang="ts" name="layoutCloseFull">

import { storeToRefs } from 'pinia';
import { useTagsViewRoutes } from '/@/stores/tagsViewRoutes';

// 定义变量内容
const stores = useTagsViewRoutes();
const { isTagsViewCurrenFull } = storeToRefs(stores);

// 关闭当前全屏
const onCloseFullscreen = () => {
	stores.setCurrenFullscreen(false);
};
</script>
<style scoped lang="scss">
</style>
