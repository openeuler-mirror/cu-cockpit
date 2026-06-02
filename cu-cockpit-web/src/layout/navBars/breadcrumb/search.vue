<template #default="{ item }">

						<div>
							<SvgIcon :name="item.meta.icon" class="mr5" />
							{{ $t(item.meta.title) }}
						</div>
					
</template>
<script setup lang="ts" name="layoutBreadcrumbSearch">
import { reactive, ref, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { storeToRefs } from 'pinia';
import { useTagsViewRoutes } from '/@/stores/tagsViewRoutes';
</script>
<style scoped lang="scss">
</style>
