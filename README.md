# GLaDOS GitHub Actions 自动签到

把这个目录里的文件上传到你的 GitHub 仓库后，配置一个仓库 Secret 就可以自动签到。

## 需要配置的 Secret

名称：

```text
GLADOS_ACCOUNTS
```

内容格式：

```text
koa:sess=xxx; koa:sess.sig=xxx
koa:sess=yyy; koa:sess.sig=yyy
```

说明：

- 一行一个账号
- 每行只填一个完整 Cookie
- 典型格式是 `koa:sess=...; koa:sess.sig=...`
- 多账号直接换行

## 工作流说明

- 文件位置：`.github/workflows/glados-checkin.yml`
- 支持手动运行
- 支持定时运行
- 当前 cron 为 `5 16 * * *`，对应北京时间每天 `00:05`

如果你想改运行时间，修改工作流里的 cron 即可。
