<template>

	<el-main class="layout-main"
		:style="isFixedHeader ? `height: calc(100% - ${setMainHeight})` : `minHeight: calc(100% - ${setMainHeight})`">
		<el-scrollbar ref="layoutMainScrollbarRef" class="layout-main-scroll layout-backtop-header-fixed"
			wrap-class="layout-main-scroll" view-class="layout-main-scroll">
			<LayoutParentView />
      <LayoutFooter v-if="isFooter" />
		</el-scrollbar>
		<el-backtop :target="setBacktopClass" />
	</el-main>
</template>
<script setup lang="ts" name="layoutMain">
import { defineAsyncComponent, onMounted, computed, ref } from 'vue';
import { useRoute } from 'vue-router';
import { storeToRefs } from 'pinia';
import { useTagsViewRoutes } from '/@/stores/tagsViewRoutes';
import { useThemeConfig } from '/@/stores/themeConfig';
import { NextLoading } from '/@/utils/loading';
</script>
