import { defineStore } from 'pinia';
import { RoleDrawerType } from '../types';
/**
 * 权限配置：抽屉
 */
const initialState: RoleDrawerType = {
	drawerVisible: false,
	roleId: undefined,
	roleName: undefined,
	users: [],
};
