<template #footer>

			<span class="dialog-footer">
				<el-button @click="handleResetPwdClose">取消</el-button>
				<el-button type="primary" @click="handleResetPwdSubmit"> 保存 </el-button>
			</span>
		
</template>
<script lang="ts" setup name="user">
import { ref, reactive, onMounted } from 'vue';
import { useExpose, useCrud } from '@fast-crud/fast-crud';
import { Md5 } from 'ts-md5';
import { createCrudOptions } from './crud';
import importExcel from '/@/components/importExcel/index.vue';
import * as echarts from 'echarts';
import { ECharts, EChartsOption, init } from 'echarts';
import { getDeptInfoById, resetPwd } from './api';
import { warningNotification, successNotification } from '/@/utils/message';
import { HeadDeptInfoType } from '../../types';
import {getBaseURL} from '/@/utils/baseUrl';
</script>
<style lang="scss" scoped>
</style>
