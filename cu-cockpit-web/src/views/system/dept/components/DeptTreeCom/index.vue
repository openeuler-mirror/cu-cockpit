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
</script>
<style lang="scss">
</style>
