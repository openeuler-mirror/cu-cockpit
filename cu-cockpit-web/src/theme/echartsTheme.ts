/**
 * ECharts「科技暗色」公共主题
 * 各图表页可复用这些片段，保证暗色主题下坐标轴、网格、图例与色板风格统一。
 *
 * 用法示例：
 *   import { techChartPalette, techDarkAxis, techDarkTooltip } from '/@/theme/echartsTheme';
 *   const option = { color: techChartPalette, tooltip: techDarkTooltip(), xAxis: { ...techDarkAxis('category') } };
 */

/** 发光色板：青 / 紫 / 绿 / 琥珀 / 蓝 / 红 */
export const techChartPalette = ['#22d3ee', '#a855f7', '#10f5a0', '#ffb020', '#3b82f6', '#ff4d6d'];

/** 暗色 tooltip 片段 */
export function techDarkTooltip() {
	return {
		backgroundColor: 'rgba(10, 18, 34, 0.92)',
		borderColor: 'rgba(34, 211, 238, 0.35)',
		borderWidth: 1,
		textStyle: { color: '#c7d2e5' },
	};
}

/** 暗色图例片段 */
export function techDarkLegend() {
	return {
		textStyle: { color: '#8fa2c2' },
		icon: 'circle',
	};
}

/**
 * 暗色坐标轴片段
 * @param type 'category' | 'value'
 */
export function techDarkAxis(type: 'category' | 'value' = 'value') {
	const base = {
		nameTextStyle: { color: '#74849f' },
		axisLabel: { color: '#8fa2c2' },
		axisLine: { lineStyle: { color: 'rgba(90, 165, 255, 0.2)' } },
		splitLine: {
			lineStyle: { type: 'dashed', color: 'rgba(90, 165, 255, 0.1)' },
		},
	};
	if (type === 'category') {
		// 类目轴通常不需要分隔线
		return { ...base, splitLine: { show: false }, boundaryGap: false };
	}
	return { ...base, axisLine: { show: false } };
}

/**
 * 生成一条「发光渐变面积线」系列的样式片段
 * @param color 主色（十六进制）
 */
export function techGlowLineStyle(color: string) {
	return {
		smooth: true,
		showSymbol: false,
		lineStyle: {
			width: 2.5,
			color,
			shadowColor: color,
			shadowBlur: 12,
		},
		itemStyle: { color },
	};
}

/** 一次性返回基础暗色 option 片段（可与业务 option 合并） */
export function techDarkChartBase() {
	return {
		color: techChartPalette,
		textStyle: { color: '#c7d2e5' },
		tooltip: techDarkTooltip(),
		legend: techDarkLegend(),
	};
}
