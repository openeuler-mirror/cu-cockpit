<template #default>

						<div class="tool-box">
							<el-tooltip content="拖动进行排序" placement="top-start">
								<SvgIcon name="fa fa-question-circle-o" :size="17" class="ml11" color="#909399" />
							</el-tooltip>
							<el-checkbox
								v-model="state.checkListAll"
								:indeterminate="state.checkListIndeterminate"
								class="ml10 mr1"
								label="列显示"
								@change="onCheckAllChange"
							/>
							<el-checkbox v-model="getConfig.isSerialNo" class="ml12 mr1" label="序号" />
							<el-checkbox v-model="getConfig.isSelection" class="ml12 mr1" label="多选" />
						</div>
						<el-scrollbar>
							<div ref="toolSetRef" class="tool-sortable">
								<div class="tool-sortable-item" v-for="v in header" :key="v.key" :data-key="v.key">
									<i class="fa fa-arrows-alt handle cursor-pointer"></i>
									<el-checkbox v-model="v.isCheck" size="default" class="ml12 mr8" :label="v.title" @change="onCheckChange" />
								</div>
							</div>
						</el-scrollbar>
					
</template>
<script setup lang="ts" name="netxTable">
import { reactive, computed, nextTick, ref } from 'vue';
import { ElMessage } from 'element-plus';
import table2excel from 'js-table2excel';
import Sortable from 'sortablejs';
import { storeToRefs } from 'pinia';
import { useThemeConfig } from '/@/stores/themeConfig';
import '/@/theme/tableTool.scss';
</script>
<style scoped lang="scss">
</style>
