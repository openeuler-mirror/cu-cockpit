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
const refreshView = inject('refreshView')

let props = defineProps({
  upload: {
    type: Object,
    default () {
      return {
        // 是否显示弹出层
        open: true,
        // 弹出层标题
        title: '',
        // 是否禁用上传
        isUploading: false,
        // 是否更新已经存在的用户数据
        updateSupport: 0,
        // 设置上传的请求头部
        headers: { Authorization: 'JWT ' + Session.get('token') },
        // 上传的地址
        url: getBaseURL() + 'api/system/file/'
      }
    }
  },
  api: { // 导入接口地址
    type: String,
    default () {
      return undefined
    }
  }
})

let loading = ref(false)
const uploadRef = ref()
const uploadShow = ref(false)
const isUploading = ref(false)
/** 导入按钮操作 */
const handleImport = function () {
  uploadShow.value = true
}

/** 下载模板操作 */
</script>
<style scoped>
</style>
