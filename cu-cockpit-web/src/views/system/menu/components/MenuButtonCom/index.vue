<template #default="scope">

								<el-button text type="info" :icon="Close" @click="removeSelectedRows(scope.row)" circle />
							
</template>
<script lang="ts" setup>
import { computed, ref } from 'vue';
import { useFs } from '@fast-crud/fast-crud';
import { createCrudOptions } from './crud';
import { MenuTreeItemType } from '../../types';
import { ElMessage, ElMessageBox } from 'element-plus';
import XEUtils from 'xe-utils';
import { BatchDelete } from './api';
import { Close, Delete } from '@element-plus/icons-vue';
</script>
