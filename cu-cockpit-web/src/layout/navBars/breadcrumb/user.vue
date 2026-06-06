<template #dropdown>

				<el-dropdown-menu>
					<!-- <el-dropdown-item command="/home">{{ $t('message.user.dropdown1') }}</el-dropdown-item>
					<el-dropdown-item command="/personal">{{ $t('message.user.dropdown2') }}</el-dropdown-item>
					<el-dropdown-item command="/versionUpgradeLog">更新日志</el-dropdown-item>
					<el-dropdown-item divided command="logOut">{{ $t('message.user.dropdown5') }}</el-dropdown-item> -->
					<el-dropdown-item command="logOut">{{ $t('message.user.dropdown5') }}</el-dropdown-item>
				</el-dropdown-menu>
			
</template>
<script setup lang="ts" name="layoutBreadcrumbUser">
import { defineAsyncComponent, ref, computed, reactive, onMounted, unref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessageBox, ElMessage } from 'element-plus';
import screenfull from 'screenfull';
import { useI18n } from 'vue-i18n';
import { storeToRefs } from 'pinia';
import { useUserInfo } from '/@/stores/userInfo';
import { userPermissiom } from '/@/stores/userPermissiom';
import { useThemeConfig } from '/@/stores/themeConfig';
import other from '/@/utils/other';
import mittBus from '/@/utils/mitt';
import { Session, Local } from '/@/utils/storage';
import headerImage from '/@/assets/img/headerImage.png';
import { InfoFilled } from '@element-plus/icons-vue';
import { signOut } from '/@/api/login/index'
import { messageCenterStore } from '/@/stores/messageCenter';
import { getBaseURL } from '/@/utils/baseUrl';
</script>
<style scoped lang="scss">
</style>
