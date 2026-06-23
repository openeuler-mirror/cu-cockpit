<template #default="scope">

									<el-button text type="info" :icon="Close" @click="removeSelectedRows(scope.row)" circle />
								
</template>
<script lang="ts" setup>
import { ref, onMounted, reactive, computed } from 'vue';
import { useFs } from '@fast-crud/fast-crud';
import { createCrudOptions } from './crud';
import { BatchDelete, getModelList } from './api';
import { Close, Delete } from '@element-plus/icons-vue';
import { MenuTreeItemType } from '/@/views/system/menu/types';
import { successMessage, successNotification, warningNotification } from '/@/utils/message';
import { automatchColumnsData } from '/@/views/system/columns/components/ColumnsTableCom/api';
import XEUtils from 'xe-utils';
import { ElMessage, ElMessageBox } from 'element-plus';
</script>
<style scoped lang="scss">
</style>
