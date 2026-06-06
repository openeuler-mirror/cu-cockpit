<template>

	<div style="padding: 20px">
		<el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
			<el-form-item label="标题" prop="title">
				<el-input v-model="form.title"></el-input>
			</el-form-item>
			<el-form-item label="key值" prop="key">
				<el-input v-model="form.key"></el-input>
			</el-form-item>
			<el-form-item>
				<el-button type="primary" @click="onSubmit(formRef)">立即创建</el-button>
				<el-button>取消</el-button>
			</el-form-item>
		</el-form>
	</div>
</template>
<script setup lang="ts">
import * as api from '../api';
import {ref, reactive, inject} from 'vue';
import type { FormInstance, FormRules } from 'element-plus';
import { successMessage } from '/@/utils/message';
</script>
<style>
</style>
