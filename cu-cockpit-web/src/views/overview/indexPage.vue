<template>
  <div class="tech-overview" ref="techRef" :class="{ 'is-fullscreen': isFullscreen }">
    <div class="tech-scanline"></div>

    <!-- 顶部标题 HUD -->
    <div class="tech-topbar">
      <div class="tech-title">
        <span class="tech-title__logo"></span>
        <div>
          <div class="tech-title__main">系统概览</div>
          <div class="tech-title__sub">SYSTEM OVERVIEW · 实时监控</div>
        </div>
      </div>
      <div class="tech-topbar__right">
        <div class="tech-clock">
          <div class="tech-clock__time">{{ nowTime }}</div>
          <div class="tech-clock__date">{{ nowDate }}</div>
        </div>
        <div class="tech-fullscreen-btn" @click="toggleFullscreen">
          <el-icon>
            <Aim v-if="isFullscreen" />
            <FullScreen v-else />
          </el-icon>
          <span>{{ isFullscreen ? '退出' : '大屏' }}</span>
        </div>
      </div>
    </div>

    <!-- 2025-0903 -->
    <el-alert title="Web 控制台正运行于限制访问模式。" type="warning" show-icon :closable="false" style="margin-bottom: 20px" v-if="u_Permission != 'root'"/>
    <overviewHeader />
    <div class="card-container">
      <indicator class="card-item" />
      <system class="card-item" />
    </div>
  </div>
</template>

<script lang="ts" setup name="overviewIndex">
import { onMounted, onUnmounted, ref } from 'vue'
import { FullScreen, Aim } from '@element-plus/icons-vue'
import screenfull from 'screenfull'
import overviewHeader from './components/headerPage.vue'
import system from './components/systemPage.vue'
import indicator from './components/indicatorPage.vue'
import { storeToRefs } from 'pinia'; 
import { userPermissiom } from '/@/stores/userPermissiom'; 
import { useThemeConfig } from '/@/stores/themeConfig';
const storeUserPermissiom = userPermissiom();
const { u_Permission } = storeToRefs(storeUserPermissiom);
const storeThemeConfig = useThemeConfig();
const { themeConfig } = storeToRefs(storeThemeConfig);

// 顶部 HUD 实时时钟
const nowTime = ref('');
const nowDate = ref('');
let clockTimer: number | null = null;
const pad = (n: number) => (n < 10 ? '0' + n : '' + n);
const updateClock = () => {
  const d = new Date();
  nowTime.value = `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  const week = ['日', '一', '二', '三', '四', '五', '六'][d.getDay()];
  nowDate.value = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} 星期${week}`;
};

// 大屏（全屏）看板模式
const techRef = ref<HTMLElement | null>(null);
const isFullscreen = ref(false);
const onFsChange = () => {
  isFullscreen.value = screenfull.isEnabled && screenfull.isFullscreen;
};
const toggleFullscreen = () => {
  if (!screenfull.isEnabled || !techRef.value) return;
  screenfull.toggle(techRef.value);
};

// 概览页主体是科技风，进入时同步外层左侧菜单与顶部标签；离开时尊重用户原主题设置。
const mountOverviewTechShell = () => {
  document.documentElement.classList.add('theme-tech-dark');
};
const restoreOverviewTechShell = () => {
  if (!themeConfig.value.isTechTheme) {
    document.documentElement.classList.remove('theme-tech-dark');
  }
};

onMounted(() => {
  mountOverviewTechShell();
  updateClock();
  clockTimer = window.setInterval(updateClock, 1000);
  if (screenfull.isEnabled) screenfull.on('change', onFsChange);
});
onUnmounted(() => {
  if (clockTimer) window.clearInterval(clockTimer);
  if (screenfull.isEnabled) screenfull.off('change', onFsChange);
  restoreOverviewTechShell();
});
</script>

<!-- 深色霓虹科技风主题：作用域限定在 .tech-overview，不影响其它页面 -->
<style lang="scss">
@import './tech-theme.scss';
</style>

<style scoped lang="scss">
.tech-overview {
  .card-container {
    display: flex;
    justify-content: space-between;
    gap: 20px;
    margin-top: 20px;

    .card-item {
      flex: 1;
      min-width: 0;
    }
  }

  @media (max-width: 1500px) {
    .card-container {
      flex-direction: column;
    }
  }
}
</style>
