import {createRouter, createWebHashHistory} from 'vue-router';
import NProgress from 'nprogress';
import 'nprogress/nprogress.css';
import pinia from '/@/stores/index';
import {storeToRefs} from 'pinia';
import {useKeepALiveNames} from '/@/stores/keepAliveNames';
import {useRoutesList} from '/@/stores/routesList';
import {useThemeConfig} from '/@/stores/themeConfig';
import {Session} from '/@/utils/storage';
import {dynamicRoutes, notFoundAndNoPower, staticRoutes} from '/@/router/route';
import {initFrontEndControlRoutes} from '/@/router/frontEnd';
import {initBackEndControlRoutes, setRouters} from '/@/router/backEnd';
import {useFrontendMenuStore} from "/@/stores/frontendMenu";
import {useTagsViewRoutes} from "/@/stores/tagsViewRoutes";
import {toRaw} from "vue";
import {checkVersion} from "/@/utils/upgrade";

/**
 * 1、前端控制路由时：isRequestRoutes 为 false，需要写 roles，需要走 setFilterRoute 方法。
 * 2、后端控制路由时：isRequestRoutes 为 true，不需要写 roles，不需要走 setFilterRoute 方法），
 * 相关方法已拆解到对应的 `backEnd.ts` 与 `frontEnd.ts`（他们互不影响，不需要同时改 2 个文件）。
 * 特别说明：
 * 1、前端控制：路由菜单由前端去写（无菜单管理界面，有角色管理界面），角色管理中有 roles 属性，需返回到 userInfo 中。
 * 2、后端控制：路由菜单由后端返回（有菜单管理界面、有角色管理界面）
 */

// 读取 `/src/stores/themeConfig.ts` 是否开启后端控制路由配置
const storesThemeConfig = useThemeConfig(pinia);
