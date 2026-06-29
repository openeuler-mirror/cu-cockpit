import * as api from './api';
import {
    dict,
    UserPageQuery,
    AddReq,
    DelReq,
    EditReq,
    compute,
    CreateCrudOptionsProps,
    CreateCrudOptionsRet
} from '@fast-crud/fast-crud';
import { request } from '/@/utils/service';
import { dictionary } from '/@/utils/dictionary';
import { successMessage } from '/@/utils/message';
import { auth } from '/@/utils/authFunction';
import { SystemConfigStore } from "/@/stores/systemConfig";
import { storeToRefs } from "pinia";
import { computed } from "vue";
import { Md5 } from 'ts-md5';
import { commonCrudConfig } from "/@/utils/commonCrud";
import { ElMessageBox } from 'element-plus';
import { exportData } from "./api";

export const createCrudOptions = function ({ crudExpose }: CreateCrudOptionsProps): CreateCrudOptionsRet {
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
        return await api.AddObj(form);
    };
    const exportRequest = async (query: UserPageQuery) => {
        return await api.exportData(query)
    }
    return {
        crudOptions: {
            table: {
                remove: {
                    confirmMessage: '是否删除该用户？',
                },
            },
            request: {
                pageRequest,
                addRequest,
                editRequest,
                delRequest,
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
                username: {
                    title: '账号',
                    search: {
                        show: true,
                    },
                    type: 'input',
                    column: {
                        minWidth: 100, //最小列宽
                    },
                    form: {
                        rules: [
                            // 表单校验规则
                            {
                                required: true,
                                message: '账号必填项',
                            },
                        ],
                        component: {
                            placeholder: '请输入账号',
                        },
                    },
                },
                password: {
                    title: '密码',
                    type: 'password',
                    column: {
                        show: false,
                    },
                    editForm: {
                        show: false,
                    },
                    form: {
                        rules: [
                            // 表单校验规则
                            {
                                required: true,
                                message: '密码必填项',
                            },
                        ],
                        component: {

                            span: 12,
                            showPassword: true,
                            placeholder: '请输入密码',
                        },
                    },
                    valueResolve({ form }) {
                        if (form.password) {
                            form.password = Md5.hashStr(form.password)
                        }
                    }
                },
            },
        },
    };
};
