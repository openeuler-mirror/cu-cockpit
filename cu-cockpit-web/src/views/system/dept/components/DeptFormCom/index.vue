<template>

	<el-form ref="formRef" :rules="rules" :model="deptFormData" label-width="100px" label-position="right" class="dept-form-com">
		<el-form-item label="父级部门" prop="parent">
			<el-tree-select
				v-model="deptFormData.parent"
				:props="defaultTreeProps"
				:data="deptDefaultList"
				:cache-data="props.cacheData"
				lazy
				check-strictly
				:load="handleTreeLoad"
				style="width: 100%"
			/>
		</el-form-item>
		<el-form-item required label="部门名称" prop="name">
			<el-input v-model="deptFormData.name" />
		</el-form-item>
		<el-form-item required label="部门标识" prop="key">
			<el-input v-model="deptFormData.key" />
		</el-form-item>
		<el-form-item label="负责人">
			<el-input v-model="deptFormData.owner" placeholder="请输入" />
		</el-form-item>
		<el-form-item label="备注">
			<el-input v-model="deptFormData.description" maxlength="200" show-word-limit type="textarea" />
		</el-form-item>
		<el-form-item>
			<el-button @click="handleUpdateMenu" type="primary" :loading="deptBtnLoading">
				{{ deptFormData.id ? '保存' : '新增' }}
			</el-button>
			<el-button @click="handleClose">取消 </el-button>
		</el-form-item>
	</el-form>
</template>
<script lang="ts" setup>
import { reactive, ref, onMounted } from 'vue';
import { ElForm, FormRules } from 'element-plus';
import { lazyLoadDept, AddObj, UpdateObj } from '../../api';
import { successNotification } from '/@/utils/message';
import { DeptFormDataType, TreeItemType, APIResponseData } from '../../types';
import type Node from 'element-plus/es/components/tree/src/model/node';
</script>
<style lang="scss" scoped>
</style>
