<template #footer v-if="props.showInput">

        <el-button type="default" @click="onClose">取消</el-button>
        <el-button type="primary" @click="onSave">确定</el-button>
      
</template>
<script setup lang="ts">

import { useUi, UserPageQuery, AddReq, EditReq, DelReq } from '@fast-crud/fast-crud';
import { ref, reactive, defineProps, PropType, watch, onMounted, nextTick } from 'vue';
import { getBaseURL } from '/@/utils/baseUrl';
import { request } from '/@/utils/service';
import { SHOW } from './types';
import FileItem from './fileItem.vue';
import { pluginsAll } from '/@/views/plugins/index';
import { storeToRefs } from "pinia";
import { useUserInfo } from "/@/stores/userInfo";
import { errorNotification, successNotification } from '/@/utils/message';

const userInfos = storeToRefs(useUserInfo()).userInfos;
const isTenentMode = !!(pluginsAll && pluginsAll.length && pluginsAll.indexOf('tenants-web') >= 0);
const isSuperTenent = (userInfos.value as any).schema_name === 'public';

const TypeLabel = ['图片', '视频', '音频', '文件']
const AcceptList = ['image/*', 'video/*', 'audio/*', ''];
const props = defineProps({
  modelValue: {},
  class: { type: Object as PropType<String | Object>, default: '' },
  inputClass: { type: Object as PropType<String | Object>, default: '' },
  style: { type: Object as PropType<Object | string>, default: {} },
  inputStyle: { type: Object as PropType<Object | string>, default: {} },
  disabled: { type: Boolean, default: false },

  tabsType: { type: Object as PropType<'' | 'card' | 'border-card'>, default: '' },
  itemSize: { type: Number, default: 100 },

  // 1000图片 100视频 10音频 1 其他 控制tabs的显示
  tabsShow: { type: Number, default: SHOW.ALL },

  // 是否可以多选，默认单选
  // 该值为true时inputType必须是selector或image（暂不支持其他type的多选）
  multiple: { type: Boolean, default: false },

  // 是否可选，该参数用于只上传和展示而不选择和绑定model的情况
  selectable: { type: Boolean, default: true },

  // 该参数用于控制是否显示表单item。若赋值为false，则不会显示表单item，也不会显示底部按钮
  // 如果不显示表单item，则无法触发dialog，需要父组件通过修改本组件暴露的 selectVisiable 状态来控制dialog
  showInput: { type: Boolean, default: true },

  // 表单item类型，不为selector是需要设置valueKey，否则可能获取不到媒体数据
  inputType: { type: Object as PropType<'selector' | 'image' | 'video' | 'audio'>, default: 'selector' },
  // inputType不为selector时生效
  inputSize: { type: Number, default: 100 },

  // v-model绑定的值是file数据的哪个key，默认是url
  valueKey: { type: String, default: 'url' },

  showUploadButton: { type: Boolean, default: true },
  showNetButton: { type: Boolean, default: true },
} as any);

