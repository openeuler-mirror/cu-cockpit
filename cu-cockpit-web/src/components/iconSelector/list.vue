<template>

	<div class="icon-selector-warp-row">
		<el-scrollbar ref="selectorScrollbarRef">
			<el-row :gutter="10" v-if="props.list.length > 0">
				<el-col :xs="6" :sm="4" :md="4" :lg="4" :xl="4" v-for="(v, k) in list" :key="k" @click="onColClick(v)">
					<div class="icon-selector-warp-item" :class="{ 'icon-selector-active': prefix === v }">
						<SvgIcon :name="v" />
					</div>
				</el-col>
			</el-row>
			<el-empty :image-size="100" v-if="list.length <= 0" :description="empty"></el-empty>
		</el-scrollbar>
	</div>
</template>
<script setup lang="ts" name="iconSelectorList">
</script>
<style scoped lang="scss">
</style>
