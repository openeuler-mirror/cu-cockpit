<template>

	<div class="layout-padding layout-padding-unset layout-iframe">
		<div class="layout-padding-auto layout-padding-view">
			<div class="w100" v-for="v in setIframeList" :key="v.path" v-loading="v.meta.loading" element-loading-background="white">
				<transition-group :name="name" mode="out-in">
					<iframe
						:src="v.meta.isLink"
						:key="v.path"
						frameborder="0"
						height="100%"
						width="100%"
						style="position: absolute"
						:data-url="v.path"
						v-show="getRoutePath === v.path"
						ref="iframeRef"
					/>
				</transition-group>
			</div>
		</div>
	</div>
</template>
<script setup lang="ts" name="layoutIframeView">
import { computed, watch, ref, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import {cookie} from "xe-utils";
</script>
