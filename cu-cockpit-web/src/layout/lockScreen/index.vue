<template>

</template>
<script setup lang="ts" name="layoutLockScreen">

import { nextTick, onMounted, reactive, ref, onUnmounted } from 'vue';
import { formatDate } from '/@/utils/formatTime';
import { Local } from '/@/utils/storage';
import { storeToRefs } from 'pinia';
import { useThemeConfig } from '/@/stores/themeConfig';

// 定义变量内容
const layoutLockScreenDateRef = ref<HtmlType>();
const layoutLockScreenInputRef = ref();
const storesThemeConfig = useThemeConfig();
const { themeConfig } = storeToRefs(storesThemeConfig);
const state = reactive({
	transparency: 1,
	downClientY: 0,
	moveDifference: 0,
	isShowLoockLogin: false,
	isFlags: false,
	querySelectorEl: '' as HtmlType,
	time: {
		hm: '',
		s: '',
		mdq: '',
	},
	setIntervalTime: 0,
	isShowLockScreen: false,
	isShowLockScreenIntervalTime: 0,
	lockScreenPassword: '',
});

// 鼠标按下 pc
const onDownPc = (down: MouseEvent) => {
	state.isFlags = true;
	state.downClientY = down.clientY;
};
// 鼠标按下 app
const onDownApp = (down: TouchEvent) => {
	state.isFlags = true;
	state.downClientY = down.touches[0].clientY;
};
// 鼠标移动 pc
const onMovePc = (move: MouseEvent) => {
	state.moveDifference = move.clientY - state.downClientY;
	onMove();
};
// 鼠标移动 app
const onMoveApp = (move: TouchEvent) => {
	state.moveDifference = move.touches[0].clientY - state.downClientY;
	onMove();
};
// 鼠标移动事件
const onMove = () => {
	if (state.isFlags) {
		const el = <HTMLElement>state.querySelectorEl;
		const opacitys = (state.transparency -= 1 / 200);
		if (state.moveDifference >= 0) return false;
		el.setAttribute('style', `top:${state.moveDifference}px;cursor:pointer;opacity:${opacitys};`);
		if (state.moveDifference < -400) {
			el.setAttribute('style', `top:${-el.clientHeight}px;cursor:pointer;transition:all 0.3s ease;`);
			state.moveDifference = -el.clientHeight;
			setTimeout(() => {
				el && el.parentNode?.removeChild(el);
			}, 300);
		}
		if (state.moveDifference === -el.clientHeight) {
			state.isShowLoockLogin = true;
			layoutLockScreenInputRef.value.focus();
		}
	}
};
// 鼠标松开
const onEnd = () => {
	state.isFlags = false;
	state.transparency = 1;
	if (state.moveDifference >= -400) {
		(<HTMLElement>state.querySelectorEl).setAttribute('style', `top:0px;opacity:1;transition:all 0.3s ease;`);
	}
};
// 获取要拖拽的初始元素
const initGetElement = () => {
	nextTick(() => {
		state.querySelectorEl = layoutLockScreenDateRef.value;
	});
};
// 时间初始化
const initTime = () => {
	state.time.hm = formatDate(new Date(), 'HH:MM');
	state.time.s = formatDate(new Date(), 'SS');
	state.time.mdq = formatDate(new Date(), 'mm月dd日，WWW');
};
// 时间初始化定时器
const initSetTime = () => {
	initTime();
	state.setIntervalTime = window.setInterval(() => {
		initTime();
	}, 1000);
};
// 锁屏时间定时器
const initLockScreen = () => {
	if (themeConfig.value.isLockScreen) {
		state.isShowLockScreenIntervalTime = window.setInterval(() => {
			if (themeConfig.value.lockScreenTime <= 1) {
				state.isShowLockScreen = true;
				setLocalThemeConfig();
				return false;
			}
			themeConfig.value.lockScreenTime--;
		}, 1000);
	} else {
		clearInterval(state.isShowLockScreenIntervalTime);
	}
};
// 存储布局配置
const setLocalThemeConfig = () => {
	themeConfig.value.isDrawer = false;
	Local.set('themeConfig', themeConfig.value);
};
// 密码输入点击事件
const onLockScreenSubmit = () => {
	themeConfig.value.isLockScreen = false;
	themeConfig.value.lockScreenTime = 30;
	setLocalThemeConfig();
};
// 页面加载时
onMounted(() => {
	initGetElement();
	initSetTime();
	initLockScreen();
});
// 页面卸载时
onUnmounted(() => {
	window.clearInterval(state.setIntervalTime);
	window.clearInterval(state.isShowLockScreenIntervalTime);
});
</script>
<style scoped lang="scss">
</style>
