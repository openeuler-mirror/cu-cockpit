import * as api from './api';
import {
  UserPageQuery,
  AddReq,
  DelReq,
  EditReq,
  CrudExpose,
  CrudOptions,
  CreateCrudOptionsProps,
  CreateCrudOptionsRet,
  dict
} from '@fast-crud/fast-crud';
import fileSelector from '/@/components/fileSelector/index.vue';
import { getBaseURL } from '/@/utils/baseUrl';


export const createCrudOptions = function ({ crudExpose, context }: CreateCrudOptionsProps): CreateCrudOptionsRet {
  const pageRequest = async (query: UserPageQuery) => {
    return await api.GetList(query);
  };
    return {
        crudOptions: {
        },
    };
};
