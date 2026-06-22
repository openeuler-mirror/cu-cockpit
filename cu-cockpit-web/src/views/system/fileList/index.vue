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
</script>
<style lang="css" scoped>
</style>