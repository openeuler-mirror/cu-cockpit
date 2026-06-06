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
</script>
<style scoped lang="scss">
</style>
