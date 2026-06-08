<template>

	<div class="pccm-item" v-if="RoleMenuField.$state.length > 0">
		<div class="menu-form-alert">
			<el-button size="small" @click="handleSaveField">保存 </el-button>
			配置数据列字段权限
		</div>

		<ul class="columns-list">
			<li class="columns-head">
				<div class="width-txt">
					<span>字段</span>
				</div>
				<div v-for="(head, hIndex) in RoleMenuFieldHeader.$state" :key="hIndex" class="width-check">
					<el-checkbox v-model="head.checked" @change="handleColumnChange($event, head.value, head.disabled)">
						<span>{{ head.label }}</span>
					</el-checkbox>
				</div>
			</li>
			<div class="columns-content">
				<li v-for="(c_item, c_index) in RoleMenuField.$state" :key="c_index" class="columns-item">
					<div class="width-txt">{{ c_item.title }}</div>
					<div v-for="(col, cIndex) in RoleMenuFieldHeader.$state" :key="cIndex" class="width-check">
						<el-checkbox v-model="c_item[col.value]" class="ci-checkout" :disabled="c_item[col.disabled]"></el-checkbox>
					</div>
				</li>
			</div>
		</ul>
	</div>
</template>
<script setup lang="ts">
import { ElMessage } from 'element-plus';
import { RoleDrawerStores } from '../stores/RoleDrawerStores';
import { RoleMenuFieldStores, RoleMenuFieldHeaderStores } from '../stores/RoleMenuFieldStores';
import { setRoleMenuField } from './api';
</script>
<style lang="scss" scoped>
</style>
