<template>

	<div class="layout-padding layout-link-container">
		<div class="layout-padding-auto layout-padding-view">
			<div class="layout-link-warp">
				<i class="layout-link-icon iconfont icon-xingqiu"></i>
				<div class="layout-link-msg">页面 "{{ $t(state.title) }}" 已在新窗口中打开</div>
				<el-button class="mt30" round size="default" @click="onGotoFullPage">
					<i class="iconfont icon-lianjie"></i>
					<span>立即前往体验</span>
				</el-button>
			</div>
		</div>
	</div>
</template>
<script setup lang="ts" name="layoutLinkView">
import { reactive, watch } from 'vue';
import { useRoute } from 'vue-router';
import { verifyUrl } from '/@/utils/toolsValidate';
import {cookie} from "xe-utils";
</script>
<style scoped lang="scss">
</style>
