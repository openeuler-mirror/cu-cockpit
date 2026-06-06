import { request } from '/@/utils/service';
import XEUtils from 'xe-utils';
/**
 * 获取 角色-菜单
 * @param query
 */
export function getRoleMenu(query: object) {
	return request({
		url: '/api/system/role_menu_button_permission/get_role_menu/',
		method: 'get',
		params: query,
	}).then((res: any) => {
		return XEUtils.toArrayTree(res.data, { key: 'id', parentKey: 'parent', children: 'children', strict: false });
	});
}
/**
 * 设置 角色-菜单
 * @param data
 * @returns
 */
export function setRoleMenu(data: object) {
	return request({
		url: '/api/system/role_menu_button_permission/set_role_menu/',
		method: 'put',
		data,
	});
}
