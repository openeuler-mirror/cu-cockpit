import {getRoleUsersAuthorized, removeRoleUser} from './api';
import {
  compute,
  dict,
  UserPageQuery,
  AddReq,
  DelReq,
  EditReq,
  CrudOptions,
  CreateCrudOptionsProps,
  CreateCrudOptionsRet
} from '@fast-crud/fast-crud';

import {auth} from "/@/utils/authFunction";
import { ref , nextTick} from 'vue';
import XEUtils from 'xe-utils';


export const createCrudOptions = function ({ crudExpose, context }: CreateCrudOptionsProps): CreateCrudOptionsRet {
  const pageRequest = async (query: UserPageQuery) => {
    return await getRoleUsersAuthorized(query);
  };
  const editRequest = async ({ form, row }: EditReq) => {
    return undefined;
  };
  const delRequest = async ({ row }: DelReq) => {
    return await removeRoleUser(crudExpose.crudRef.value.getSearchFormData().role_id, [row.id]);
  };
  const addRequest = async ({ form }: AddReq) => {
    return undefined;
  };
	const selectedRows = ref<any>([]);

    return {
        selectedRows,
        crudOptions: {
            component: {
              props: {
                clearable: true,
              },
            },
        },
    };
};
