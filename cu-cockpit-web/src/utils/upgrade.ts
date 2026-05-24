import axios from 'axios';
import * as process from 'process';
import { Local, Session } from '/@/utils/storage';
import { ElNotification } from 'element-plus';
import fs from 'fs';

// 是否显示升级提示信息框
const IS_SHOW_UPGRADE_SESSION_KEY = 'isShowUpgrade';
const VERSION_KEY = 'VERSION';
const VERSION_FILE_NAME = 'version-build';

const META_ENV = import.meta.env;

export function showUpgrade() {
	const isShowUpgrade = Session.get(IS_SHOW_UPGRADE_SESSION_KEY) ?? false;
	if (isShowUpgrade) {
		Session.remove(IS_SHOW_UPGRADE_SESSION_KEY);
		// ElNotification({
		// 	title: '新版本升级',
		// 	message: '检测到系统新版本，正在更新中！不用担心，更新很快的哦！',
		// 	type: 'success',
		// 	duration: 5000,
		// });
	}
}
