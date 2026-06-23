<template>

	<div class="error layout-view-bg-white" :style="{ height: `calc(100vh - ${initTagViewHeight}` }">
		<div class="error-flex">
			<div class="left">
				<div class="left-item">
					<div class="left-item-animation left-item-num">404</div>
					<div class="left-item-animation left-item-title">{{ $t('message.notFound.foundTitle') }}</div>
					<div class="left-item-animation left-item-msg">{{ $t('message.notFound.foundMsg') }}</div>
					<div class="left-item-animation left-item-btn">
						<el-button type="primary" round @click="onGoHome">{{ $t('message.notFound.foundBtn') }}</el-button>
					</div>
				</div>
			</div>
			<div class="right">
				<img
					src="./img404.png"
				/>
			</div>
		</div>
	</div>
</template>
<script lang="ts">
</script>
<style scoped lang="scss">
</style>
