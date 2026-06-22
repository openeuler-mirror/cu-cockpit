<template>

	<div class="login-scan-container">
		<div ref="qrcodeRef"></div>
		<div class="font12 mt20 login-msg">{{ $t('message.scan.text') }}</div>
	</div>
</template>
<script lang="ts">

import { ref, defineComponent, onMounted } from 'vue';
import QRCode from 'qrcodejs2-fixes';

export default defineComponent({
	name: 'loginScan',
	setup() {
		const qrcodeRef = ref<HTMLElement | null>(null);
		
		return { qrcodeRef };
	},
});
</script>
<style scoped lang="scss">
</style>
