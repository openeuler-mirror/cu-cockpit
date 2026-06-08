<template>

	<el-tree
		ref="treeRef"
		:data="menuData"
		:props="defaultTreeProps"
		:default-checked-keys="menuDefaultCheckedKeys"
		@check-change="handleMenuChange"
		@node-click="handleMenuClick"
		node-key="id"
		check-strictly
		highlight-current
		show-checkbox
		default-expand-all
		:check-on-click-leaf="false"
	>
	</el-tree>
</template>
<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { RoleDrawerStores } from '../stores/RoleDrawerStores';
import { RoleMenuTreeStores } from '../stores/RoleMenuTreeStores';
import { RoleMenuBtnStores } from '../stores/RoleMenuBtnStores';
import { RoleMenuFieldStores } from '../stores/RoleMenuFieldStores';
import { RoleMenuFieldHeaderStores } from '../stores/RoleMenuFieldStores';
import { getRoleMenu, getRoleMenuBtnField, setRoleMenu } from './api';
import { ElMessage } from 'element-plus';
import XEUtils from 'xe-utils';
import { RoleMenuTreeType } from '../types';
</script>
