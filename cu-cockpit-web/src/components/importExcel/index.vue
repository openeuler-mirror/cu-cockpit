<template #footer>

      <div  class="dialog-footer">
        <el-button type="primary" :disabled="loading" @click="submitFileForm">确 定</el-button>
        <el-button :disabled="loading" @click="uploadShow = false">取 消</el-button>
      </div>
      
</template>
<script lang="ts" setup name="importExcel">
import { request, downloadFile } from '/@/utils/service';
import {inject,ref} from "vue";
import { getBaseURL } from '/@/utils/baseUrl';
import { Session } from '/@/utils/storage';
import {  ElMessageBox } from 'element-plus'
import type { Action } from 'element-plus'
</script>
<style scoped>
</style>
