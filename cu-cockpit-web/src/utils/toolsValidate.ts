/**
 * 2020.11.29 lyt 整理
 * 工具类集合，适用于平时开发
 * 新增多行注释信息，鼠标放到方法名即可查看
 */

/**
 * 验证百分比（不可以小数）
 * @param val 当前值字符串
 * @returns 返回处理后的字符串
 */
export function verifyNumberPercentage(val: string): string {
	// 匹配空格
	let v = val.replace(/(^\s*)|(\s*$)/g, '');
	// 只能是数字和小数点，不能是其他输入
	v = v.replace(/[^\d]/g, '');
	// 不能以0开始
	v = v.replace(/^0/g, '');
	// 数字超过100，赋值成最大值100
	v = v.replace(/^[1-9]\d\d{1,3}$/, '100');
	// 返回结果
	return v;
}
