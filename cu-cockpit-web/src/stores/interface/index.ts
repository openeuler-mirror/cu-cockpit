/**
 * 定义接口来定义对象的类型
 * `stores` 全部类型定义在这里
 */
import { useFrontendMenuStore } from "/@/stores/frontendMenu";

// 用户信息
export interface UserInfosState {
	id: '',
	avatar: string;
	is_superuser: boolean,
	username: string;
	name: string;
	email: string;
	mobile: string;
	gender: string;
	pwd_change_count: null | number;
	dept_info: {
		dept_id: number;
		dept_name: string;
	};
	role_info: any[];
}
export interface UserInfosStates {
	userInfos: UserInfosState;
}

// 路由缓存列表
export interface KeepAliveNamesState {
	keepAliveNames: string[];
	cachedViews: string[];
}

// 后端返回原始路由(未处理时)
export interface RequestOldRoutesState {
	requestOldRoutes: string[];
}

// TagsView 路由列表
export interface TagsViewRoutesState {
	tagsViewRoutes: string[];
	isTagsViewCurrenFull: Boolean;
}

// 路由列表
export interface RoutesListState {
	routesList: string[];
	isColumnsMenuHover: Boolean;
	isColumnsNavHover: Boolean;
}
