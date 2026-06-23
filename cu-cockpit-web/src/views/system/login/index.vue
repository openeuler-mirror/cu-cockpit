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
import _ from "lodash-es";
import {useUserInfo} from "/@/stores/userInfo";
</script>
<style scoped lang="scss">
</style>
