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
</script>
<style lang="scss">
</style>
