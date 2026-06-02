<template>

	<div class="layout-logo" v-if="setShowLogo" @click="onThemeConfigChange">
		<img :src="siteLogo" class="layout-logo-medium-img" />
		<span>{{ getSystemConfig['login.site_title'] || themeConfig.globalTitle }}</span>
	</div>
	<div class="layout-logo-size" v-else @click="onThemeConfigChange">
		<img :src="siteLogo" class="layout-logo-size-img" />
	</div>
</template>
<script setup lang="ts" name="layoutLogo">

import { computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useThemeConfig } from '/@/stores/themeConfig';
import logoMini from '/@/assets/logo-mini.png';
import { SystemConfigStore } from "/@/stores/systemConfig";
import _ from "lodash-es";
// 定义变量内容
const storesThemeConfig = useThemeConfig();
const { themeConfig } = storeToRefs(storesThemeConfig);

// 设置 logo 的显示。classic 经典布局默认显示 logo
const setShowLogo = computed(() => {
	let { isCollapse, layout } = themeConfig.value;
	return !isCollapse || layout === 'classic' || document.body.clientWidth < 1000;
});
// logo 点击实现菜单展开/收起
const onThemeConfigChange = () => {
	if (themeConfig.value.layout === 'transverse') return false;
	themeConfig.value.isCollapse = !themeConfig.value.isCollapse;
};

const systemConfigStore = SystemConfigStore()
const { systemConfig } = storeToRefs(systemConfigStore)
const getSystemConfig = computed(() => {
	return systemConfig.value
})

const siteLogo = computed(() => {
	if (!_.isEmpty(getSystemConfig.value['login.site_logo'])) {
		return getSystemConfig.value['login.site_logo']
	}
	return logoMini
});

</script>
<style scoped lang="scss">
</style>
