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

	const onSelectionChange = (changed: any) => {
		const tableData = crudExpose.getTableData();
		const unChanged = tableData.filter((row: any) => !changed.includes(row));
		// 添加已选择的行
		XEUtils.arrayEach(changed, (item: any) => {
			const ids = XEUtils.pluck(selectedRows.value, 'id');
			if (!ids.includes(item.id)) {
				selectedRows.value = XEUtils.union(selectedRows.value, [item]);
			}
		});
		// 剔除未选择的行
		XEUtils.arrayEach(unChanged, (unItem: any) => {
			selectedRows.value = XEUtils.remove(selectedRows.value, (item: any) => item.id !== unItem.id);
		});
	};
	const toggleRowSelection = () => {
		// 多选后，回显默认勾选
		const tableRef = crudExpose.getBaseTableRef();
		const tableData = crudExpose.getTableData();
		const selected = XEUtils.filter(tableData, (item: any) => {
			const ids = XEUtils.pluck(selectedRows.value, 'id');
			return ids.includes(item.id);
		});

		nextTick(() => {
			XEUtils.arrayEach(selected, (item) => {
				tableRef.toggleRowSelection(item, true);
			});
		});
	};
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
