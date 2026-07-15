<template>
    <div class="tech-services services-overview">
        <header class="services-hud">
            <div class="services-identity">
                <span class="services-identity__mark"><el-icon><Setting /></el-icon></span>
                <div>
                    <h1 class="services-title">服务管理</h1>
                    <div class="services-kicker">SERVICE CONTROL · SYSTEMD UNIT INVENTORY</div>
                </div>
            </div>
            <div class="services-hud__actions">
                <div v-if="u_Permission !== 'root'" class="services-access-state">
                    <el-icon><Lock /></el-icon>
                    <span>受限访问</span>
                </div>
                <div v-if="!loadError" class="services-sync-state">
                    <span class="services-sync-state__dot"></span>
                    <span>{{ serviceLoading ? '同步中' : '服务在线' }}</span>
                </div>
                <el-button class="services-action" :icon="Refresh" :loading="serviceLoading" @click="getService">
                    刷新
                </el-button>
            </div>
        </header>

        <section class="services-summary" aria-label="服务摘要">
            <div
                v-for="item in summaryItems"
                :key="item.label"
                class="services-summary__item"
                :style="{ '--summary-accent': item.color }"
            >
                <span class="services-summary__icon"><el-icon><component :is="item.icon" /></el-icon></span>
                <div>
                    <div class="services-summary__label">{{ item.label }}</div>
                    <div class="services-summary__value">{{ item.value }}</div>
                </div>
            </div>
        </section>

        <section class="services-panel">
            <div class="services-toolbar">
                <div class="services-filters">
                    <el-input
                        v-model="searchName"
                        class="services-filter--search"
                        :prefix-icon="Search"
                        placeholder="按服务名称或描述过滤"
                        clearable
                    />
                    <el-select
                        v-model="runtimeFilter"
                        class="services-filter--state"
                        multiple
                        clearable
                        placeholder="运行状态"
                    >
                        <el-option v-for="item in runtimeOptions" :key="item.value" :label="item.label" :value="item.value" />
                    </el-select>
                    <el-select
                        v-model="registerFilter"
                        class="services-filter--register"
                        multiple
                        collapse-tags
                        collapse-tags-tooltip
                        clearable
                        placeholder="注册状态"
                    >
                        <el-option v-for="item in registerOptions" :key="item.value" :label="item.label" :value="item.value" />
                    </el-select>
                </div>
                <div class="services-filter-count">
                    显示 <strong>{{ filteredServices.length }}</strong> / {{ services.length }} 项
                </div>
            </div>

            <div v-if="loadError && !serviceLoading" class="services-error">
                <el-icon><WarningFilled /></el-icon>
                <p>{{ loadError }}</p>
                <el-button class="services-action" :icon="Refresh" @click="getService">重新加载</el-button>
            </div>

            <el-table
                v-else
                v-loading="serviceLoading"
                :data="filteredServices"
                class="services-table"
                row-key="服务名称"
                size="large"
                empty-text="未检测到服务"
            >
                <el-table-column label="服务名称" min-width="240">
                    <template #default="{ row }">
                        <div class="service-identity" :class="{ 'is-active': row.运行状态 === 'active' }">
                            <span class="service-identity__mark"></span>
                            <span class="service-identity__name">{{ row.服务名称 }}</span>
                        </div>
                    </template>
                </el-table-column>
                <el-table-column label="描述" min-width="300" class-name="services-column--description">
                    <template #default="{ row }">
                        <span class="service-description" :class="{ 'is-empty': !row.描述 }">
                            {{ row.描述 || '暂无描述' }}
                        </span>
                    </template>
                </el-table-column>
                <el-table-column label="运行状态" width="124" align="center">
                    <template #default="{ row }">
                        <span class="service-runtime" :class="runtimeStatusClass(row.运行状态)">
                            <span class="service-runtime__dot"></span>
                            {{ runtimeStatusLabel(row.运行状态) }}
                        </span>
                    </template>
                </el-table-column>
                <el-table-column label="注册状态" width="132" align="center">
                    <template #default="{ row }">
                        <span class="service-register" :class="registerStatusClass(row.注册状态)">
                            {{ registerStatusLabel(row.注册状态) }}
                        </span>
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="156" align="center" fixed="right">
                    <template #default="{ row }">
                        <div v-if="canOperate(row)" class="service-commands">
                            <el-tooltip
                                :content="row.运行状态 === 'active' ? '服务已在运行' : '启动服务'"
                                placement="top"
                                effect="dark"
                                popper-class="service-command-tooltip"
                                :show-after="120"
                                :hide-after="0"
                            >
                                <el-button
                                    class="service-command service-command--start"
                                    :icon="VideoPlay"
                                    :loading="isOperating(row, 'start')"
                                    :disabled="row.运行状态 === 'active' || isOperating(row)"
                                    circle
                                    aria-label="启动服务"
                                    @click="setStatus('start', row)"
                                />
                            </el-tooltip>
                            <el-tooltip
                                content="重启服务"
                                placement="top"
                                effect="dark"
                                popper-class="service-command-tooltip"
                                :show-after="120"
                                :hide-after="0"
                            >
                                <el-button
                                    class="service-command service-command--restart"
                                    :icon="RefreshRight"
                                    :loading="isOperating(row, 'restart')"
                                    :disabled="isOperating(row)"
                                    circle
                                    aria-label="重启服务"
                                    @click="setStatus('restart', row)"
                                />
                            </el-tooltip>
                            <el-tooltip
                                :content="row.运行状态 !== 'active' ? '服务未运行' : '停止服务'"
                                placement="top"
                                effect="dark"
                                popper-class="service-command-tooltip"
                                :show-after="120"
                                :hide-after="0"
                            >
                                <el-button
                                    class="service-command service-command--stop"
                                    :icon="VideoPause"
                                    :loading="isOperating(row, 'stop')"
                                    :disabled="row.运行状态 !== 'active' || isOperating(row)"
                                    circle
                                    aria-label="停止服务"
                                    @click="setStatus('stop', row)"
                                />
                            </el-tooltip>
                        </div>
                        <span v-else>—</span>
                    </template>
                </el-table-column>
                <template #empty>
                    <div class="services-empty">
                        <el-icon><Operation /></el-icon>
                        <p>{{ services.length ? '没有符合筛选条件的服务' : '未检测到服务' }}</p>
                        <el-button v-if="hasFilters" class="services-action" @click="resetFilters">清除筛选</el-button>
                    </div>
                </template>
            </el-table>
        </section>
    </div>
