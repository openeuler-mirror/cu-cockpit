<template>
	<div class="tech-storage storage-detail">
		<header class="storage-hud">
			<div class="storage-identity">
				<el-button class="storage-back" :icon="ArrowLeft" circle aria-label="返回存储列表" @click="backToStorage" />
				<div>
					<h1 class="storage-title">设备详情</h1>
					<div class="storage-kicker">DEVICE PROFILE · {{ props.name }}</div>
				</div>
			</div>
			<div class="storage-hud__actions">
				<div class="storage-status" v-if="device && !loadError">
					<span class="storage-status__dot"></span>
					<span>设备已识别</span>
				</div>
				<el-button class="storage-action" :icon="Refresh" :loading="loading" @click="getStorageInfo">刷新</el-button>
			</div>
		</header>

		<nav class="storage-breadcrumb" aria-label="设备路径">
			<el-breadcrumb :separator-icon="ArrowRight">
				<el-breadcrumb-item :to="{ name: 'storage' }">存储拓扑</el-breadcrumb-item>
				<el-breadcrumb-item
					v-for="item in breadcrumbs"
					:key="item"
					:to="{ name: 'storageDetail', params: { name: item } }"
				>
					{{ item }}
				</el-breadcrumb-item>
			</el-breadcrumb>
		</nav>

		<section class="storage-panel" v-loading="loading" v-if="loadError || !device">
			<div class="storage-error" v-if="!loading">
				<el-icon><WarningFilled /></el-icon>
				<p>{{ loadError || '未找到该存储设备。' }}</p>
				<el-button class="storage-action" :icon="ArrowLeft" @click="backToStorage">返回存储拓扑</el-button>
			</div>
		</section>

		<template v-if="device">
			<section class="device-profile">
				<div class="device-profile__identity">
					<span class="device-profile__icon"><i class="iconfont" :class="deviceIcon(device.type)"></i></span>
					<div>
						<h2 class="device-profile__name">{{ device.name }}</h2>
						<div class="device-profile__meta">
							<span class="device-type">{{ typeLabel(device.type) }}</span>
							<span class="device-profile__chip">{{ device.fstype || '无文件系统' }}</span>
							<span class="device-profile__chip">{{ device.mountpoint || '未挂载' }}</span>
						</div>
					</div>
				</div>
				<div class="device-profile__capacity">
					<div class="device-profile__capacity-label">标称容量</div>
					<div class="device-profile__capacity-value">{{ device.size || '—' }}</div>
				</div>
			</section>

			<div class="storage-sections">
				<section class="storage-info-section is-wide" v-if="isPhysicalDevice">
					<div class="storage-info-section__head">
						<h2 class="storage-info-section__title"><el-icon><Cpu /></el-icon>硬件身份</h2>
					</div>
					<div class="storage-info-grid">
						<div
							v-for="item in hardwareInfo"
							:key="item.label"
							class="storage-info-item"
							:style="{ '--field-accent': item.color }"
						>
							<div class="storage-info-item__label"><i class="iconfont" :class="item.icon"></i>{{ item.label }}</div>
							<div class="storage-info-item__value">{{ displayValue(item.value) }}</div>
						</div>
					</div>
				</section>

				<section class="storage-info-section" v-if="!isPhysicalDevice">
					<div class="storage-info-section__head">
						<h2 class="storage-info-section__title"><el-icon><Grid /></el-icon>分区标识</h2>
					</div>
					<div class="storage-info-grid">
						<div
							v-for="item in partitionInfo"
							:key="item.label"
							class="storage-info-item"
							:style="{ '--field-accent': item.color }"
						>
							<div class="storage-info-item__label"><i class="iconfont" :class="item.icon"></i>{{ item.label }}</div>
							<div class="storage-info-item__value">{{ displayValue(item.value) }}</div>
						</div>
					</div>
				</section>

				<section class="storage-info-section" v-if="!isPhysicalDevice">
					<div class="storage-info-section__head">
						<h2 class="storage-info-section__title"><el-icon><FolderOpened /></el-icon>文件系统</h2>
					</div>
					<div class="storage-info-grid">
						<div
							v-for="item in filesystemInfo"
							:key="item.label"
							class="storage-info-item"
							:style="{ '--field-accent': item.color }"
						>
							<div class="storage-info-item__label"><i class="iconfont" :class="item.icon"></i>{{ item.label }}</div>
							<div class="storage-info-item__value">{{ displayValue(item.value) }}</div>
						</div>
					</div>
				</section>

				<section class="storage-info-section is-wide" v-if="device.children?.length">
					<div class="storage-info-section__head">
						<h2 class="storage-info-section__title"><el-icon><Connection /></el-icon>下级设备</h2>
						<span class="child-count">{{ device.children.length }} 个节点</span>
					</div>
					<el-table :data="device.children" class="storage-table" size="large" @row-click="toDetail">
						<el-table-column label="设备标识" min-width="140">
							<template #default="{ row }">
								<div class="device-name">
									<span class="device-name__icon"><i class="iconfont" :class="deviceIcon(row.type)"></i></span>
									<span class="device-name__text">{{ row.name }}</span>
								</div>
							</template>
						</el-table-column>
						<el-table-column
							label="类型"
							min-width="140"
							align="center"
							class-name="storage-column--mobile-hidden storage-column--type"
						>
							<template #default="{ row }"><span class="device-type">{{ typeLabel(row.type) }}</span></template>
						</el-table-column>
						<el-table-column prop="fstype" label="文件系统" min-width="140" class-name="storage-column--secondary">
							<template #default="{ row }">{{ row.fstype || '—' }}</template>
						</el-table-column>
						<el-table-column label="挂载位置" min-width="140" class-name="storage-column--secondary">
							<template #default="{ row }">
								<div class="mount-state" :class="{ 'is-mounted': Boolean(row.mountpoint) }">
									<span class="mount-state__dot"></span>
									<span class="mount-state__path">{{ row.mountpoint || '未挂载' }}</span>
								</div>
							</template>
						</el-table-column>
						<el-table-column label="容量" min-width="140" align="right">
							<template #default="{ row }"><span class="storage-size">{{ row.size || '—' }}</span></template>
						</el-table-column>
						<el-table-column
							label=""
							width="60"
							align="center"
							class-name="storage-column--secondary storage-column--action"
						>
							<template #default><span class="storage-detail-link"><el-icon><ArrowRight /></el-icon></span></template>
						</el-table-column>
					</el-table>
				</section>
			</div>
		</template>
	</div>
