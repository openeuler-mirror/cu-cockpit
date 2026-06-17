import {AddReq, DelReq, EditReq, dict, CreateCrudOptionsRet, CreateCrudOptionsProps} from '@fast-crud/fast-crud';
import * as api from './api';
import {auth} from '/@/utils/authFunction'
import {request} from '/@/utils/service';
import { successNotification } from '/@/utils/message';
import { ElMessage } from 'element-plus';
import { nextTick, ref } from 'vue';
import XEUtils from 'xe-utils';
//此处为crudOptions配置

export const createCrudOptions = function ({crudExpose, context}: CreateCrudOptionsProps): CreateCrudOptionsRet {
    const pageRequest = async () => {
        if (context!.selectOptions.value.id) {
            return await api.GetList({menu: context!.selectOptions.value.id} as any);
        } else {
            return undefined;
        }
    };
    const editRequest = async ({form, row}: EditReq) => {
        return await api.UpdateObj({...form, menu: row.menu});
    };
    const delRequest = async ({row}: DelReq) => {
        return await api.DelObj(row.id);
    };
    const addRequest = async ({form}: AddReq) => {
        return await api.AddObj({...form, ...{menu: context!.selectOptions.value.id}});
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
            pagination:{
                show:false
            },
            search: {
                container: {
                    action: {
                        //按钮栏配置
                        col: {
                            span: 8,
                        },
                    },
                },
            },
            actionbar: {
                buttons: {
                    add: {
                        show: auth('menu:CreateButton')
                    },
                    batchAdd: {
						show: true,
						type: 'primary',
						text: '批量生成',
						click: async () => {
							if (context!.selectOptions.value.id == undefined) {
								ElMessage.error('请选择菜单');
								return;
							}
							const result = await api.BatchAdd({ menu: context!.selectOptions.value.id });
							if (result.code == 2000) {
								successNotification(result.msg);
								crudExpose.doRefresh();
							}
						},
					},
                },
            },
            rowHandle: {
                //固定右侧
                fixed: 'right',
                width: 200,
                buttons: {
                    view: {
                        show: false,
                    },
                    edit: {
                        icon: '',
                        type: 'primary',
                        show: auth('menu:UpdateButton')
                    },
                    remove: {
                        show: auth('menu:DeleteButton')
                    },
                },
            },
            columns: {
                $checked: {
					title: '选择',
					form: { show: false },
					column: {
						type: 'selection',
						align: 'center',
						width: '70px',
						columnSetDisabled: true, //禁止在列设置中选择
					},
				},
                _index: {
                    title: '序号',
                    form: {show: false},
                    column: {
                        type: 'index',
                        align: 'center',
                        width: '70px',
                        columnSetDisabled: true, //禁止在列设置中选择
                    },
                },
                search: {
                    title: '关键词',
                    column: {show: false},
                    type: 'text',
                    search: {show: true},
                    form: {
                        show: false,
                        component: {
                            placeholder: '输入关键词搜索',
                        },
                    },
                },
            },
        },
    };
};
