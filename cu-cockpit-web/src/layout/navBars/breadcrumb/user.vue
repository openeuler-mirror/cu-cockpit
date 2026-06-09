<template #dropdown>

				<el-dropdown-menu>
					<!-- <el-dropdown-item command="/home">{{ $t('message.user.dropdown1') }}</el-dropdown-item>
					<el-dropdown-item command="/personal">{{ $t('message.user.dropdown2') }}</el-dropdown-item>
					<el-dropdown-item command="/versionUpgradeLog">更新日志</el-dropdown-item>
					<el-dropdown-item divided command="logOut">{{ $t('message.user.dropdown5') }}</el-dropdown-item> -->
					<el-dropdown-item command="logOut">{{ $t('message.user.dropdown5') }}</el-dropdown-item>
				</el-dropdown-menu>
			
</template>
<script setup lang="ts" name="layoutBreadcrumbUser">

import { defineAsyncComponent, ref, computed, reactive, onMounted, unref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessageBox, ElMessage } from 'element-plus';
import screenfull from 'screenfull';
import { useI18n } from 'vue-i18n';
import { storeToRefs } from 'pinia';
import { useUserInfo } from '/@/stores/userInfo';
import { userPermissiom } from '/@/stores/userPermissiom';
import { useThemeConfig } from '/@/stores/themeConfig';
import other from '/@/utils/other';
import mittBus from '/@/utils/mitt';
import { Session, Local } from '/@/utils/storage';
import headerImage from '/@/assets/img/headerImage.png';
import { InfoFilled } from '@element-plus/icons-vue';
import { signOut } from '/@/api/login/index'
// 引入组件
const UserNews = defineAsyncComponent(() => import('/@/layout/navBars/breadcrumb/userNews.vue'));
const Search = defineAsyncComponent(() => import('/@/layout/navBars/breadcrumb/search.vue'));

// 定义变量内容
const { locale, t } = useI18n();
const router = useRouter();
const stores = useUserInfo();
const storesThemeConfig = useThemeConfig();
const storesUserPermissiom=userPermissiom();
const { userInfos } = storeToRefs(stores);
const { u_Permission } =storeToRefs(storesUserPermissiom);
const { themeConfig } = storeToRefs(storesThemeConfig);
const searchRef = ref();
const state = reactive({
	isScreenfull: false,
	disabledI18n: 'zh-cn',
	disabledSize: 'large',
});
const permissionsRef = ref();
// 设置分割样式
const layoutUserFlexNum = computed(() => {
	let num: string | number = '';
	const { layout, isClassicSplitMenu } = themeConfig.value;
	const layoutArr: string[] = ['defaults', 'columns'];
	if (layoutArr.includes(layout) || (layout === 'classic' && !isClassicSplitMenu)) num = '1';
	else num = '';
	return num;
});

// 全屏点击时
const onScreenfullClick = () => {
	if (!screenfull.isEnabled) {
		ElMessage.warning('暂不不支持全屏');
		return false;
	}
	screenfull.toggle();
	screenfull.on('change', () => {
		if (screenfull.isFullscreen) state.isScreenfull = true;
		else state.isScreenfull = false;
	});
};
// 布局配置 icon 点击时
const onLayoutSetingClick = () => {
	mittBus.emit('openSetingsDrawer');
};
// 下拉菜单点击时
</script>
<style scoped lang="scss">
</style>
