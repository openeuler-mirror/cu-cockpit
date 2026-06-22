<template v-for="item in logsConfig" :key="item.key">

                    <el-descriptions-item v-if="logsDetail[item.key]"
                        :label="item.label || item.key" :span="item.span ?? 1">
                        {{ logsDetail[item.key] }}
                    </el-descriptions-item>

                
</template>
<script lang="ts" setup>
import { onMounted, ref } from 'vue';
import { Local } from '/@/utils/storage';
import { logs } from '/@/api/log';
</script>
<style scoped lang="scss">
</style>