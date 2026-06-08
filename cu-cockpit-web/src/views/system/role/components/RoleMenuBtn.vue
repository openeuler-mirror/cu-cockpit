<template>

</template>
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { RoleDrawerStores } from '../stores/RoleDrawerStores';
import { RoleMenuBtnStores } from '../stores/RoleMenuBtnStores';
import { RoleMenuTreeStores } from '../stores/RoleMenuTreeStores';
import { RoleMenuBtnType } from '../types';
import { getRoleToDeptAll, setRoleMenuBtn, setRoleMenuBtnDataRange } from './api';
import XEUtils from 'xe-utils';
import { ElMessage } from 'element-plus';
import { Local } from '/@/utils/storage';
</script>
<style lang="scss" scoped>
</style>