</template>

<script setup lang="ts" name="servicesIndex">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue';
import {
    CircleCheck,
    CircleClose,
    Lock,
    Operation,
    Refresh,
    RefreshRight,
    Search,
    Setting,
    VideoPause,
    VideoPlay,
    WarningFilled,
} from '@element-plus/icons-vue';
import { ElMessageBox } from 'element-plus';
import { storeToRefs } from 'pinia';
import { serviceStatus, runServiceManage } from '/@/api/run/run';
import { useThemeConfig } from '/@/stores/themeConfig';
import { userPermissiom } from '/@/stores/userPermissiom';
import { errorNotification, successNotification } from '/@/utils/message';

interface ServiceRow {
    服务名称: string;
    描述: string;
    运行状态: string;
    注册状态: string;
}

interface RequestError {
    request?: {
        responseText?: string;
    };
}

interface ErrorPayload {
    error?: string;
}

type StatusType = 'start' | 'stop' | 'restart';

const permissionStore = userPermissiom();
const themeStore = useThemeConfig();
const { u_Permission } = storeToRefs(permissionStore);
const { themeConfig } = storeToRefs(themeStore);
const services = ref<ServiceRow[]>([]);
const serviceLoading = ref(false);
const loadError = ref('');
const searchName = ref('');
const runtimeFilter = ref<string[]>([]);
const registerFilter = ref<string[]>([]);
const operating = ref<{ name: string; action: StatusType } | null>(null);

const runtimeOptions = [
    { value: 'active', label: '运行中' },
    { value: 'inactive', label: '未运行' },
];

const registerOptions = [
    { value: 'enabled', label: '启用' },
    { value: 'disabled', label: '禁用' },
    { value: 'static', label: '静态' },
    { value: 'alias', label: '别名' },
    { value: 'indirect', label: '间接' },
    { value: 'masked', label: '已屏蔽' },
];

const isEnabled = (status: string) => ['enabled', 'enabled-runtime'].includes(status);
const canOperate = (row: ServiceRow) => ['enabled', 'enabled-runtime', 'disabled'].includes(row.注册状态);
const hasFilters = computed(() => Boolean(searchName.value || runtimeFilter.value.length || registerFilter.value.length));

const matchesRegisterFilter = (status: string) => {
    if (!registerFilter.value.length) return true;
    return registerFilter.value.some((selected) => (selected === 'enabled' ? isEnabled(status) : selected === status));
};

const filteredServices = computed(() => {
    const keyword = searchName.value.trim().toLowerCase();
    return services.value.filter((service) => {
        const matchesKeyword =
            !keyword ||
            service.服务名称.toLowerCase().includes(keyword) ||
            (service.描述 || '').toLowerCase().includes(keyword);
        const matchesRuntime = !runtimeFilter.value.length || runtimeFilter.value.includes(service.运行状态);
        return matchesKeyword && matchesRuntime && matchesRegisterFilter(service.注册状态);
    });
});

