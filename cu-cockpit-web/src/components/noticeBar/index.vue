<template>

	<div class="notice-bar" :style="{ background, height: `${height}px` }" v-show="!state.isMode">
		<div class="notice-bar-warp" :style="{ color, fontSize: `${size}px` }">
			<i v-if="leftIcon" class="notice-bar-warp-left-icon" :class="leftIcon"></i>
			<div class="notice-bar-warp-text-box" ref="noticeBarWarpRef">
				<div class="notice-bar-warp-text" ref="noticeBarTextRef" v-if="!scrollable">{{ text }}</div>
				<div class="notice-bar-warp-slot" v-else><slot /></div>
			</div>
			<SvgIcon :name="rightIcon" v-if="rightIcon" class="notice-bar-warp-right-icon" @click="onRightIconClick" />
		</div>
	</div>
</template>
<script setup lang="ts" name="noticeBar">
import { reactive, ref, onMounted, nextTick } from 'vue';
</script>
<style scoped lang="scss">
</style>
