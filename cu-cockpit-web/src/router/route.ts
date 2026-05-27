import { RouteRecordRaw } from 'vue-router';

/**
 * 路由meta对象参数说明
 * meta: {
 *      title:          菜单栏及 tagsView 栏、菜单搜索名称（国际化）
 *      isLink：        是否超链接菜单，开启外链条件，`1、isLink: 链接地址不为空`
 *      isHide：        是否隐藏此路由
 *      isKeepAlive：   是否缓存组件状态
 *      isAffix：       是否固定在 tagsView 栏上
 *      isIframe：      是否内嵌窗口，开启条件，`1、isIframe:true 2、isLink：链接地址不为空`
 *      roles：         当前路由权限标识，取角色管理。控制路由显示、隐藏。超级管理员：admin 普通角色：common
 *      icon：          菜单、tagsView 图标，阿里：加 `iconfont xxx`，fontawesome：加 `fa xxx`
 * }
 */

/**
 * 定义动态路由
 * 前端添加路由，请在顶级节点的 `children 数组` 里添加
 * @description 未开启 isRequestRoutes 为 true 时使用（前端控制路由），开启时第一个顶级 children 的路由将被替换成接口请求回来的路由数据
 * @description 各字段请查看 `/@/views/system/menu/component/addMenu.vue 下的 ruleForm`
 * @returns 返回路由菜单数据
 */
export const dynamicRoutes: Array<RouteRecordRaw> = [
	{
		path: '/',
		name: '/',
		component: () => import('/@/layout/index.vue'),
		redirect: '/overview',
		meta: {
			isKeepAlive: false,
		},
		children: [
      {
        path: '/overview',
        component: () => import('/@/views/overview/indexPage.vue'),
        name: 'overview',
        meta: {
          title: 'message.router.overview',
          isLink: '',
          isHide: false,
          isKeepAlive: false,
          isAffix: true,
          isIframe: false,
          icon: 'iconfont icon-caidan',
        }
      },
      {
        path: '/storage',
        component: () => import('/@/views/storage/indexPage.vue'),
        name: 'storage',
        meta: {
          title: 'message.router.storage',
          isLink: '',
          isHide: false,
          isKeepAlive: false,
          isAffix: false,
          isIframe: false,
          icon: 'iconfont icon-cunchu',
        }
      },
      {
        path: '/storage/detail/:name',
        component: () => import('/@/views/storage/detailPage.vue'),
        name: 'storageDetail',
        meta: {
          title: 'message.router.storageDetail',
          isLink: '',
          isHide: true,
          isKeepAlive: false,
          isAffix: false,
          isIframe: false,
          icon: 'iconfont icon-cunchu',
        },
        props: true
      },
      {
        path: '/services',
        component: () => import('/@/views/services/indexPage.vue'),
        name: 'services',
        meta: {
          title: 'message.router.services',
          isLink: '',
          isHide: false,
          isKeepAlive: false,
          isAffix: false,
          isIframe: false,
          icon: 'iconfont icon-fuwuqi',
        }
      },
      {
        path: '/hardware',
        component: () => import('/@/views/hardware/indexPage.vue'),
        name: 'hardware',
        meta: {
          title: 'message.router.hardware',
          isLink: '',
          isHide: false,
          isKeepAlive: false,
          isAffix: false,
          isIframe: false,
          icon: 'iconfont icon-yingjianxinxi',
        }
      },
      {
        path: '/indicator',
        component: () => import('/@/views/indicator/indexPage.vue'),
        name: 'indicator',
        meta: {
          title: 'message.router.indicator',
          isLink: '',
          isHide: false,
          isKeepAlive: false,
          isAffix: false,
          isIframe: false,
          icon: 'iconfont icon-ico_shuju',
        }
      },
      {
        path: '/config',
        component: () => import('/@/views/config/indexPage.vue'),
        name: 'config',
        meta: {
          title: 'message.router.configHost',
          isLink: '',
          isHide: false,
          isKeepAlive: false,
          isAffix: false,
          isIframe: false,
          icon: 'iconfont icon-xitongshezhi',
        }
      },
      {
        path: '/log',
        component: () => import('/@/views/log/indexPage.vue'),
        name: 'logs',
        meta: {
          title: 'message.router.logs',
          isLink: '',
          isHide: false,
          isKeepAlive: true,
          isAffix: false,
          isIframe: false,
          icon: 'fa fa-file-text-o',
        }
      },
      {
        path: '/log/detail/',
        component: () => import('/@/views/log/detailPage.vue'),
        name: 'logsDetail',
        meta: {
          title: 'message.router.logsDetail',
          isLink: '',
          isHide: true,
          isKeepAlive: false,
          isAffix: false,
          isIframe: false,
          icon: 'fa fa-file-text-o',
        },
        props: true
      },
      {
        path: '/terminal',
        component: () => import('/@/views/terminal/indexPage.vue'),
        name: 'terminal',
        meta: {
          title: 'message.router.terminal',
          isLink: '',
          isHide: false,
          isKeepAlive: true,
          isAffix: false,
          isIframe: false,
          icon: 'iconfont icon-diannao2',
        }
      },
    ],
	}
];

/**
 * 定义404、401界面
 * @link 参考
 */