const selectVisiable = ref<boolean>(false);
const tabsActived = ref<number>([3, 2, 1, 0][((props.tabsShow & (props.tabsShow - 1)) === 0) ? Math.log2(props.tabsShow) : 3]);
const fileApiPrefix = '/api/system/file/';
const fileApi = {
  GetList: (query: UserPageQuery) => request({ url: fileApiPrefix, method: 'get', params: query }),
  AddObj: (obj: AddReq) => request({ url: fileApiPrefix, method: 'post', data: obj }),
  DelObj: (id: DelReq) => request({ url: fileApiPrefix + id + '/', method: 'delete', data: { id } }),
  GetAll: () => request({ url: fileApiPrefix + 'get_all/' }),
};
// 过滤表单
const filterForm = reactive({ name: '' });
// 分页表单
const pageForm = reactive({ page: 1, limit: 10, total: 0 });
// 展示的数据列表
const listData = ref<any[]>([]);
const listAllData = ref<any[]>([]);
const listRequest = async () => {
  let res = await fileApi.GetList({
    page: pageForm.page,
    limit: pageForm.limit,
    file_type: isTenentMode ? tabsActived.value % 4 : tabsActived.value,
    system: tabsActived.value > 3,
    upload_method: 1,
    ...filterForm
  });
  listData.value = [];
  await nextTick();
  listData.value = (res.data as any[]).map((item: any) => ({ ...item, url: getBaseURL(item.url) }));
  pageForm.total = res.total;
  pageForm.page = res.page;
  pageForm.limit = res.limit;
  selectedInit();
};
const formDisplayEnter = (e: MouseEvent) => (e.target as HTMLElement).style.setProperty('--fileselector-close-display', 'block');
const formDisplayLeave = (e: MouseEvent) => (e.target as HTMLElement).style.setProperty('--fileselector-close-display', 'none');
const listRequestAll = async () => {
  if (props.inputType !== 'selector') return;
  let res = await fileApi.GetAll();
  listAllData.value = res.data;
};
// tab改变时触发
const handleTabChange = (name: string) => { pageForm.page = 1; listRequest(); };
// 分页器改变时触发
const handlePageChange = (currentPage: number, pageSize: number) => { pageForm.page = currentPage; pageForm.limit = pageSize; listRequest(); };
// 选择的行为
const listContainerRef = ref<any>();
const onItemClick = async (e: MouseEvent) => {
  if (!props.selectable) return;
  let target = e.target as HTMLElement;
  let flat = 0;  // -1删除 0不变 1添加
  while (!target.dataset.id) target = target.parentElement as HTMLElement;
  let fileId = target.dataset.id;
  if (props.multiple) {
    if (!!!data.value) data.value = [];
    if (target.classList.contains('active')) { target.classList.remove('active'); flat = -1; }
    else { target.classList.add('active'); flat = 1; }
    if (data.value.length) {
      let _l = JSON.parse(JSON.stringify(data.value));
      if (flat === 1) _l.push(fileId);
      else _l.splice(_l.indexOf(fileId), 1);
      data.value = _l;
    } else data.value = [fileId];
    // 去重排序，<降序，>升序
    data.value = Array.from(new Set(data.value)).sort();
  } else {
    for (let i of listContainerRef.value?.children) (i as HTMLElement).classList.remove('active');
    target.classList.add('active');
    data.value = fileId;
  }
  // onDataChange(data.value);
};
// 每次列表刷新都得更新一下选择状态，因为所有标签页共享列表
const selectedInit = async () => {
  if (!props.selectable) return;
  await nextTick(); // 不等待一次不会刷新
  for (let i of (listContainerRef.value?.children || [])) {
    i.classList.remove('active');
    let fid = (i as HTMLElement).dataset.id;
    if (props.multiple) { if (data.value?.includes(fid)) i.classList.add('active'); }
    else { if (fid === data.value) i.classList.add('active'); }
  }
};
const uploadRef = ref<any>();
const onSave = () => {
  onDataChange(data.value);
  emit('onSave', data.value);
  selectVisiable.value = false;
};
const onClose = () => {
  data.value = props.modelValue;
  emit('onClose');
  selectVisiable.value = false;
};
const onClosed = () => {
  clearState();
  emit('onClosed');
};
// 清空状态
const clearState = () => {
  filterForm.name = '';
  pageForm.page = 1;
  pageForm.limit = 10;
  pageForm.total = 0;
  listData.value = [];
  // all数据不能清，因为all只会在挂载的时候赋值一次
  // listAllData.value = [];
};
const clear = () => { data.value = null; onDataChange(null); };
const clearOne = (item: any) => {
  let _l = (JSON.parse(JSON.stringify(data.value)) as any[]).filter((i: any) => i !== item)
  data.value = _l;
  onDataChange(_l);
};

