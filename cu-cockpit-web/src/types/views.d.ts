/**
 * views personal
 */
type NewInfo = {
	title: string;
	date: string;
	link: string;
};
type Recommend = {
	title: string;
	msg: string;
	icon: string;
	bg: string;
	iconColor: string;
};
declare type PersonalState = {
	newsInfoList: NewInfo[];
	personalForm: {
		avatar:string,
		username: string;
		name: string;
		email: string;
		mobile: string;
		gender: number | string;
		dept_info: {
			dept_id: number;
			dept_name: string;
		}
		role_info: [{
			id: number;
			name: string;
		}]
	};
};

/**
 * views visualizing
 */
declare type Demo2State<T = any> = {
	time: {
		txt: string;
		fun: number;
	};
	dropdownList: T[];
	dropdownActive: string;
	skyList: T[];
	dBtnList: T[];
	chartData4Index: number;
	dBtnActive: number;
	earth3DBtnList: T[];
	chartData4List: T[];
	myCharts: T[];
};

/**
 * views params
 */
declare type ParamsState = {
	value: string;
	tagsViewName: string;
	tagsViewNameIsI18n: boolean;
};

/**
 * views system
 */
// role
declare interface RowRoleType {
	roleName: string;
	roleSign: string;
	describe: string;
	sort: number;
	status: boolean;
	createTime: string;
}

interface SysRoleTableType extends TableType {
	data: RowRoleType[];
}

declare interface SysRoleState {
	tableData: SysRoleTableType;
}

declare type TreeType = {
	id: number;
	label: string;
	children?: TreeType[];
};

// user
declare type RowUserType<T = any> = {
	username: string;
	userNickname: string;
	roleSign: string;
	department: string[];
	phone: string;
	email: string;
	sex: string;
	password: string;
	overdueTime: T;
	status: boolean;
	describe: string;
	createTime: T;
};

interface SysUserTableType extends TableType {
	data: RowUserType[];
}

declare interface SysUserState {
	tableData: SysUserTableType;
}

declare type DeptTreeType = {
	deptName: string;
	createTime: string;
	status: boolean;
	sort: number;
	describe: string;
	id: number | string;
	children?: DeptTreeType[];
};

// dept
declare interface RowDeptType extends DeptTreeType {
	deptLevel: string[];
	person: string;
	phone: string;
	email: string;
}

interface SysDeptTableType extends TableType {
	data: DeptTreeType[];
}

declare interface SysDeptState {
	tableData: SysDeptTableType;
}

// dic
type ListType = {
	id: number;
	label: string;
	value: string;
};
