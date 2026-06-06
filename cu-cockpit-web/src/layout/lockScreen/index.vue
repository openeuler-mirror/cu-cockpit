<template>

</template>
<script setup lang="ts" name="layoutLockScreen">
import { nextTick, onMounted, reactive, ref, onUnmounted } from 'vue';
import { formatDate } from '/@/utils/formatTime';
import { Local } from '/@/utils/storage';
import { storeToRefs } from 'pinia';
import { useThemeConfig } from '/@/stores/themeConfig';
</script>
<style scoped lang="scss">
</style>
