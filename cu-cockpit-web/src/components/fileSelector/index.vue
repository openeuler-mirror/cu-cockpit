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
</script>
<style scoped>
</style>