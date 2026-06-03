<template>

  <div ref="itemRef" class="file-item" :title="data.name" @mouseenter="isShow = true" @mouseleave="isShow = false">
    <div v-if="showTitle" class="file-name" :class="{ show: isShow }">{{ data.name }}</div>
    <component :is="FileTypes[data.file_type].tag" v-bind="FileTypes[data.file_type].attr" />
    <div v-if="props.showClose" class="file-del" :class="{ show: isShow }">
      <el-icon :size="24" color="white" @click.stop="delFileHandle" style="cursor: pointer;">
        <CircleClose style="mix-blend-mode: difference;" />
      </el-icon>
    </div>
  </div>
</template>
<script setup lang="ts">
import { defineComponent } from 'vue';
import { ref, defineProps, PropType, watch, onMounted, h } from 'vue';
import { successNotification } from '/@/utils/message';
import { getBaseURL } from '/@/utils/baseUrl';
</script>
<style scoped>
</style>