<template>

	<fs-page>
		<el-row class="dept-el-row">
			<el-col :span="6">
				<div class="dept-box dept-left">
					<DeptTreeCom
						ref="deptTreeRef"
						:treeData="deptTreeData"
						@treeClick="handleTreeClick"
						@updateDept="handleUpdateMenu"
						@deleteDept="handleDeleteMenu"
					/>
				</div>
			</el-col>

			<el-col :span="18">
				<div class="dept-box dept-table">
					<DeptUserCom ref="deptUserRef" />
				</div>
			</el-col>
		</el-row>

		<el-drawer v-model="drawerVisible" title="部门配置" direction="rtl" size="500px" :close-on-click-modal="false" :before-close="handleDrawerClose">
			<DeptFormCom
				v-if="drawerVisible"
				:initFormData="drawerFormData"
				:treeData="deptTreeData"
				:cacheData="deptTreeCacheData"
				@drawerClose="handleDrawerClose"
			/>
		</el-drawer>
	</fs-page>
</template>
<script lang="ts" setup name="dept">
import { ref, onMounted } from 'vue';
import XEUtils from 'xe-utils';
import { ElMessageBox } from 'element-plus';
import DeptTreeCom from './components/DeptTreeCom/index.vue';
import DeptFormCom from './components/DeptFormCom/index.vue';
import DeptUserCom from './components/DeptUserCom/index.vue';
import { GetList, DelObj } from './api';
import { successNotification } from '../../../utils/message';
import { APIResponseData, TreeItemType } from './types';
</script>
<style lang="scss" scoped>
</style>
