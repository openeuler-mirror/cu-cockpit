import { defineStore } from 'pinia';

/**
 * 路由缓存列表
 * @methods setCacheKeepAlive 设置要缓存的路由 names（开启 Tagsview）
 * @methods addCachedView 添加要缓存的路由 names（关闭 Tagsview）
 * @methods delCachedView 删除要缓存的路由 names（关闭 Tagsview）
 * @methods delOthersCachedViews 右键菜单`关闭其它`，删除要缓存的路由 names（关闭 Tagsview）
 * @methods delAllCachedViews 右键菜单`全部关闭`，删除要缓存的路由 names（关闭 Tagsview）
 */
