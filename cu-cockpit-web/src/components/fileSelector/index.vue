<template #footer v-if="props.showInput">

        <el-button type="default" @click="onClose">取消</el-button>
        <el-button type="primary" @click="onSave">确定</el-button>
      
</template>
<script setup lang="ts">
import { useUi, UserPageQuery, AddReq, EditReq, DelReq } from '@fast-crud/fast-crud';
import { ref, reactive, defineProps, PropType, watch, onMounted, nextTick } from 'vue';
import { getBaseURL } from '/@/utils/baseUrl';
import { request } from '/@/utils/service';
import { SHOW } from './types';
import FileItem from './fileItem.vue';
import { pluginsAll } from '/@/views/plugins/index';
import { storeToRefs } from "pinia";
import { useUserInfo } from "/@/stores/userInfo";
import { errorNotification, successNotification } from '/@/utils/message';
</script>
<style scoped>
</style>