// 网络文件部分
const netLoading = ref<boolean>(false);
const netVisiable = ref<boolean>(false);
const netUrl = ref<string>('');
const netPrefix = ref<string>('HTTP://');
const netChange = () => {
  let s = netUrl.value.trim();
  if (s.toUpperCase().startsWith('HTTP://') || s.toUpperCase().startsWith('HTTPS://')) s = s.split('://')[1];
  if (s.startsWith('/')) s = s.substring(1);
  netUrl.value = s;
};
const confirmNetUrl = () => {
  if (!netUrl.value) return;
  netLoading.value = true;
  let controller = new AbortController();
  let timeout = setTimeout(() => {
    controller.abort();
  }, 10 * 1000);
  fetch(netPrefix.value + netUrl.value, { signal: controller.signal }).then(async (res: Response) => {
    clearTimeout(timeout);
    if (!res.ok) errorNotification(`网络${TypeLabel[tabsActived.value % 4]}获取失败！`);
    const _ = res.url.split('?')[0].split('/');
    let filename = _[_.length - 1];
    // let filetype = res.headers.get('content-type')?.split('/')[1] || '';
    let blob = await res.blob();
    let file = new File([blob], filename, { type: blob.type });
    let form = new FormData();
    form.append('file', file);
    form.append('upload_method', '1');
    fetch(getBaseURL() + 'api/system/file/', { method: 'post', body: form })
      .then(() => successNotification('网络文件上传成功！'))
      .then(() => { netVisiable.value = false; listRequest(); listRequestAll(); })
      .catch(() => errorNotification('网络文件上传失败！'))
      .then(() => netLoading.value = false);
  }).catch((err: any) => {
    console.log(err);
    clearTimeout(timeout);
    errorNotification(`网络${TypeLabel[tabsActived.value % 4]}获取失败！`);
    netLoading.value = false;
  });
};




// fs-crud部分
const data = ref<any>(null);
const emit = defineEmits(['update:modelValue', 'onSave', 'onClose', 'onClosed']);
watch(
  () => props.modelValue,
  (val) => data.value = props.multiple ? JSON.parse(JSON.stringify(val)) : val,
  { immediate: true }
);
const { ui } = useUi();
const formValidator = ui.formItem.injectFormItemContext();
const onDataChange = (value: any) => {
  let _v = null;
  if (value) {
    if (typeof value === 'string') _v = value.replace(/\\/g, '/');
    else {
      _v = [];
      for (let i of value) _v.push(i.replace(/\\/g, '/'));
    }
  }
  emit('update:modelValue', _v);
  formValidator.onChange();
  formValidator.onBlur();
};

defineExpose({ data, onDataChange, selectVisiable, clearState, clear });

onMounted(() => {

  if (props.multiple && !['selector', 'image'].includes(props.inputType))
    throw new Error('FileSelector组件属性multiple为true时inputType必须为selector');
  listRequestAll();
  console.log('fileselector tenentmdoe', isTenentMode);
  console.log('fileselector supertenent', isSuperTenent);
});
</script>
<style scoped>

.form-display {
  --fileselector-close-display: none;
  overflow: hidden;
}

._overlay {
  width: unset !important;
}

.headerBar>* {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

:deep(.el-input-group__prepend) {
  padding: 0 20px;
}

.listContainer {
  display: grid;
  justify-items: center;
  grid-template-columns: repeat(4, 1fr);
  grid-auto-rows: min-content;
  grid-gap: 36px;
  margin-top: 24px;
  padding: 8px;
  height: calc(50vh);
  overflow-y: auto;
  scrollbar-width: thin;
}

.listContainer>* {
  aspect-ratio: 1 / 1;
  box-shadow: 0 0 4px rgba(0, 0, 0, .2);
  border-radius: 8px;
  overflow: hidden;
}

.active {
  box-shadow: 0 0 8px var(--el-color-primary);
}

.listPaginator {
  display: flex;
  justify-content: flex-end;
  justify-items: center;
  padding-top: 24px;
}

.addControllorHover {
  width: 100%;
  height: 100%;
  position: absolute;
  left: 0;
  top: 0;
  cursor: pointer;
  border-radius: 8px;
  border: 1px solid #dcdfe6;
}

.addControllorHover:hover {
  border-color: #c0c4cc;
}

.closeHover {
  display: var(--fileselector-close-display);
  position: absolute;
  right: 2px;
  top: 2px;
  cursor: pointer;
}

.itemList {
  border: 1px solid #dcdfe6;
  border-radius: 8px;
}
</style>