</template>

<script lang="ts" setup name="storageDetail">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { ArrowLeft, ArrowRight, Connection, Cpu, FolderOpened, Grid, Refresh, WarningFilled } from '@element-plus/icons-vue';
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router';
import { hardInfo } from '/@/api/run/run';
import { useThemeConfig } from '/@/stores/themeConfig';

interface Hardware {
	ID_MODEL?: string;
	ID_REVISION?: string;
	ID_SERIAL_SHORT?: string;
	ID_VENDOR?: string;
}

interface Device {
	name: string;
	type: string;
	fstype?: string;
	pttype?: string;
	size?: string;
	mountpoint?: string | null;
	partuuid?: string;
	uuid?: string;
	children?: Device[];
	hardware?: Hardware;
}

const props = defineProps<{ name: string }>();
const router = useRouter();
const themeStore = useThemeConfig();
const { themeConfig } = storeToRefs(themeStore);
const loading = ref(false);
const loadError = ref('');
const device = ref<Device | null>(null);
const breadcrumbs = ref<string[]>([]);

const resetMainScroll = async () => {
	await nextTick();
	const scrollContainer = document.querySelector<HTMLElement>('.layout-main-scroll.el-scrollbar__wrap');
	if (scrollContainer) scrollContainer.scrollTop = 0;
};

