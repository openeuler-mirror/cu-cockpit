<template>

	<div class="item-com">
		<p class="item-com-title">{{ props.title }}</p>
		<ul class="item-com-list" :style="{ height: showPagination ? 'calc(100% - 75px)' : 'calc(100% - 45px)' }">
			<li
				v-for="item in state.data"
				:key="item[props.value]"
				@click="handleClick(item)"
				:class="state.current === item[props.value] ? 'item-com-item active' : 'item-com-item'"
			>
				{{ item[props.label] }}
			</li>
		</ul>
		<div v-if="showPagination" class="item-com-pagination">
			<el-pagination
				background
				small
				hide-on-single-page
				v-model:current-page="state.page"
				v-model:page-size="state.limit"
				layout="prev, pager, next"
				:pager-count="5"
				:total="state.total"
				@current-change="handleCurrentChange"
			/>
		</div>
	</div>
</template>
<script lang="ts" setup>
import { reactive, onMounted } from 'vue';
import { RoleInfoStateType } from './types';
</script>
<style lang="scss" scoped>
</style>
