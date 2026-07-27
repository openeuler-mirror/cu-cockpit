// 用户权限 2025-0905
import { defineStore } from 'pinia';
import { Local } from '../utils/storage';
import { getSystemContext } from '/@/api/system';

export const userPermissiom = defineStore('userPermissiom', {
    state: () => ({
        u_Permission: 'other',
        serverRole: 'viewer',
        permissionLoaded: false,
    }),
    actions: {
        async refreshUserPermission() {
            const response = await getSystemContext();
            this.serverRole = response.identity.role;
            const forceRestricted = Local.get('forceRestricted') === true;
            this.u_Permission = response.identity.is_admin && !forceRestricted ? 'root' : 'other';
            this.permissionLoaded = true;
            Local.set('u_Permission', this.u_Permission);
            return this.u_Permission;
        },
        async setUserPermissionStore(_userName: unknown, value: string) {
            Local.set('forceRestricted', value !== 'root');
            return this.refreshUserPermission();
        },
        async getUserPermissionStore() {
            return this.refreshUserPermission();
        },
    },
    persist: {
        enabled: true,
    },
});
