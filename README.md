# cu-admin

操作系统管理平台

## 本地备份 worker 与维护恢复

在部署主机上安装 Python 依赖及系统服务后，确认 `os.env` 包含正确的
`BACKUP_RESTORE_SERVICES`（至少 `cu-cockpit.service`，并列出该主机已安装的全部
`cu-cockpit-metrics.*`、`cu-cockpit-inspection.*`、`cu-cockpit-backup.*` 单元）。
该名单必须与维护时实际存在的 writer 单元一致；不完整时恢复会拒绝执行。
默认备份根为应用目录下的 `var/backups`；可在 `os.env` 中用绝对路径 `BACKUP_ROOT`
指定。备份包含默认 SQLite 数据库及已注册且存在的 Chrony 配置；缺少 Chrony 时
不能创建符合该部署目标的备份，worker 会报错，不会跳过配置。

在目标机上以 root 执行以下命令（将 `/opt/cu-cockpit` 替换为实际 `APP_DIR`）：

```bash
cd /opt/cu-cockpit
set -a; . ./os.env; set +a
venv/bin/python manage.py backup_center init
APP_DIR=/opt/cu-cockpit bash packaging/rpm/install_backup_timer.sh
systemctl status cu-cockpit-backup.timer
```

`init` 显式建立私有备份根 (0700)、元数据/索引/默认关闭的日程 (0600)，再次执行不
替换安装密钥或重置任务/日程。版本不匹配时不会自动迁移；确认已有版本后，显式执行
`venv/bin/python manage.py backup_center upgrade-version --from-version OLD_VERSION`，
只更新版本、保留安装身份与密钥。更新版本前须核对归档兼容性。
安装器仅部署并启用每分钟检查的 timer，不执行 `init`、不安装网络依赖。
可用 `SYSTEMD_UNIT_DIR` 指定测试目录并设置 `SKIP_SYSTEMCTL=true` 只渲染文件。

在页面启用日程或创建任务后，timer 运行
`manage.py backup_center run-scheduled`（先排当日任务，再处理一个排队任务）；
也可在 SSH 终端以 root 执行 `venv/bin/python manage.py backup_center run-pending`。
两者输出实际处理的任务 JSON（无任务为 `null`），任务失败时退出非零。
若任务索引满且没有可回收的已完成备份，定时 worker 仍会先处理一个排队任务，
下一轮再尝试排入当日日程；无容量时不会提前标记该日程为已排队。

恢复必须在**独立 SSH 维护进程**中以 root 执行，不能在 Web 请求或备份 timer
的服务进程中运行。先通过管理页面完成预检及 token 确认，再在确认有效期内执行：

```bash
cd /opt/cu-cockpit
set -a; . ./os.env; set +a
venv/bin/python manage.py backup_center restore TASK_ID --confirm-maintenance
```

页面的 `awaiting_maintenance` 仅表示等待上述命令，并非恢复完成。命令只接受任务
ID，不接受自定义数据库或配置路径；执行前验证任务、归档、版本及服务名单。恢复时
停用本应用的 timer 和 writer，保留恢复前安全备份，并把结果写入任务状态。若返回
`manual_recovery_required`，不要盲目重启服务，先按任务记录的安全归档人工排查。
失败清理会尝试停止全部已登记的 writer；若无法确认某个单元已停，任务错误会列出该
单元，且不会执行数据回滚。服务重启失败时清理后保持停服，等待人工恢复。

## 备份导入部署限制

`POST /api/system/backups/import` 在 Django 解析 multipart 前检查 session 管理员身份和
`Content-Length`（归档最大 256 MiB，整个请求最大 257 MiB），通过后仍需正常通过 CSRF。
反向代理可能先缓冲请求；当前 Nginx 模板尚未设置该路径的 `client_max_body_size` 或
代理侧身份准入。后续 installer 配置 Nginx 时应为该路径设置不超过 257m 的请求体上限，
并在需要避免匿名上传占用代理临时磁盘时增加代理侧准入；不能把 Django 的限制当作
Nginx 已经拒绝上传的保证。

## 备份测试运行环境

部署主机只需 Python 依赖和已构建的前端 dist，不必安装 Node.js 或前端编译依赖。
在仓库根目录运行备份和巡检相关后端测试（将 `venv/bin/python` 替换为本机已验证的虚拟环境解释器）：

```bash
venv/bin/python manage.py test \
	tests.test_backup_restore_center tests.test_backup_jobs tests.test_backup_api \
	tests.test_backup_commands tests.test_inspection_center tests.test_inspection_jobs \
	tests.test_inspection_api --noinput
```

全仓库旧测试的已知基线失败单独处理，不属于上述功能测试门槛。

其中仅备份页面请求体到严格日程 API 的跨 runtime 集成测试需要 Node.js、
`cu-cockpit-web/node_modules/typescript` 和 `cu-cockpit-web/node_modules/@vue/compiler-sfc`。
部署主机缺少这些工具时，该方法应报告 1 个 skip（附缺失原因），其余纯 Python
日程成功和 `next_run` 只读字段拒绝测试仍须执行；不要将 skip 计作跨 runtime 验证通过。
前端源码与依赖齐全的本地开发环境还须运行：

```bash
node --test tests/frontend/backup-workspace.test.cjs
```

本地后端测试中的跨 runtime 方法也必须实际通过；Node 脚本执行失败属于测试失败，
不应转为 skip。