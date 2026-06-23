<template>

</template>
<script lang="ts" setup name="terminalIndex">
import { onMounted, onBeforeUnmount, ref, reactive, watch, nextTick } from 'vue';
import { FormInstance, FormRules } from 'element-plus';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';
import { Local } from '/@/utils/storage';
import websocket from '/@/utils/websocket';
import { connect, check, getToken } from '/@/api/terminal';
import Cookies from 'js-cookie';
import { debounce } from 'lodash';
</script>
<style scoped lang="scss">
</style>