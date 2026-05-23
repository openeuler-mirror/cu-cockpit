// aside
declare type AsideState = {
	menuList: RouteRecordRaw[];
	clientWidth: number;
};

// columnsAside
declare type ColumnsAsideState<T = any> = {
	columnsAsideList: T[];
	liIndex: number;
	liOldIndex: null | number;
	liHoverIndex: null | number;
	liOldPath: null | string;
	difference: number;
	routeSplit: string[];
};

// navBars breadcrumb
