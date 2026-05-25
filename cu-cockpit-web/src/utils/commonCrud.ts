import {dict} from '@fast-crud/fast-crud';
import {shallowRef} from 'vue';
import deptFormat from '/@/components/dept-format/index.vue';

/** 1. 每个字段可选属性 */
export interface CrudFieldOption {
	form?: boolean;
	table?: boolean;
	search?: boolean;
	width?: number;
}

/** 2. 总配置接口 */
export interface CrudOptions {
	create_datetime?: CrudFieldOption;
	update_datetime?: CrudFieldOption;
	creator_name?: CrudFieldOption;
	modifier_name?: CrudFieldOption;
	dept_belong_id?: CrudFieldOption;
	description?: CrudFieldOption;
}
