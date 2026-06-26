import { CrudOptions, AddReq, DelReq, EditReq, dict, CrudExpose, compute } from '@fast-crud/fast-crud';
import * as api from './api';
import { dictionary } from '/@/utils/dictionary';
import { successMessage } from '../../../utils/message';
import { auth } from '/@/utils/authFunction';
import { getBaseURL } from '/@/utils/baseUrl';


export const createCrudOptions = function ({ crudExpose }: { crudExpose: CrudExpose; }): CreateCrudOptionsTypes {
    const pageRequest = async (query: any) => {
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
        return await api.AddObj(form);
    };
    return {
        crudOptions: {
            request: {
                pageRequest,
                addRequest,
                editRequest,
                delRequest,
            },
            pagination: {
                show: true
            },
            actionbar: {
                buttons: {
                    add: {
                        show: false
                    }
                }
            },
            columns: {
                _index: {
                    title: '序号',
                    form: { show: false },
                    column: {
                        type: 'index',
                        align: 'center',
                        width: '70px',
                        columnSetDisabled: true, //禁止在列设置中选择
                    },
                },
                task_name: {
                    title: '任务名',
                    type: 'text',
                    column: {
                        minWidth: 160,
                        align: 'left'
                    },
                    search: {
                        show: true
                    }
                },
            },
        },
    };
};
