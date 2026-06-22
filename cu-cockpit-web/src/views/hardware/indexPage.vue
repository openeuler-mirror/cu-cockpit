<template #label>

                        <div class="cell-item">
                            {{ item.label }}
                        </div>
                    
</template>
<script lang="ts" setup name="hardwareIndex">
import { reactive, onMounted, ref } from 'vue';
import { hardInfo, pciInfo, memorySlot } from '/@/api/run/run';
import { Refresh } from '@element-plus/icons-vue';
</script>
<style scoped lang="scss">
</style>