const serviceSummary = computed(() => ({
    total: services.value.length,
    active: services.value.filter((service) => service.运行状态 === 'active').length,
    inactive: services.value.filter((service) => service.运行状态 === 'inactive').length,
    operable: services.value.filter(canOperate).length,
}));

const summaryItems = computed(() => [
    { label: '服务总量', value: serviceSummary.value.total, icon: Setting, color: '#22d3ee' },
    { label: '运行中', value: serviceSummary.value.active, icon: CircleCheck, color: '#10f5a0' },
    { label: '已停止', value: serviceSummary.value.inactive, icon: CircleClose, color: '#ffb020' },
    { label: '可管理服务', value: serviceSummary.value.operable, icon: Operation, color: '#a855f7' },
]);

const runtimeStatusLabels: Record<string, string> = { active: '运行中', inactive: '未运行' };
const runtimeStatusLabel = (status: string) => runtimeStatusLabels[status] || status || '未知';
const runtimeStatusClass = (status: string) => ({ 'is-active': status === 'active', 'is-inactive': status === 'inactive' });
const registerStatusLabels: Record<string, string> = {
    enabled: '启用',
    'enabled-runtime': '临时启用',
    disabled: '禁用',
    static: '静态',
    alias: '别名',
    indirect: '间接',
    masked: '已屏蔽',
};
const registerStatusLabel = (status: string) => registerStatusLabels[status] || status || '未知';
const registerStatusClass = (status: string) => `is-${isEnabled(status) ? 'enabled' : status || 'unknown'}`;

const resetFilters = () => {
    searchName.value = '';
    runtimeFilter.value = [];
    registerFilter.value = [];
};

const getService = async () => {
    serviceLoading.value = true;
    loadError.value = '';
    try {
        const response = await serviceStatus();
        services.value = Array.isArray(response) ? response : [];
    } catch (error) {
        services.value = [];
        loadError.value = '服务状态加载失败，请检查服务管理接口后重试。';
        console.error('获取服务状态失败:', error);
    } finally {
        serviceLoading.value = false;
    }
};

const isOperating = (row: ServiceRow, action?: StatusType) =>
    operating.value?.name === row.服务名称 && (!action || operating.value.action === action);

const parseOperationError = (error: unknown) => {
    if (typeof error !== 'object' || error === null) return '';
    const responseText = (error as RequestError).request?.responseText;
    if (!responseText) return '';
    try {
        const payload = JSON.parse(responseText) as ErrorPayload;
        return typeof payload.error === 'string' ? payload.error : '';
    } catch {
        return '';
    }
};

const setStatus = async (status: StatusType, service: ServiceRow) => {
    if (u_Permission.value !== 'root') {
        await ElMessageBox.alert('被限制访问模式下不可操作，请切换到管理员模式', '提示', {
            confirmButtonText: '确定',
        });
        return;
    }

    const actionLabels: Record<StatusType, string> = { start: '启动', stop: '停止', restart: '重启' };
    try {
        await ElMessageBox.confirm(`是否确定${actionLabels[status]} ${service.服务名称} 服务`, '服务操作确认', {
            confirmButtonText: '确认',
            cancelButtonText: '取消',
            type: 'warning',
        });
        operating.value = { name: service.服务名称, action: status };
        const response = await runServiceManage({ service_name: service.服务名称, operation: status });
        if (response?.return_code === 0) {
            successNotification(`${service.服务名称}${actionLabels[status]}成功`);
            await getService();
        } else {
            errorNotification(`${service.服务名称}${actionLabels[status]}失败`);
        }
    } catch (error: unknown) {
        if (error === 'cancel' || error === 'close') return;
        const detail = parseOperationError(error);
        errorNotification(
            detail
                ? `${service.服务名称}服务出现${detail}，${actionLabels[status]}失败`
                : `${service.服务名称}${actionLabels[status]}失败`
        );
    } finally {
        operating.value = null;
    }
};

const mountServicesTechShell = () => document.documentElement.classList.add('theme-tech-dark');
const restoreServicesTechShell = () => {
    if (!themeConfig.value.isTechTheme) document.documentElement.classList.remove('theme-tech-dark');
};
const resetMainScroll = async () => {
    await nextTick();
    const scrollContainer = document.querySelector<HTMLElement>('.layout-main-scroll.el-scrollbar__wrap');
    if (scrollContainer) scrollContainer.scrollTop = 0;
};

onMounted(() => {
    mountServicesTechShell();
    resetMainScroll();
    getService();
});

onUnmounted(restoreServicesTechShell);
</script>

<style lang="scss">
@use './tech-services.scss';
</style>