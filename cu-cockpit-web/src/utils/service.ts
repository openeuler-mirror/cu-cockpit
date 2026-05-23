import axios from 'axios';
import { get } from 'lodash-es';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { Action } from 'element-plus';

// @ts-ignore
import { errorLog, errorCreate } from './tools.ts';
// import { env } from "/src/utils/util.env";
// import { useUserStore } from "../store/modules/user";
import { Local, Session } from '/@/utils/storage';
import qs from 'qs';
import { getBaseURL } from './baseUrl';
import { successMessage } from './message.js';
/**
 * @description 创建请求实例
 */
