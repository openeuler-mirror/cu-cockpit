<template #pagination-left>

			<el-tooltip content="批量删除所选择的用户权限">
				<el-button v-show="selectedRowsCount > 0 && auth('role:SetMenu')" type="danger"  @click="multipleDel" :icon="Delete">批量删除</el-button>
			</el-tooltip>
		
</template>
<script lang="ts" setup>

import {auth} from "/@/utils/authFunction";
import { ref, onMounted, defineAsyncComponent, computed } from 'vue';
import { useFs } from '@fast-crud/fast-crud';
import { createCrudOptions } from './crud';
import { Close, Delete } from '@element-plus/icons-vue';
import XEUtils from 'xe-utils';
import {removeRoleUser} from "./api"
import { ElMessageBox } from 'element-plus';
import { errorMessage, successNotification } from '/@/utils/message';

import { RoleUserStores } from '../../stores/RoleUserStores';
const RoleUserDrawer = RoleUserStores(); // 授权用户抽屉参数

const subUser = defineAsyncComponent(() => import('../addUsers/index.vue'));
const subUserRef = ref();

const refreshData = () => {
  crudExpose.doRefresh();
};

//抽屉是否显示
const drawer = ref(false);

//抽屉关闭确认
const handleClose = (done: () => void) => {
	selectedRows.value = [];
	done();
};

// 选中行的条数
const selectedRowsCount = computed(() => {
	return selectedRows.value.length;
});

const removeSelectedRows = (row: any) => {
	const tableRef = crudExpose.getBaseTableRef();
	const tableData = crudExpose.getTableData();
	if (XEUtils.pluck(tableData, 'id').includes(row.id)) {
		tableRef.toggleRowSelection(row, false);
	} else {
		selectedRows.value = XEUtils.remove(selectedRows.value, (item: any) => item.id !== row.id);
	}
};

const multipleDel = async ()  => {
	if (selectedRows.value.length < 1) {
		errorMessage("请先勾选用户");
		return
	} 
	await ElMessageBox.confirm(`确定要删除这 “${selectedRows.value.length}” 位用户的权限吗`, "确认");
		const req = await removeRoleUser(crudRef.value.getSearchFormData().role_id, XEUtils.pluck(selectedRows.value, 'id'));
		selectedRows.value = [];
		successNotification(req.msg)
		crudExpose.doRefresh()
}

const { crudBinding, crudRef, crudExpose, selectedRows } = useFs({ createCrudOptions, context: {subUserRef} });
const { setSearchFormData, doRefresh } = crudExpose;

defineExpose({ drawer, setSearchFormData, doRefresh });

</script>
