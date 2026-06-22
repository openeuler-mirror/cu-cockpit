<template #header>

                    <div class="card-header">
                        <span>{{ device.pttype ? device.pttype.toUpperCase() + ' 分区' : '分区' }}</span>
                    </div>
                
</template>
<script lang="ts" setup name="storageDetail">
import { onMounted, ref } from 'vue';
import { hardInfo } from '/@/api/run/run';
import { useRouter } from 'vue-router';
</script>
<style scoped lang="scss">
</style>
