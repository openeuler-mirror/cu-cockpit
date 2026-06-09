import { inject } from 'vue';
import { dict, UserPageQuery, AddReq, DelReq, EditReq, compute, CreateCrudOptionsProps, CreateCrudOptionsRet } from '@fast-crud/fast-crud';
import { request } from '/@/utils/service';
import * as api from './api';
import { dictionary } from '/@/utils/dictionary';
import { successMessage } from '/@/utils/message';
import { auth } from "/@/utils/authFunction";


export const createCrudOptions = function ({ crudExpose, context }: CreateCrudOptionsProps): CreateCrudOptionsRet {
	const pageRequest = async (query: UserPageQuery) => {
		const show_all = context?.isShowChildFlag.value ? '1' : '0';
		const res = await api.GetList({ ...query, show_all });
		/**
		 * 处理crud警告：Invalid prop: type check failed for prop "name". Expected String with value "2", got Number with value 2.
		 */
		// res.data.forEach((item: any) => {
		// 	item.dept = String(item.dept);
		// 	if (item.role && Array.isArray(item.role) && item.role.length > 0) {
		// 		item.role = item.role.map((r: number) => String(r));
		// 	}
		// });
		return res;
	};
	const editRequest = async ({ form, row }: EditReq) => {
		form.id = row.id;
		return await api.UpdateObj(form);
	};
    return {
        crudOptions: {
        },
    };
};
