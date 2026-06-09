<template>

	<div class="upgrade-dialog">
		<el-dialog
			v-model="state.isUpgrade"
			width="300px"
			destroy-on-close
			:show-close="false"
			:close-on-click-modal="false"
			:close-on-press-escape="false"
		>
			<div class="upgrade-title">
				<div class="upgrade-title-warp">
					<span class="upgrade-title-warp-txt">{{ $t('message.upgrade.title') }}</span>
					<span class="upgrade-title-warp-version">v{{ state.version }}</span>
				</div>
			</div>
			<div class="upgrade-content">
				{{ getThemeConfig.globalTitle }} {{ $t('message.upgrade.msg') }}
				<div class="mt5">
					 
				</div>
				<div class="upgrade-content-desc mt5">{{ $t('message.upgrade.desc') }}</div>
			</div>
			<div class="upgrade-btn">
				<el-button round size="default" type="info" text  @click="onCancel" >{{ $t('message.upgrade.btnOne') }}</el-button>
				<el-button type="primary" round size="default" @click="onUpgrade"  :loading="state.isLoading" >{{ state.btnTxt }}</el-button>
			</div>
		</el-dialog>
	</div>
</template>
<script setup lang="ts" name="layoutUpgrade">

import { reactive, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { storeToRefs } from 'pinia';
import { useThemeConfig } from '/@/stores/themeConfig';
import { Local,Session } from '/@/utils/storage';

// 定义变量内容
const { t } = useI18n();
const storesThemeConfig = useThemeConfig();
const { themeConfig } = storeToRefs(storesThemeConfig);
const state = reactive({
	isUpgrade: false,
	// @ts-ignore
	version: __VERSION__,
	isLoading: false,
	btnTxt: '',
});

// 获取布局配置信息
const getThemeConfig = computed(() => {
	return themeConfig.value;
});
// 残忍拒绝
const onCancel = () => {
	state.isUpgrade = false;
  Session.set('isUpgrade', false)
};
// 马上更新
const onUpgrade = () => {
	state.isLoading = true;
	state.btnTxt = t('message.upgrade.btnTwoLoading');
	setTimeout(() => {
		Local.clear();
		window.location.reload();
		Local.set('version', state.version);
    Session.set('isUpgrade', false)
	}, 2000);
};
// 延迟显示，防止刷新时界面显示太快
const delayShow = () => {
  const isUpgrade = Session.get('isUpgrade')===false?Session.get('isUpgrade'):true
  if(isUpgrade){
    setTimeout(() => {
      state.isUpgrade = true;
    }, 2000);
  }
};
// 页面加载时
onMounted(() => {
	delayShow();
	setTimeout(() => {
		state.btnTxt = t('message.upgrade.btnTwo');
	}, 200);
});
</script>
<style scoped lang="scss">
</style>
