<template #reference>

              <el-button size="mini" type="danger" :icon="Delete" ></el-button>
</template>
<script setup lang="ts">
import * as api from '../api';
import { dictionary } from '/@/utils/dictionary';
import { getBaseURL } from '/@/utils/baseUrl';
import { ref, reactive, watch, nextTick,inject  } from 'vue';
import type { FormInstance, FormRules, TableInstance } from 'element-plus';
import { successMessage, errorMessage } from '/@/utils/message';
import { Session } from '/@/utils/storage';
import {Edit,Finished,Delete} from "@element-plus/icons-vue";
import crudTable from "./components/crudTable.vue"
</script>
<style scoped>
</style>
