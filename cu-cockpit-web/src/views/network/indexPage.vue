<template>
	<div class="tech-network">
		<header class="network-hud">
			<div class="network-identity"><span><el-icon><Connection /></el-icon></span><div><h1>网络与防火墙</h1><p>INTERFACES · ROUTES · DNS · LISTENERS · FIREWALLD</p></div></div>
			<div class="network-hud__actions"><span class="network-state" :class="{ 'is-active': overview.firewall.active }"><span></span>{{ overview.firewall.active ? 'FIREWALLD 在线' : 'FIREWALLD 未运行' }}</span><el-button class="network-action" :icon="Refresh" :loading="loading" @click="loadData">刷新</el-button></div>
		</header>
		<section class="network-summary">
			<div v-for="item in summaryItems" :key="item.label" class="network-summary__item" :style="{ '--summary-accent': item.color }"><span><el-icon><component :is="item.icon" /></el-icon></span><div><small>{{ item.label }}</small><strong>{{ item.value }}</strong></div></div>
		</section>
		<section class="network-panel" v-loading="loading">
			<el-tabs v-model="activeTab" class="network-tabs">
				<el-tab-pane label="接口与 IP" name="interfaces">
					<div class="network-interface-grid">
						<article v-for="item in overview.interfaces" :key="item.ifindex" class="network-interface-card">
							<div class="network-interface-card__head"><span :class="{ 'is-up': item.up }"><el-icon><Monitor /></el-icon></span><div><h3>{{ item.name }}</h3><small>{{ item.type }} · MTU {{ item.mtu }}</small></div><strong :class="{ 'is-up': item.up }">{{ item.state }}</strong></div>
							<div class="network-interface-card__mac">{{ item.mac || '无 MAC' }}</div>
							<div class="network-address-list"><span v-for="address in item.addresses" :key="`${address.family}-${address.local}`"><b>{{ address.family }}</b>{{ address.local }}/{{ address.prefixlen }}</span><em v-if="!item.addresses.length">无 IP 地址</em></div>
						</article>
					</div>
				</el-tab-pane>
				<el-tab-pane label="路由与 DNS" name="routes">
					<div class="network-dns-bar"><div><small>DNS 服务器</small><strong>{{ overview.dns.nameservers.join(' · ') || '未配置' }}</strong></div><div><small>默认网关</small><strong>{{ defaultRoute.gateway || '—' }} · {{ defaultRoute.dev || '—' }}</strong></div><code>{{ overview.dns.path }}</code></div>
					<div class="network-table-wrap"><el-table :data="pagedRoutes" class="network-table network-route-table"><el-table-column prop="dst" label="目标" min-width="130"><template #default="{ row }"><code>{{ row.dst || 'default' }}</code></template></el-table-column><el-table-column prop="gateway" label="网关" min-width="100"><template #default="{ row }">{{ row.gateway || '直连' }}</template></el-table-column><el-table-column prop="dev" label="接口" min-width="115" /><el-table-column prop="protocol" label="协议" min-width="110" class-name="network-col-secondary" /><el-table-column prop="prefsrc" label="源地址" min-width="150" class-name="network-col-secondary" /><el-table-column prop="metric" label="Metric" width="80" align="right" class-name="network-col-metric" /></el-table></div>
					<div v-if="overview.routes.length" class="network-pagination">
						<el-pagination
							:current-page="routePage"
							:page-size="routePageSize"
							:page-sizes="pageSizeOptions"
							:pager-count="5"
							:total="overview.routes.length"
							layout="total, sizes, prev, pager, next"
							@size-change="onRoutePageSizeChange"
							@current-change="routePage = $event"
						/>
						<span class="network-pagination__page">{{ routePage }} / {{ Math.ceil(overview.routes.length / routePageSize) }}</span>
					</div>
				</el-tab-pane>
				<el-tab-pane label="监听端口" name="listeners">
					<div class="network-tab-toolbar"><el-input v-model="listenerSearch" :prefix-icon="Search" clearable placeholder="端口 / 地址 / 进程" @input="listenerPage = 1" /></div>
					<div class="network-table-wrap"><el-table :data="pagedListeners" class="network-table network-listener-table"><el-table-column prop="protocol" label="协议" width="90"><template #default="{ row }"><span class="network-protocol">{{ row.protocol }}</span></template></el-table-column><el-table-column label="监听地址" min-width="210"><template #default="{ row }"><code>{{ row.local_address }}:{{ row.local_port }}</code></template></el-table-column><el-table-column prop="state" label="状态" width="100" class-name="network-col-secondary" /><el-table-column label="进程" min-width="230" class-name="network-col-secondary"><template #default="{ row }">{{ row.processes.map((item) => `${item.name}(${item.pid})`).join(', ') || '未公开' }}</template></el-table-column><el-table-column label="Peer" min-width="170" class-name="network-col-secondary"><template #default="{ row }"><code>{{ row.peer_address }}:{{ row.peer_port }}</code></template></el-table-column></el-table></div>
					<div v-if="filteredListeners.length" class="network-pagination">
						<el-pagination
							:current-page="listenerPage"
							:page-size="listenerPageSize"
							:page-sizes="pageSizeOptions"
							:pager-count="5"
							:total="filteredListeners.length"
							layout="total, sizes, prev, pager, next"
							@size-change="onListenerPageSizeChange"
							@current-change="listenerPage = $event"
						/>
						<span class="network-pagination__page">{{ listenerPage }} / {{ Math.ceil(filteredListeners.length / listenerPageSize) }}</span>
					</div>
				</el-tab-pane>
				<el-tab-pane label="Firewalld" name="firewall">
					<div class="network-firewall-status" :class="{ 'is-active': overview.firewall.active }"><span><el-icon><Lock /></el-icon></span><div><h3>{{ overview.firewall.active ? 'Firewalld 正在运行' : 'Firewalld 未运行' }}</h3><p>{{ overview.firewall.reason || `默认区域：${overview.firewall.default_zone}` }}</p></div><el-button class="network-action" :icon="Plus" :disabled="!isAdmin || !overview.firewall.writable" @click="openFirewallDialog">添加规则</el-button></div>
					<div v-if="overview.firewall.zones.length" class="network-zone-grid"><article v-for="zone in overview.firewall.zones" :key="zone.name" class="network-zone-card"><div><h3>{{ zone.name }}</h3><span v-if="zone.default">DEFAULT</span></div><p>接口：{{ zone.interfaces.join(', ') || '—' }}</p><section><small>Services</small><span v-for="service in zone.services" :key="service">{{ service }}<button v-if="isAdmin" @click="removeRule(zone.name, 'service', service)">×</button></span><em v-if="!zone.services.length">无</em></section><section><small>Ports</small><span v-for="port in zone.ports" :key="port">{{ port }}<button v-if="isAdmin" @click="removePort(zone.name, port)">×</button></span><em v-if="!zone.ports.length">无</em></section></article></div>
					<div v-else class="network-firewall-empty"><el-icon><WarningFilled /></el-icon><span>{{ overview.firewall.reason || '没有可显示的 zone' }}</span></div>
				</el-tab-pane>
			</el-tabs>
		</section>
		<el-dialog v-model="firewallDialog" title="添加 Firewalld 规则" width="min(520px, 94vw)" class="network-dialog">
			<el-form label-position="top"><el-form-item label="Zone"><el-select v-model="ruleForm.zone"><el-option v-for="zone in overview.firewall.zones" :key="zone.name" :label="zone.name" :value="zone.name" /></el-select></el-form-item><el-form-item label="规则类型"><el-segmented v-model="ruleForm.rule_type" :options="[{ label: 'Service', value: 'service' }, { label: 'Port', value: 'port' }]" /></el-form-item><el-form-item v-if="ruleForm.rule_type === 'service'" label="Service"><el-select v-model="ruleForm.value" filterable><el-option v-for="service in overview.firewall.available_services" :key="service" :label="service" :value="service" /></el-select></el-form-item><template v-else><el-form-item label="端口"><el-input v-model="ruleForm.value" placeholder="1-65535" /></el-form-item><el-form-item label="协议"><el-radio-group v-model="ruleForm.protocol"><el-radio-button label="tcp">TCP</el-radio-button><el-radio-button label="udp">UDP</el-radio-button></el-radio-group></el-form-item></template></el-form>
			<template #footer><el-button @click="firewallDialog = false">取消</el-button><el-button type="primary" :loading="saving" @click="addRule">添加 Runtime + Permanent</el-button></template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts" name="networkIndex">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue';
