<template #cell_avatar="scope">

              <div v-if="scope.row.avatar" style="display: flex; justify-content: center; align-items: center;">
                <el-image 
                  style="width: 50px; height: 50px; border-radius: 50%; aspect-ratio: 1 /1 ; " 
                  :src="getBaseURL(scope.row.avatar)"
                  :preview-src-list="[getBaseURL(scope.row.avatar)]" 
                  :preview-teleported="true" />
              </div>
            
</template>
<script lang="ts" setup name="user">
import {useExpose, useCrud} from '@fast-crud/fast-crud';
import {createCrudOptions} from './crud';
import * as api from './api';
import {ElTree} from 'element-plus';
import {ref, onMounted, watch, toRaw, h} from 'vue';
import XEUtils from 'xe-utils';
import {getElementLabelLine} from 'element-tree-line';
import importExcel from '/@/components/importExcel/index.vue'
import {getBaseURL} from '/@/utils/baseUrl';
</script>
<style lang="scss" scoped>
</style>
