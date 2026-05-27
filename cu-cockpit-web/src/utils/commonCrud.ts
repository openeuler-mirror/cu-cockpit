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

/** 3. 默认完整配置 */
const defaultOptions: Required<CrudOptions> = {
	create_datetime: { form: false, table: false, search: false, width: 160 },
	update_datetime: { form: false, table: false, search: false, width: 160 },
	creator_name: { form: false, table: false, search: false, width: 100 },
	modifier_name: { form: false, table: false, search: false, width: 100 },
	dept_belong_id: { form: false, table: false, search: false, width: 300 },
	description: { form: false, table: false, search: false, width: 100 },
};

/** 4. mergeOptions 函数 */
function mergeOptions(baseOptions: Required<CrudOptions>, userOptions: CrudOptions = {}): Required<CrudOptions> {
	const result = { ...baseOptions };
	for (const key in userOptions) {
		if (Object.prototype.hasOwnProperty.call(userOptions, key)) {
			const baseField = result[key as keyof CrudOptions];
			const userField = userOptions[key as keyof CrudOptions];
			if (baseField && userField) {
				result[key as keyof CrudOptions] = { ...baseField, ...userField };
			}
		}
	}
	return result;
}
