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
