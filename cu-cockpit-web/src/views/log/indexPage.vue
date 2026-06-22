<template>

</template>
<script lang="ts" setup name="logs">
import { reactive, ref, computed, onMounted, h, onActivated, onUnmounted, nextTick, watch } from 'vue';
import inputSelect from '/@/components/inputSelect/index.vue';
import { logs, getBoot } from '/@/api/log';
import { useRouter } from 'vue-router';
import { Local } from '/@/utils/storage';
import { ElPopover, RowEventHandlerParams } from 'element-plus';
</script>
<style>
</style>