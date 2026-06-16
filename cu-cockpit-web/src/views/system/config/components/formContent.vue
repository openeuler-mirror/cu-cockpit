<template #reference>

              <el-button size="mini" type="danger" :icon="Delete" ></el-button>
            
</template>
<script setup lang="ts">

import * as api from '../api';
import { dictionary } from '/@/utils/dictionary';
import { getBaseURL } from '/@/utils/baseUrl';
import { ref, reactive, watch, nextTick,inject  } from 'vue';
import type { FormInstance, FormRules, TableInstance } from 'element-plus';
import { successMessage, errorMessage } from '/@/utils/message';
import { Session } from '/@/utils/storage';
import {Edit,Finished,Delete} from "@element-plus/icons-vue";
import crudTable from "./components/crudTable.vue"
const props = defineProps(['options', 'editableTabsItem']);

let formData: any = ref({});
let formList: any = ref([]);
const formRef =  ref<FormInstance>()
let uploadUrl = ref(getBaseURL() + 'api/system/file/');
let uploadHeaders = ref({
  Authorization: 'JWT ' + Session.get('token'),
});
let dialogImageUrl = ref('');
let dialogImgVisible = ref(false);
let uploadImgKey = ref(null);

// 获取数据
const getInit = () => {
  api.GetList({ parent: props.options.id, limit: 999 }).then((res: any) => {
    let data = res.data;
    formList.value = data;
    const _formData: any = {};
    for (const item of data) {
      const key = item.key;
      if (item.value) {
        _formData[key] = item.value;
      } else {
        if ([5, 12,11, 14].indexOf(item.form_item_type) !== -1) {
          _formData[key] = item.value || [];
        } else {
          _formData[key] = item.value;
        }
      }
    }
    formData.value = Object.assign({}, _formData)
  });
};

// 提交数据
const onSubmit = (formEl: FormInstance | undefined) => {
  const keys = Object.keys(formData.value);
  const values = Object.values(formData.value);
  for (const index in formList.value) {
    const item = formList.value[index];
    // 赋值操作
    keys.forEach((mapKey, mapIndex) => {
      if (mapKey === item.key) {
        item.value = values[mapIndex];
        // 必填项的验证
        if (['img', 'imgs'].indexOf(item.form_item_type_label) > -1) {
          for (const arr of item.rule) {
            if (arr.required && item.value === null) {
              errorMessage(item.title + '不能为空');
              return;
            }
          }
        }
      }
    });
  }
  // formRef.value.clearValidate();
  if (!formEl) return
  formEl.validate((valid:any) => {
    if (valid) {
      api.saveContent(formList.value).then((res:any) => {
        successMessage('保存成功');
        refreshView&&refreshView();
      });
    } else {
      console.log('error submit!!');
      return false;
    }
  });
};


// 图片预览
const handlePictureCardPreview = (file: any) => {
  dialogImageUrl = file.url;
  dialogImgVisible.value = true;
};

// 判断是否为图片
// 封装一个判断图片文件后缀名的方法
const isImage = (fileName: any) => {
  if (typeof fileName !== 'string') return;
  const name = fileName.toLowerCase();
  return name.endsWith('.png') || name.endsWith('.jpeg') || name.endsWith('.jpg') || name.endsWith('.png') || name.endsWith('.bmp');
};

// 上传成功
const handleUploadSuccess = (response: any, file: any, fileList: any, imgKey: any) => {
  const that = this;
  const { code, msg } = response;
  if (code === 2000) {
    const { url } = response.data;
    const { name } = file;
    const type = isImage(name);
    if (!type) {
      errorMessage('只允许上传图片');
    } else {
      const uploadImgKey = formData[imgKey];
      if (!uploadImgKey || uploadImgKey === '') {
        formData[imgKey] = [];
      }
      // console.log(len)
      const dict = {
        name: name,
        url: getBaseURL() + url,
      };
      formData[imgKey].push(dict);
    }
  } else {
    errorMessage('上传失败,' + JSON.stringify(msg));
  }
};

// 上传失败
const handleError = () => {
  errorMessage('上传失败');
};

// 上传超出限制
const handleExceed = () => {
  errorMessage('超过文件上传数量');
};

// 删除时的钩子
const beforeRemove = (file: any, fileList: any, key: any) => {
  var index = 0;
  formData[key].map((value: any, inx: any) => {
    if (value.uid === file.uid) index = inx;
  });
  formData[key].splice(index, 1);
};

// 配置的行删除
const onDelRow = (obj: any) => {
  api.DelObj(obj.id).then((res: any) => {
    // this.refreshView();
  });
};

// 行编辑
const onEdit = (index: any) => {
  formList.value[index].edit =true
  formList.value[index].new_key =formList.value[index].key
};
// 行编辑保存
const refreshView = inject<Function>('refreshView')
const onEditSave = (obj: any) => {
  obj.key = JSON.parse(JSON.stringify(obj.new_key));
  api.UpdateObj(obj).then((res: any) => {
    refreshView && refreshView()
  });
};

watch(
    props.options,
    (nv) => {
      if (nv && nv.id) {
        getInit();
      }
    },
    { immediate: true }
);
</script>
<style scoped>

</style>
