import * as api from './api';
import { dict, useCompute, PageQuery, AddReq, DelReq, EditReq, CreateCrudOptionsProps, CreateCrudOptionsRet } from '@fast-crud/fast-crud';
import tableSelector from '/@/components/tableSelector/index.vue';
import { shallowRef, computed } from 'vue';
import manyToMany from '/@/components/manyToMany/index.vue';
import { auth } from '/@/utils/authFunction';
