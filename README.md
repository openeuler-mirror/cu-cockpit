# cu-admin

操作系统管理平台

## 备份导入部署限制

`POST /api/system/backups/import` 在 Django 解析 multipart 前检查 session 管理员身份和
`Content-Length`（归档最大 256 MiB，整个请求最大 257 MiB），通过后仍需正常通过 CSRF。
反向代理可能先缓冲请求；当前 Nginx 模板尚未设置该路径的 `client_max_body_size` 或
代理侧身份准入。后续 installer 配置 Nginx 时应为该路径设置不超过 257m 的请求体上限，
并在需要避免匿名上传占用代理临时磁盘时增加代理侧准入；不能把 Django 的限制当作
Nginx 已经拒绝上传的保证。