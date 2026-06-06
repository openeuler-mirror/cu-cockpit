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
</script>
