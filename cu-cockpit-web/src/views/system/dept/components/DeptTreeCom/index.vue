<template>

	<el-input v-model="filterVal" :prefix-icon="Search" placeholder="请输入部门名称" />
</template>
<script lang="ts" setup>

import { ref, watch, toRaw, h } from 'vue';
import { ElTree } from 'element-plus';
import { getElementLabelLine } from 'element-tree-line';
import { Search } from '@element-plus/icons-vue';
import { lazyLoadDept, deptMoveUp, deptMoveDown } from '../../api';
import { warningNotification } from '/@/utils/message';
import { TreeItemType, APIResponseData } from '../../types';
import type Node from 'element-plus/es/components/tree/src/model/node';

interface IProps {
	treeData: TreeItemType[];
}

const ElementTreeLine = getElementLabelLine(h);

const defaultTreeProps: any = {
	children: 'children',
	label: 'name',
	isLeaf: (data: TreeItemType[], node: Node) => {
		if (node.data.hasChild) {
			return false;
		} else {
			return true;
		}
	},
};

withDefaults(defineProps<IProps>(), {
	treeData: () => [],
});
const emit = defineEmits(['treeClick', 'deleteDept', 'updateDept']);

let filterVal = ref('');
let showTotalNum = ref(false);
let sortDisable = ref(false);
let treeSelectDept = ref<TreeItemType>({});
let treeSelectNode = ref<Node | null>(null);
const treeRef = ref<InstanceType<typeof ElTree>>();

watch(filterVal, (val) => {
	treeRef.value!.filter(val);
});

/**
 * 部门树的搜索事件
 */
const handleFilterTreeNode = (value: string, data: TreeItemType) => {
	if (!value) return true;
	return toRaw(data).name?.indexOf(value) !== -1;
};

/**
 * 部门树的懒加载
 */
const handleLoadNode = (node: Node, resolve: Function) => {
	if (node.level !== 0) {
		lazyLoadDept({ parent: node.data.id }).then((res: APIResponseData) => {
			resolve(res.data);
		});
	}
};

/**
 * 部门的点击事件
 */
const handleNodeClick = (record: TreeItemType, node: Node) => {
	treeSelectDept.value = record;
	treeSelectNode.value = node;
	emit('treeClick', record);
};

/**
 * 新增 or 编辑 操作
 */
const handleUpdateMenu = (type: string) => {
	if (type === 'update') {
		if (!treeSelectDept.value.id) {
			warningNotification('请选择菜单！');
			return;
		}
		emit('updateDept', type, treeSelectDept.value);
	} else {
		emit('updateDept', type);
	}
};

/**
 * 删除部门
 */
const handleDeleteDept = () => {
	if (!treeSelectDept.value.id) {
		warningNotification('请选择菜单！');
		return;
	}
	emit('deleteDept', treeSelectDept.value.id, () => {
		treeSelectDept.value = {};
	});
};

/**
 * 部门上下移动操作
 */
const handleSort = async (type: string) => {
	if (!treeSelectDept.value.id) {
		warningNotification('请选择菜单！');
		return;
	}
	if (sortDisable.value) return;

	const parentList = treeSelectNode.value?.parent.childNodes || [];
	const index = parentList.findIndex((i) => i.data.id === treeSelectDept.value.id);
	const record = parentList.find((i) => i.data.id === treeSelectDept.value.id);

	if (type === 'up') {
		if (index === 0) return;
		parentList.splice(index - 1, 0, record as any);
		parentList.splice(index + 1, 1);
		sortDisable.value = true;
		await deptMoveUp({ dept_id: treeSelectDept.value.id });
		sortDisable.value = false;
	}
	if (type === 'down') {
		parentList.splice(index + 2, 0, record as any);
		parentList.splice(index, 1);
		sortDisable.value = true;
		await deptMoveDown({ dept_id: treeSelectDept.value.id });
		sortDisable.value = false;
	}
};

defineExpose({
	treeRef,
});
</script>
<style lang="scss">
</style>
