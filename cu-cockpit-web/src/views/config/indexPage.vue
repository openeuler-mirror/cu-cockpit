<template #label>

                                <div class="cell-item">SHA256</div>
                            
</template>
<script lang="ts" setup name="configIndex">
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue';
import { configGet, hostSet, timeSet, configUpdate } from '/@/api/config/config';
import type { FormInstance, FormRules } from 'element-plus';
import { ElMessage, ElMessageBox } from 'element-plus';
import dayjs from 'dayjs'
import { storeToRefs } from 'pinia';
import { userPermissiom } from '/@/stores/userPermissiom';
</script>
<style scoped lang="scss">
</style>
