import { judementSameArr } from '/@/utils/arrayOperation';
import {BtnPermissionStore} from "/@/stores/btnPermission";
/**
 * 单个权限验证
 * @param value 权限值
 * @returns 有权限，返回 `true`，反之则反
 */
export function auth(value: string): boolean {
	const stores = BtnPermissionStore();
	return stores.data.some((v: string) => v === value);
}
