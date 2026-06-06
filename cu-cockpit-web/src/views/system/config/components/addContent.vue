<template>

	<div style="padding: 20px">
		<el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
			<el-form-item label="所属分组" prop="parent">
				<el-select v-model="form.parent" placeholder="请选择分组" clearable>
					<el-option :label="item.title" :value="item.id" :key="index" v-for="(item, index) in parentOptions"></el-option>
				</el-select>
			</el-form-item>
			<el-form-item label="标题" prop="title">
				<el-input v-model="form.title" placeholder="请输入" clearable></el-input>
			</el-form-item>
			<el-form-item label="key值" prop="key">
				<el-input v-model="form.key" placeholder="请输入" clearable></el-input>
			</el-form-item>
			<el-form-item label="表单类型" prop="form_item_type">
				<el-select v-model="form.form_item_type" placeholder="请选择" clearable>
					<el-option :label="item.label" :value="item.value" :key="index" v-for="(item, index) in dictionary('config_form_type')"></el-option>
				</el-select>
			</el-form-item>
			<el-form-item
				v-if="[4, 5, 6].indexOf(form.form_item_type) > -1"
				label="字典key"
				prop="setting"
				:rules="[{ required: true, message: '不能为空' }]"
			>
				<el-input v-model="form.setting" placeholder="请输入dictionary中key值" clearable></el-input>
			</el-form-item>
			<div v-if="[13, 14].indexOf(form.form_item_type) > -1">
				<associationTable ref="associationTableRef" v-model="form.setting" @updateVal="associationTableUpdate"></associationTable>
			</div>
			<el-form-item label="校验规则">
				<el-select v-model="form.rule" multiple placeholder="请选择(可多选)" clearable>
					<el-option :label="item.label" :value="item.value" :key="index" v-for="(item, index) in ruleOptions"></el-option>
				</el-select>
			</el-form-item>
			<el-form-item label="提示信息" prop="placeholder">
				<el-input v-model="form.placeholder" placeholder="请输入" clearable></el-input>
			</el-form-item>
			<el-form-item label="排序" prop="sort">
				<el-input-number v-model="form.sort" :min="0" :max="99"></el-input-number>
			</el-form-item>
			<el-form-item>
				<el-button type="primary" @click="onSubmit(formRef)">立即创建</el-button>
			</el-form-item>
		</el-form>
	</div>
</template>
<script setup lang="ts">
import * as api from '../api';
import associationTable from './components/associationTable.vue';
import {ref, reactive, onMounted, inject} from 'vue';
import type { FormInstance, FormRules } from 'element-plus';
import { successMessage } from '/@/utils/message';
import { dictionary } from '/@/utils/dictionary';
</script>
<style>
</style>
