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

const props = defineProps({
	type: {
		type: String,
		default: 'role',
	},
	title: {
		type: String,
		default: '标题',
	},
	label: {
		type: String,
		default: 'name',
	},
	value: {
		type: String,
		default: 'id',
	},
	showPagination: {
		type: Boolean,
		default: false,
	},
});
const emit = defineEmits(['fetchData', 'itemClick']);

const state = reactive<RoleInfoStateType>({
	current: '',
	page: 1,
	limit: 20,
	data: [],
	total: 10,
});

const fetchData = () => {
	emit(
		'fetchData',
		{
			page: state.page,
			limit: state.limit,
		},
		(res: { code: number; data: any[]; total: number }) => {
			if (res?.code === 2000) {
				state.data = res.data;
				state.total = res?.total || 10;
			}
		}
	);
};

const handleClick = (record: any) => {
	state.current = record[props.value];
	emit('itemClick', props.type, record);
};

const handleCurrentChange = (page: number) => {
	state.page = page;
	fetchData();
};

onMounted(() => {
	fetchData();
});
</script>
<style lang="scss" scoped>
</style>
