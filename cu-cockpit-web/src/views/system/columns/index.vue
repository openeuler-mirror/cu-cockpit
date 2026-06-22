<template>

	<fs-page class="columns">
		<el-row class="columns-el-row" :gutter="10">
			<el-col :span="6">
				<div class="columns-box columns-left">
					<ItemCom title="角色" type="role" showPagination @fetchData="fetchRoleData" @itemClick="handleClick" />
				</div>
			</el-col>
<!--      <el-col :span="4">-->
<!--        <div class="columns-box columns-left">-->
<!--          <ItemCom title="菜单" type="menu" showPagination @fetchData="fetchMenuData" @itemClick="handleClick" />-->
<!--        </div>-->
<!--      </el-col>-->
			<el-col :span="8">
				<div class="columns-box columns-center">
					<ItemCom title="模型表" type="model" label="showText" value="key" @fetchData="fetchModelData" @itemClick="handleClick" />
				</div>
			</el-col>
			<el-col :span="10">
				<div class="columns-box columns-right">
					<ColumnsTableCom ref="columnsTableRef" :currentInfo="currentInfo" />
				</div>
			</el-col>
		</el-row>
	</fs-page>
</template>
<script lang="ts" setup>
import { ref, reactive } from 'vue';
import ItemCom from './components/ItemCom/index.vue';
import ColumnsTableCom from './components/ColumnsTableCom/index.vue';
import { getRoleList, getModelList,getMenuList } from './api';
import { PageQuery, CurrentInfoType, ModelItemType } from './types';
</script>
<style lang="scss" scoped>
</style>
