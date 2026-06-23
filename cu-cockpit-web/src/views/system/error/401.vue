<template>

	<div class="error layout-view-bg-white" :style="{ height: `calc(100vh - ${initTagViewHeight}` }">
		<div class="error-flex">
			<div class="left">
				<div class="left-item">
					<div class="left-item-animation left-item-num">401</div>
					<div class="left-item-animation left-item-title">{{ $t('message.noAccess.accessTitle') }}</div>
					<div class="left-item-animation left-item-msg">{{ $t('message.noAccess.accessMsg') }}</div>
					<div class="left-item-animation left-item-btn">
						<el-button type="primary" round @click="onSetAuth">{{ $t('message.noAccess.accessBtn') }}</el-button>
					</div>
				</div>
			</div>
			<div class="right">
			</div>
		</div>
	</div>
</template>
<script lang="ts">
</script>
<style scoped lang="scss">
</style>