const findDeviceByName = (devices: Device[], targetName: string, currentPath: string[]): Device | null => {
	for (const currentDevice of devices) {
		const nextPath = [...currentPath, currentDevice.name];
		if (currentDevice.name === targetName) {
			breadcrumbs.value = nextPath;
			return currentDevice;
		}
		if (currentDevice.children?.length) {
			const found = findDeviceByName(currentDevice.children, targetName, nextPath);
			if (found) return found;
		}
	}
	return null;
};

const getStorageInfo = async () => {
	loading.value = true;
	loadError.value = '';
	device.value = null;
	breadcrumbs.value = [];
	try {
		const response = await hardInfo('storage');
		const devices: Device[] = Array.isArray(response?.blockdevices) ? response.blockdevices : [];
		device.value = findDeviceByName(devices, props.name, []);
		if (!device.value) loadError.value = `未在存储拓扑中找到设备“${props.name}”。`;
	} catch (error) {
		loadError.value = '设备信息加载失败，请检查监控服务后重试。';
		console.error('获取存储设备详情失败:', error);
	} finally {
		loading.value = false;
		await resetMainScroll();
	}
};

const isPhysicalDevice = computed(() => device.value?.type === 'disk' || device.value?.type === 'rom');
const typeLabel = (type: string) => ({ disk: '磁盘', part: '分区', lvm: '逻辑卷', rom: '光驱' })[type] || type || '未知';
const deviceIcon = (type: string) => (type === 'part' || type === 'lvm' ? 'icon-shebeileixing' : 'icon-04');
const displayValue = (value: unknown) => (value === null || value === undefined || value === '' ? '—' : String(value));

const hardwareInfo = computed(() => [
	{ label: '厂商', value: device.value?.hardware?.ID_VENDOR, icon: 'icon-mingcheng', color: '#22d3ee' },
	{ label: '型号', value: device.value?.hardware?.ID_MODEL, icon: 'icon-shebeileixing', color: '#a855f7' },
	{ label: '固件版本', value: device.value?.hardware?.ID_REVISION, icon: 'icon-lishibanben', color: '#ffb020' },
	{ label: '序列号', value: device.value?.hardware?.ID_SERIAL_SHORT, icon: 'icon-bianhao1', color: '#10f5a0' },
]);

const partitionInfo = computed(() => [
	{ label: '设备名称', value: device.value?.name, icon: 'icon-mingcheng', color: '#22d3ee' },
	{ label: '分区 UUID', value: device.value?.partuuid, icon: 'icon-fuwenben', color: '#a855f7' },
	{ label: '分区表类型', value: device.value?.pttype, icon: 'icon-shebeileixing', color: '#ffb020' },
	{ label: '标称容量', value: device.value?.size, icon: 'icon-cunchudaxiao', color: '#10f5a0' },
]);

const filesystemInfo = computed(() => [
	{ label: '文件系统类型', value: device.value?.fstype, icon: 'icon-shebeileixing', color: '#22d3ee' },
	{ label: '文件系统 UUID', value: device.value?.uuid, icon: 'icon-fuwenben', color: '#a855f7' },
	{ label: '挂载点', value: device.value?.mountpoint, icon: 'icon-guazaidian', color: '#10f5a0' },
	{ label: '挂载状态', value: device.value?.mountpoint ? '已挂载' : '未挂载', icon: 'icon-04', color: '#ffb020' },
]);

const toDetail = (row: Device) => router.push({ name: 'storageDetail', params: { name: row.name } });
const backToStorage = () => router.push({ name: 'storage' });
const mountStorageTechShell = () => document.documentElement.classList.add('theme-tech-dark');
const restoreStorageTechShell = () => {
	if (!themeConfig.value.isTechTheme) document.documentElement.classList.remove('theme-tech-dark');
};

watch(() => props.name, getStorageInfo, { immediate: true });
onMounted(mountStorageTechShell);
onUnmounted(restoreStorageTechShell);
</script>

<style lang="scss">
@use './tech-storage.scss';
</style>
