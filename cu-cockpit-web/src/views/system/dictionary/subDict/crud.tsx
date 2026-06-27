import * as api from './api';
import {
  dict,
  UserPageQuery,
  AddReq,
  DelReq,
  EditReq,
  CrudOptions,
  CreateCrudOptionsProps,
  CreateCrudOptionsRet
} from '@fast-crud/fast-crud';
import { dictionary } from '/@/utils/dictionary';


export const createCrudOptions = function ({ crudExpose, context }: CreateCrudOptionsProps): CreateCrudOptionsRet {
  const pageRequest = async (query: UserPageQuery) => {
    return await api.GetList(query);
  };
  const editRequest = async ({ form, row }: EditReq) => {
    form.id = row.id;
    return await api.UpdateObj(form);
  };
  const delRequest = async ({ row }: DelReq) => {
    return await api.DelObj(row.id);
  };
  const addRequest = async ({ form }: AddReq) => {
    const data = crudExpose!.getSearchFormData()
    const parent = data.parent
    form.parent = parent
    if (parent) {
      return await api.AddObj(form);
    } else {
      return undefined
    }

  };
    return {
        crudOptions: {
            component: {
              props: {
                clearable: true,
              },
            },
            component: {
              props: {
                clearable: true,
              },
              placeholder: '请输入名称',
            },
            component: {
              props: {
                clearable: true,
              },
            },
            component: {
              props: {
                clearable: true,
              },
              placeholder: '请选择数据值类型',
            },
        },
    };
};
