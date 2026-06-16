import * as api from './api';
import { dict, UserPageQuery, AddReq, DelReq, EditReq, compute, CreateCrudOptionsProps, CreateCrudOptionsRet } from '@fast-crud/fast-crud';
import { request } from '/@/utils/service';
import { dictionary } from '/@/utils/dictionary';
import { inject, nextTick, ref } from 'vue';
import {auth} from "/@/utils/authFunction";
import XEUtils from 'xe-utils';




export const createCrudOptions = function ({ crudExpose, props,modelDialog,selectOptions,allModelData }: CreateCrudOptionsProps): CreateCrudOptionsRet {
	const pageRequest = async (query: UserPageQuery) => {
		// return await api.GetList(query);
		if (selectOptions.value.id) {
			return await api.GetList({ menu: selectOptions.value.id } as any);
		} else {
			return undefined;
		}
	};
	const editRequest = async ({ form, row }: EditReq) => {
		form.id = row.id;
		return await api.UpdateObj(form);
	};
	const delRequest = async ({ row }: DelReq) => {
		return await api.DelObj(row.id);
	};
	const addRequest = async ({ form }: AddReq) => {
		form.menu = selectOptions.value.id;
		return await api.AddObj(form);
	};
    return {
        crudOptions: {
        },
    };
};
