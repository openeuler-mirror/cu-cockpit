/**角色列表数据类型 */
export interface RoleItemType {
	id: string | number;
	modifier_name: string;
	creator_name: string;
	create_datetime: string;
	update_datetime: string;
	description: string;
	modifier: string;
	dept_belong_id: string;
	name: string;
	key: string;
	sort: number;
	status: boolean;
	admin: boolean;
	creator: string;
}

export interface UsersType {
	id: string | number;
	name: string;
}
export interface RoleUsersType {
	all_users: UsersType[];
	right_users: UsersType[];
}

/**
 * 权限配置 抽屉组件参数数据类型
 */
export interface RoleDrawerType {
	/** 是否显示抽屉*/
	drawerVisible: boolean;
	/** 角色id*/
	roleId: string | number | undefined;
	/** 角色名称*/
	roleName: string | undefined;
	/** 用户*/
	users: UsersType[];
}
