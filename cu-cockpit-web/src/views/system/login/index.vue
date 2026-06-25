<template>

	<div class="login-container flex z-10">
		<div class="login-left">
			<div class="login-left-logo">
				<img :src="siteLogo" />
				<div class="login-left-logo-text">
					<span>{{ getSystemConfig['login.site_title'] || getThemeConfig.globalViceTitle }}</span>
					<span class="login-left-logo-text-msg" style="margin-top: 5px;">{{
						getSystemConfig['login.site_name'] || getThemeConfig.globalViceTitleMsg }}</span>
				</div>
			</div>
		</div>
		<div class="login-right flex z-10">
			<div class="login-right-warp flex-margin">
<!--				<span class="login-right-warp-one"></span>-->
<!--				<span class="login-right-warp-two"></span>-->
				<div class="login-right-warp-mian">
					<div class="login-right-warp-main-title">
            {{userInfos.pwd_change_count===0?'初次登录修改密码':'欢迎登录'}}
          </div>
					<div class="login-right-warp-main-form">
						<div v-if="!state.isScan">
							<el-tabs v-model="state.tabsActiveName">
                <el-tab-pane :label="$t('message.label.changePwd')" name="changePwd"  v-if="userInfos.pwd_change_count===0">
                  <ChangePwd />
                </el-tab-pane>
								<el-tab-pane :label="$t('message.label.one1')" name="account" v-else>
									<Account />
								</el-tab-pane>

								<!-- TODO 手机号码登录未接入，展示隐藏 -->
								<!-- <el-tab-pane :label="$t('message.label.two2')" name="mobile">
									<Mobile />
								</el-tab-pane> -->
							</el-tabs>
						</div>
            <OAuth2 />

            <!--						<Scan v-if="state.isScan" />-->
<!--						<div class="login-content-main-sacn" @click="state.isScan = !state.isScan">-->
<!--							<i class="iconfont" :class="state.isScan ? 'icon-diannao1' : 'icon-barcode-qr'"></i>-->
<!--							<div class="login-content-main-sacn-delta"></div>-->
<!--						</div>-->
					</div>
				</div>
			</div>
		</div>

		<div class="login-authorization z-10">
			 
		</div>
	</div>
	<div v-if="loginBg">
		<img :src="loginBg" class="loginBg fixed inset-0 z-1 w-full h-full" />
	</div>
</template>
<script setup lang="ts" name="loginIndex">

import {defineAsyncComponent, onMounted, reactive, computed, watch} from 'vue';
import { storeToRefs } from 'pinia';
import { useThemeConfig } from '/@/stores/themeConfig';
import { NextLoading } from '/@/utils/loading';
import logoMini from '/@/assets/logo-mini.png';
import loginMain from '/@/assets/login-main.svg';
import loginBg from '/@/assets/login-bg.png';
import { SystemConfigStore } from '/@/stores/systemConfig'
import { getBaseURL } from "/@/utils/baseUrl";
// 引入组件
const Account = defineAsyncComponent(() => import('/@/views/system/login/component/account.vue'));
const Mobile = defineAsyncComponent(() => import('/@/views/system/login/component/mobile.vue'));
const Scan = defineAsyncComponent(() => import('/@/views/system/login/component/scan.vue'));
const ChangePwd = defineAsyncComponent(() => import('/@/views/system/login/component/changePwd.vue'));
const OAuth2 = defineAsyncComponent(() => import('/@/views/system/login/component/oauth2.vue'));

import _ from "lodash-es";
import {useUserInfo} from "/@/stores/userInfo";
const { userInfos } = storeToRefs(useUserInfo());

// 定义变量内容
const storesThemeConfig = useThemeConfig();
const { themeConfig } = storeToRefs(storesThemeConfig);
const state = reactive({
	tabsActiveName: 'account',
	isScan: false,
});


watch(()=>userInfos.value.pwd_change_count,(val)=>{
  if(val===0){
    state.tabsActiveName ='changePwd'
  }else{
    state.tabsActiveName ='account'
  }
},{deep:true,immediate:true})


// 获取布局配置信息
const getThemeConfig = computed(() => {
	return themeConfig.value;
});

const systemConfigStore = SystemConfigStore()
const { systemConfig } = storeToRefs(systemConfigStore)
const getSystemConfig = computed(() => {
	return systemConfig.value
})

const siteLogo = computed(() => {
	if (!_.isEmpty(getSystemConfig.value['login.site_logo'])) {
		return getSystemConfig.value['login.site_logo']
	}
	return logoMini
});

const siteBg = computed(() => {
	if (!_.isEmpty(getSystemConfig.value['login.login_background'])) {
		return getSystemConfig.value['login.login_background']
	}
});

// 页面加载时
onMounted(() => {
	NextLoading.done();
});
</script>
<style scoped lang="scss">
</style>
