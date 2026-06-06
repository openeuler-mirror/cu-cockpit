<template>

	<div class="columns-form-com">
		<el-form ref="formRef" :model="formData" :rules="formRules" label-width="80px">
			<el-form-item label="字段名" prop="field_name">
				<el-input v-model="formData.field_name" placeholder="请输入字段名" />
			</el-form-item>

			<el-form-item label="列名" prop="title">
				<el-input v-model="formData.title" placeholder="请输入列名" />
			</el-form-item>

			<el-form-item label="创建显示">
				<el-switch v-model="formData.is_create" />
			</el-form-item>

			<el-form-item label="编辑显示">
				<el-switch v-model="formData.is_update" />
			</el-form-item>

			<el-form-item label="查询显示">
				<el-switch v-model="formData.is_query" />
			</el-form-item>

			<el-form-item>
				<el-button type="primary" @click="handleSubmit" :loading="btnLoading"> 确定 </el-button>
				<el-button @click="handleClose">取消</el-button>
			</el-form-item>
		</el-form>
	</div>
</template>
<script lang="ts" setup>
import { reactive, ref, onMounted } from 'vue';
import { addColumnsData, updateColumnsData } from '../ColumnsTableCom/api';
import { successNotification } from '/@/utils/message';
import { CurrentInfoType, ColumnsFormDataType } from '../../types';
import type { FormInstance } from 'element-plus';
</script>
<style lang="scss" scoped>
</style>
