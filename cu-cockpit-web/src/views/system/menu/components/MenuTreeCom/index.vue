<template>

	<el-input v-model="filterVal" :prefix-icon="Search" placeholder="请输入菜单名称" />
</template>
<script lang="ts" setup>

import { ref, toRaw, watch, h } from 'vue';
import { ElTree } from 'element-plus';
import { getElementLabelLine } from 'element-tree-line';
import { Search } from '@element-plus/icons-vue';
import SvgIcon from '/@/components/svgIcon/index.vue';
import { lazyLoadMenu, menuMoveUp, menuMoveDown } from '../../api';
import { warningNotification } from '/@/utils/message';
import { TreeTypes, MenuTreeItemType } from '../../types';
import type Node from 'element-plus/es/components/tree/src/model/node';

interface IProps {
	treeData: TreeTypes[];
}

const ElementTreeLine = getElementLabelLine(h);

const defaultTreeProps: any = {
	children: 'children',
	label: 'name',
	icon: 'icon',
	isLeaf: (data: TreeTypes[], node: Node) => {
		if (node.data.is_catalog) {
			return false;
		} else {
			return true;
		}
	},
};

const treeRef = ref<InstanceType<typeof ElTree>>();

withDefaults(defineProps<IProps>(), {
	treeData: () => [],
});
const emit = defineEmits(['treeClick', 'deleteDept', 'updateDept']);

let filterVal = ref('');
let sortDisable = ref(false);
let treeSelectMenu = ref<Partial<MenuTreeItemType>>({});
let treeSelectNode = ref<Node | null>(null);

watch(filterVal, (val) => {
	treeRef.value!.filter(val);
});

/**
 * 树的搜索事件
 */
const filterNode = (value: string, data: any) => {
	if (!value) return true;
	return toRaw(data).name.indexOf(value) !== -1;
};

/**
 * 树的懒加载
 */
const handleTreeLoad = (node: Node, resolve: Function) => {
	if (node.level !== 0) {
		lazyLoadMenu({ parent: node.data.id }).then((res: APIResponseData) => {
			resolve(res.data);
		});
	}
};

/**
 * 树的点击事件
 */
const handleNodeClick = (record: MenuTreeItemType, node: Node) => {
	treeSelectMenu.value = record;
	treeSelectNode.value = node;
	emit('treeClick', record);
};

/**
 * 点击左侧编辑按钮
 */
const handleUpdateMenu = (type: string) => {
	if (type === 'update') {
		if (!treeSelectMenu.value.id) {
			warningNotification('请选择菜单！');
			return;
		}
		emit('updateDept', type, treeSelectMenu.value);
	} else {
		emit('updateDept', type);
	}
};

/**
 * 删除菜单
 */
const handleDeleteMenu = () => {
	if (!treeSelectMenu.value.id) {
		warningNotification('请选择菜单！');
		return;
	}
	emit('deleteDept', treeSelectMenu.value.id, () => {
		treeSelectMenu.value = {};
	});
};

/**
 * 移动操作
 */
const handleSort = async (type: string) => {
	if (!treeSelectMenu.value.id) {
		warningNotification('请选择菜单！');
		return;
	}
	if (sortDisable.value) return;

	const parentList = treeSelectNode.value?.parent.childNodes || [];
	const index = parentList.findIndex((i) => i.data.id === treeSelectMenu.value.id);
	const record = parentList.find((i) => i.data.id === treeSelectMenu.value.id);

	if (type === 'up') {
		if (index === 0) return;
		parentList.splice(index - 1, 0, record as any);
		parentList.splice(index + 1, 1);
		sortDisable.value = true;
		await menuMoveUp({ menu_id: treeSelectMenu.value.id });
		sortDisable.value = false;
	}
	if (type === 'down') {
		parentList.splice(index + 2, 0, record as any);
		parentList.splice(index, 1);
		sortDisable.value = true;
		await menuMoveDown({ menu_id: treeSelectMenu.value.id });
		sortDisable.value = false;
	}
};

defineExpose({
	treeRef,
});
</script>
<style lang="scss">
</style>
