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
</script>
<style scoped lang="scss">
</style>
