import { nextTick, defineAsyncComponent } from 'vue';
import type { App } from 'vue';
import * as svg from '@element-plus/icons-vue';
import router from '/@/router/index';
import pinia from '/@/stores/index';
import { storeToRefs } from 'pinia';
import { useThemeConfig } from '/@/stores/themeConfig';
import { i18n } from '/@/i18n/index';
import { Local } from '/@/utils/storage';
import { verifyUrl } from '/@/utils/toolsValidate';
import {SystemConfigStore} from "/@/stores/systemConfig";

// 引入组件
const SvgIcon = defineAsyncComponent(() => import('/@/components/svgIcon/index.vue'));

/**
 * 导出全局注册 element plus svg 图标
 * @param app vue 实例
 * @description 使用
 */
export function elSvg(app: App) {
	const icons = svg as any;
	for (const i in icons) {
		app.component(`ele-${icons[i].name}`, icons[i]);
	}
	app.component('SvgIcon', SvgIcon);
}

/**
 * 设置浏览器标题国际化
 * @method const title = useTitle(); ==> title()
 */
export function useTitle() {
	const stores = SystemConfigStore(pinia);
	const { systemConfig }: { systemConfig: any} = storeToRefs(stores);
	nextTick(() => {
		let webTitle = '';
		let globalTitle: string = systemConfig['base.web_title'];
		const { path, meta } = router.currentRoute.value;
		if (path === '/login') {
			webTitle = <string>meta.title;
		} else {
			webTitle = setTagsViewNameI18n(router.currentRoute.value);
		}
		document.title = `${webTitle}`;
	});
}

/***
 * 设置网站favicon图标
 */
export function useFavicon() {
	const stores = SystemConfigStore(pinia);
	const { systemConfig } = storeToRefs(stores);
	nextTick(() => {
		const iconUrl = systemConfig.value['base.web_favicon']
		if(iconUrl){
			// 动态设置 favicon，这里假设 favicon 的 URL 是动态获取的或从变量中来
			const faviconUrl = `${iconUrl}?t=${new Date().getTime()}`;
			const link = document.querySelector("link[rel~='icon']") as HTMLLinkElement;
			if (!link) {
				const newLink = document.createElement('link') as HTMLLinkElement;
				newLink.rel = 'shortcut icon';
				newLink.href = faviconUrl;
				document.head.appendChild(newLink);
			} else {
				link.href = faviconUrl;
			}
		}

	});
}

/**
 * 设置 自定义 tagsView 名称、 自定义 tagsView 名称国际化
 * @param params 路由 query、params 中的 tagsViewName
 * @returns 返回当前 tagsViewName 名称
 */
export function setTagsViewNameI18n(item: any) {
	let tagsViewName: string = '';
	const { query, params, meta } = item;
	if (query?.tagsViewName || params?.tagsViewName) {
		if (/\/zh-cn|en|zh-tw\//.test(query?.tagsViewName) || /\/zh-cn|en|zh-tw\//.test(params?.tagsViewName)) {
			// 国际化
			const urlTagsParams = (query?.tagsViewName && JSON.parse(query?.tagsViewName)) || (params?.tagsViewName && JSON.parse(params?.tagsViewName));
			tagsViewName = urlTagsParams[i18n.global.locale.value];
		} else {
			// 非国际化
			tagsViewName = query?.tagsViewName || params?.tagsViewName;
		}
	} else {
		// 非自定义 tagsView 名称
		tagsViewName = i18n.global.t(meta.title);
	}
	return tagsViewName;
}