import { Connection, Lock, Monitor, Plus, Refresh, Search, WarningFilled } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { storeToRefs } from 'pinia';
import { getNetworkOverview, updateFirewallRule } from '/@/api/system/network';
import type { NetworkOverview } from '/@/api/system/network';
import { userPermissiom } from '/@/stores/userPermissiom';
import { useThemeConfig } from '/@/stores/themeConfig';

const permissionStore = userPermissiom(); const { u_Permission } = storeToRefs(permissionStore); const isAdmin = computed(() => u_Permission.value === 'root');
const themeStore = useThemeConfig(); const { themeConfig } = storeToRefs(themeStore);
const loading = ref(false); const saving = ref(false); const activeTab = ref('interfaces'); const listenerSearch = ref(''); const firewallDialog = ref(false);
const routePage = ref(1); const routePageSize = ref(10); const listenerPage = ref(1); const listenerPageSize = ref(10); const pageSizeOptions = [10, 20, 50];
const overview = reactive<NetworkOverview>({ interfaces: [], routes: [], default_routes: [], dns: { nameservers: [], search: [], options: [], path: '', symlink: false }, listeners: [], firewall: { installed: false, active: false, writable: false, reason: '', default_zone: '', zones: [], available_services: [] }, summary: { interfaces: 0, interfaces_up: 0, addresses: 0, routes: 0, listeners: 0 } });
const ruleForm = reactive<{ zone: string; rule_type: 'service' | 'port'; value: string; protocol: 'tcp' | 'udp' }>({ zone: '', rule_type: 'service', value: '', protocol: 'tcp' });
const defaultRoute = computed(() => overview.default_routes[0] || {});
const pagedRoutes = computed(() => { const start = (routePage.value - 1) * routePageSize.value; return overview.routes.slice(start, start + routePageSize.value); });
const summaryItems = computed(() => [
	{ label: '网络接口', value: `${overview.summary.interfaces_up}/${overview.summary.interfaces} UP`, icon: Connection, color: '#22d3ee' },
	{ label: 'IP 地址', value: overview.summary.addresses, icon: Monitor, color: '#10f5a0' },
	{ label: '路由条目', value: overview.summary.routes, icon: Connection, color: '#a855f7' },
	{ label: '监听端口', value: overview.summary.listeners, icon: Lock, color: '#ffb020' },
]);
const filteredListeners = computed(() => { const keyword = listenerSearch.value.trim().toLowerCase(); return overview.listeners.filter((item) => !keyword || `${item.protocol} ${item.local_address} ${item.local_port} ${item.processes.map((process) => process.name).join(' ')}`.toLowerCase().includes(keyword)); });
const pagedListeners = computed(() => { const start = (listenerPage.value - 1) * listenerPageSize.value; return filteredListeners.value.slice(start, start + listenerPageSize.value); });
const loadData = async () => { loading.value = true; try { await permissionStore.refreshUserPermission(); Object.assign(overview, await getNetworkOverview()); routePage.value = Math.min(routePage.value, Math.max(1, Math.ceil(overview.routes.length / routePageSize.value))); listenerPage.value = Math.min(listenerPage.value, Math.max(1, Math.ceil(filteredListeners.value.length / listenerPageSize.value))); } catch (error) { ElMessage.error('网络数据加载失败'); console.error(error); } finally { loading.value = false; } };
const onRoutePageSizeChange = (size: number) => { routePageSize.value = size; routePage.value = 1; };
const onListenerPageSizeChange = (size: number) => { listenerPageSize.value = size; listenerPage.value = 1; };
const openFirewallDialog = () => { ruleForm.zone = overview.firewall.default_zone || overview.firewall.zones[0]?.name || ''; ruleForm.rule_type = 'service'; ruleForm.value = ''; ruleForm.protocol = 'tcp'; firewallDialog.value = true; };
const addRule = async () => { saving.value = true; try { await updateFirewallRule({ action: 'add', ...ruleForm }); firewallDialog.value = false; ElMessage.success('规则已添加'); await loadData(); } catch (error) { console.error(error); } finally { saving.value = false; } };
const removeRule = async (zone: string, ruleType: 'service' | 'port', value: string, protocol?: 'tcp' | 'udp') => { await ElMessageBox.confirm(`从 ${zone} 删除 ${value}？`, '删除防火墙规则', { type: 'warning' }); await updateFirewallRule({ action: 'remove', zone, rule_type: ruleType, value, protocol }); ElMessage.success('规则已删除'); await loadData(); };
const removePort = (zone: string, value: string) => { const [port, protocol] = value.split('/'); return removeRule(zone, 'port', port, protocol as 'tcp' | 'udp'); };
const mountTechShell = () => document.documentElement.classList.add('theme-tech-dark'); const restoreTechShell = () => { if (!themeConfig.value.isTechTheme) document.documentElement.classList.remove('theme-tech-dark'); };
onMounted(() => { mountTechShell(); loadData(); }); onUnmounted(restoreTechShell);
</script>

<style lang="scss">
@use './tech-network.scss';
</style>