<template #cell_preview="scope">

        <div v-if="scope.row.file_type === 0">
          <el-image style="width: 100%; aspect-ratio: 1 /1 ;" :src="getBaseURL(scope.row.url)"
            :preview-src-list="[getBaseURL(scope.row.url)]" :preview-teleported="true" />
        </div>
        <div v-if="scope.row.file_type === 1" class="_preview"
          @click="openPreviewHandle(getBaseURL(scope.row.url), 'video')">
          <el-icon :size="60">
            <VideoCamera />
          </el-icon>
        </div>
        <div v-if="scope.row.file_type === 2" class="_preview"
          @click="openPreviewHandle(getBaseURL(scope.row.url), 'video')">
          <el-icon :size="60">
            <Headset />
          </el-icon>
        </div>
        <el-icon v-if="scope.row.file_type === 3" :size="60">
          <Document />
        </el-icon>
        <div v-if="scope.row.file_type > 3">未知类型</div>
      
</template>
<script lang="ts" setup>

import { ref, onMounted, nextTick } from 'vue';
import { useExpose, useCrud } from '@fast-crud/fast-crud';
import { createCrudOptions } from './crud';
import { getBaseURL } from '/@/utils/baseUrl';
import FileSelector from '/@/components/fileSelector/index.vue';
import { SHOW } from '/@/components/fileSelector/types';

const fileSelectorRef = ref<any>(null);
const getSizeDisplay = (n: number) => n < 1024 ? n + 'b' : (n < 1024 * 1024 ? (n / 1024).toFixed(2) + 'Kb' : (n / (1024 * 1024)).toFixed(2) + 'Mb');

const openAddHandle = async () => {
  fileSelectorRef.value.selectVisiable = true;
  await nextTick();
};
// crud组件的ref
const crudRef = ref();
// crud 配置的ref
const crudBinding = ref();
// 暴露的方法
const { crudExpose } = useExpose({ crudRef, crudBinding });
// 你的crud配置
const { crudOptions } = createCrudOptions({ crudExpose, context: { openAddHandle } });
// 初始化crud配置
const { resetCrudOptions } = useCrud({ crudExpose, crudOptions });

const selected = ref<any>([]);
const openPreview = ref<boolean>(false);
const videoPreviewSrc = ref<string>('');
const audioPreviewSrc = ref<string>('');
const videoPreviewRef = ref<HTMLVideoElement>();
const audioPreviewRef = ref<HTMLAudioElement>();
const openPreviewHandle = (src: string, type: string) => {
  openPreview.value = true;
  (videoPreviewRef.value as HTMLVideoElement).muted = true;
  (audioPreviewRef.value as HTMLAudioElement).muted = true;
  if (type === 'video') videoPreviewSrc.value = src;
  else audioPreviewSrc.value = src;
  window.addEventListener('keydown', onPreviewKeydown);
};
const closePreview = () => {
  openPreview.value = false;
  videoPreviewSrc.value = '';
  audioPreviewSrc.value = '';
  window.removeEventListener('keydown', onPreviewKeydown);
};
const onPreviewKeydown = (e: KeyboardEvent) => {
  if (e.key !== 'Escape') return;
  openPreview.value = false;
  videoPreviewSrc.value = '';
  audioPreviewSrc.value = '';
  window.removeEventListener('keydown', onPreviewKeydown);
};

// 页面打开后获取列表数据
onMounted(() => {
  crudExpose.doRefresh();
});
</script>
<style lang="css" scoped>
</style>