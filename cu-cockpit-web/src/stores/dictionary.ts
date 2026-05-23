import { defineStore } from 'pinia';
import { DictionaryStates } from './interface';
import { request } from '../utils/service';

export const urlPrefix = '/api/init/dictionary/';
export const BUTTON_VALUE_TO_COLOR_MAPPING: any = {
	1: 'success',
	true: 'success',
	0: 'danger',
	false: 'danger',
	Search: 'warning', // 查询
	Update: 'primary', // 编辑
	Create: 'success', // 新增
	Retrieve: 'info', // 单例
	Delete: 'danger', // 删除
};
