import { CrudOptions, AddReq, DelReq, EditReq, dict, CrudExpose, UserPageQuery, CreateCrudOptionsRet } from '@fast-crud/fast-crud';
import _ from 'lodash-es';
import * as api from './api';
import { request } from '/@/utils/service';
import { auth } from "/@/utils/authFunction";

//此处为crudOptions配置