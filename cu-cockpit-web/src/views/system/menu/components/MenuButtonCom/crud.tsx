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
            },
        },
    };
};
