<template>

	<div class="other-fast-way" v-if="backends.length">
		<div class="fast-title"><span>其他快速方式登录</span></div>
		<ul class="fast-list">
			<li v-for="(v, k) in backends" :key="v">
				<a @click.once="handleOAuth2LoginClick(v)" style="width: 50px;color: #18bc9c">
					<img :src="v.icon" :alt="v.app_name" />
										<p>{{ v.app_name }}</p>

				</a>
			</li>
		</ul>
	</div>
</template>
<script lang="ts">

import { defineComponent, onMounted, reactive, toRefs } from 'vue';
import * as loginApi from '../api';
import { OAuth2Backend } from '/@/views/system/login/types';

export default defineComponent({
	name: 'loginOAuth2',
	setup() {
		const handleOAuth2LoginClick = (backend: OAuth2Backend) => {
			history.replaceState(null, '', location.pathname + location.search);
			window.location.href = backend.authentication_url + '?next=' + window.location.href;
		};
		const state = reactive({
			handleOAuth2LoginClick: handleOAuth2LoginClick,
			backends: [],
		});
		const getBackends = async () => {
			loginApi.getBackends().then((ret: any) => {				
				state.backends = ret.data;
			});
		};
		// const handleTreeClick = (record: MenuTreeItemType) => {
		//   menuButtonRef.value?.handleRefreshTable(record);
		//   menuFieldRef.value?.handleRefreshTable(record)
		// };

		onMounted(() => {
			// getBackends();
		});
		return {
			...toRefs(state),
		};
	},
});
</script>
<style scoped lang="scss">
</style>
