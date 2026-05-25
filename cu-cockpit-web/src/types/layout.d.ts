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
declare type BreadcrumbState<T = any> = {
	breadcrumbList: T[];
	routeSplit: string[];
	routeSplitFirst: string;
	routeSplitIndex: number;
};

// navBars search
declare type SearchState<T = any> = {
	isShowSearch: boolean;
	menuQuery: string;
	tagsViewList: T[];
};

// navBars tagsView
