import { request } from '/@/utils/service';
import { UserPageQuery} from '@fast-crud/fast-crud';

/**
 * 当前角色查询未授权的用户
 * @param role_id 角色id
 * @param query 查询条件 需要有角色id
 * @returns
 */