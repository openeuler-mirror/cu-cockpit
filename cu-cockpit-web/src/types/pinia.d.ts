/**
 * pinia 类型定义
 */

// 用户信息
declare interface UserInfosState<T = any> {
	userInfos: {
		authBtnList: string[];
		photo: string;
		roles: string[];
		time: number;
		username: string;
		[key: string]: T;
	};
}

// 路由缓存列表
declare interface KeepAliveNamesState {
	keepAliveNames: string[];
	cachedViews: string[];
}

// 后端返回原始路由(未处理时)
