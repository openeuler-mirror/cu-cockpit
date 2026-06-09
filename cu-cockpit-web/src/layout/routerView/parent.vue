<template>

	<div class="layout-parent">
		<router-view v-slot="{ Component }">
			<transition :name="setTransitionName" mode="out-in">
				<keep-alive :include="getKeepAliveNames" v-if="showView">
						<component :is="Component" :key="state.refreshRouterViewKey" class="w100" v-show="!isIframePage" />
				</keep-alive>
			</transition>
		</router-view>
		<transition :name="setTransitionName" mode="out-in">
			<Iframes class="w100" v-show="isIframePage" :refreshKey="state.iframeRefreshKey" :name="setTransitionName"
				:list="state.iframeList" />
		</transition>
	</div>
</template>
<script setup lang="ts" name="layoutParentView">

import { defineAsyncComponent, computed, reactive, onBeforeMount, onUnmounted, nextTick, watch, onMounted, ref, provide } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { storeToRefs } from 'pinia';
import { useKeepALiveNames } from '/@/stores/keepAliveNames';
import { useThemeConfig } from '/@/stores/themeConfig';
import { Session } from '/@/utils/storage';
import mittBus from '/@/utils/mitt';

// 引入组件
const Iframes = defineAsyncComponent(() => import('/@/layout/routerView/iframes.vue'));

// 定义变量内容
const route = useRoute();
const router = useRouter();
const storesKeepAliveNames = useKeepALiveNames();
const storesThemeConfig = useThemeConfig();
const { keepAliveNames, cachedViews } = storeToRefs(storesKeepAliveNames);
const { themeConfig } = storeToRefs(storesThemeConfig);
const state = reactive<ParentViewState>({
	refreshRouterViewKey: '', // 非 iframe tagsview 右键菜单刷新时
	iframeRefreshKey: '', // iframe tagsview 右键菜单刷新时
	keepAliveNameList: [],
	iframeList: [],
});

//全局依赖刷新页面
const showView = ref(true)
/**
 * 刷新页面
 */
const refreshView = function () {
	showView.value = false // 通过v-if移除router-view节点
	nextTick(() => {
		showView.value = true // DOM更新后再通过v-if添加router-view节点
	})
}
provide('refreshView', refreshView)

// 设置主界面切换动画
const setTransitionName = computed(() => {
	return themeConfig.value.animation;
});
// 获取组件缓存列表(name值)
const getKeepAliveNames = computed(() => {
  console.log(cachedViews.value)
	return themeConfig.value.isTagsview ? cachedViews.value : state.keepAliveNameList;
});
// 设置 iframe 显示/隐藏
</script>
