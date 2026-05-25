// 用户权限 2025-0905
import { defineStore } from 'pinia';
import { Local } from '../utils/storage';

export const userPermissiom = defineStore('userPermissiom', {
    state: () => ({
        u_Permission:'other'
    }),
    actions: {
        async setUserPermissionStore(userName:any,val:string) {
            // let tmp = JSON.parse(Local.get('pList')) ||{};
            // tmp[userName]=val;
            // Local.set('pList',JSON.stringify(tmp));
            this.u_Permission=val;
        },
        async getUserPermissionStore(val:string){
            //账号是root 默认是root
            if(val == 'root'){
                this.u_Permission='root';
                Local.set('u_Permission','root');
            }else{
                let tmp = JSON.parse(Local.get('pList')) || {};
                Local.set('u_Permission','ohter');
                // if(tmp[val]){
                //     this.u_Permission=tmp[val];
                //     Local.set('u_Permission',tmp[val]);
                // }else{
                //     this.u_Permission='other'
                //     tmp[val]='other',
                //     Local.set('pList',JSON.stringify(tmp));
                //     Local.set('u_Permission','other');
                // }
            }
        }
    },
    persist: {
        enabled: true,
    },
});
