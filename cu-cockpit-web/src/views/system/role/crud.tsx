import { CreateCrudOptionsProps, CreateCrudOptionsRet, AddReq, DelReq, EditReq, dict, compute } from '@fast-crud/fast-crud';
import * as api from './api';
import { dictionary } from '/@/utils/dictionary';
import { successMessage } from '../../../utils/message';
import { auth } from '/@/utils/authFunction';
import { nextTick, computed } from 'vue';

/**
 *
 * @param crudExpose：index传递过来的示例
 * @param context：index传递过来的自定义参数
 * @returns
 */

export const createCrudOptions = function ({ crudExpose, context }: CreateCrudOptionsProps): CreateCrudOptionsRet {
	const pageRequest = async (query: any) => {
		return await api.GetList(query);
	};
    return {
        crudOptions: {
        },
    };
};
