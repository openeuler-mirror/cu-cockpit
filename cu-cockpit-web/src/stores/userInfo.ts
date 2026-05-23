import { defineStore } from 'pinia';
import { UserInfosStates } from './interface';
import { Session } from '/@/utils/storage';
import { request } from '../utils/service';
import { getBaseURL } from '../utils/baseUrl';
import headerImage from '/@/assets/img/headerImage.png';

/**
 * 用户信息
 * @methods setUserInfos 设置用户信息
 */
