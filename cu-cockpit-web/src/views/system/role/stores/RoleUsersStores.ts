import { defineStore } from 'pinia';
import { RoleUsersType } from '../types';
import { getAllUsers } from '../components/api';
import XEUtils from 'xe-utils';
/**
 * 权限抽屉：角色-用户
 */
