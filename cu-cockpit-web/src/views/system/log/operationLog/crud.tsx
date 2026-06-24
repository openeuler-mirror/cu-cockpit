import * as api from './api';
import { UserPageQuery, AddReq, DelReq, EditReq, CrudExpose, CrudOptions, CreateCrudOptionsProps, CreateCrudOptionsRet } from '@fast-crud/fast-crud';


export const createCrudOptions = function ({ crudExpose }: CreateCrudOptionsProps): CreateCrudOptionsRet {
	const pageRequest = async (query: UserPageQuery) => {
		return await api.GetList(query);
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
