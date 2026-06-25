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


const ElementTreeLine = getElementLabelLine(h);

interface Tree {
  id: number;
  name: string;
  status: boolean;
  children?: Tree[];
}

interface APIResponseData {
  code?: number;
  data: [];
  msg?: string;
}

// 引入组件
const placeholder = ref('请输入部门名称');
const filterText = ref('');
const treeRef = ref<InstanceType<typeof ElTree>>();

const treeProps = {
  children: 'children',
  label: 'name',
  icon: 'icon',
};

watch(filterText, (val) => {
  treeRef.value!.filter(val);
});

const filterNode = (value: string, data: Tree) => {
  if (!value) return true;
  return toRaw(data).name.indexOf(value) !== -1;
};

let data = ref([]);

const content = `
1.部门信息;
`;

const getData = () => {
  api.GetDept({}).then((ret: APIResponseData) => {
    const responseData = ret.data;
    const result = XEUtils.toArrayTree(responseData, {
      parentKey: 'parent',
      children: 'children',
    });

    data.value = result;
  });
};

//树形点击事件
const onTreeNodeClick = (node: any) => {
  const {id} = node;
  crudExpose.doSearch({form: {dept: id}});
};

// 页面打开后获取列表数据
onMounted(() => {
  getData();
});

// crud组件的ref
const crudRef = ref();
// crud 配置的ref
const crudBinding = ref();
// 暴露的方法
const {crudExpose} = useExpose({crudRef, crudBinding});
// 你的crud配置
const {crudOptions} = createCrudOptions({crudExpose});
// 初始化crud配置
const {resetCrudOptions} = useCrud({crudExpose, crudOptions});

// 页面打开后获取列表数据
onMounted(() => {
  crudExpose.doRefresh();
});
</script>
<style lang="scss" scoped>
</style>
