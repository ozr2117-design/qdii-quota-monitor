# ⏱️ Cloudflare Workers 定时调度器与全局触发准则

## 📌 全局规范准则 (Global Architecture Rule)
**【准则声明】**：  
GitHub Actions 原生自带的 `schedule (cron)` 存在全球队列排队延迟（经常延迟 15~40 分钟，高峰期偶发跳过）。  
对于任何**高时效性业务（如基金限额抢购、实时盯盘、行情同步）**，一律采用 **Cloudflare Workers Cron Triggers** 作为**秒级准时推动器**，外部调用 GitHub `workflow_dispatch` 接口触发，确保时钟精度达到毫秒级。

---

## 🚀 已部署的 Cloudflare 调度器详情

- **Worker 名称**：`github-action-cron-dispatcher`
- **Cloudflare 账号**：`006960eb51dac6fb10e8b8b253083c1f`
- **专属公网触发域名**：  
  `https://github-action-cron-dispatcher.ozr2117.workers.dev`
- **手动 Webhook 接口**：  
  `GET https://github-action-cron-dispatcher.ozr2117.workers.dev/trigger`（任何外部服务访问此链接，即可在 3 秒内直接唤醒 GitHub Actions 更新）

---

## 🕒 定时 Cron 触发时间表 (交易日 UTC+8)

| 触发时间 | UTC 表达式 | 业务目的 |
| :---: | :---: | :--- |
| **08:45** | `45 0 * * 1-5` | 早盘前确认昨夜公告与直销系统重置状态 |
| **10:30** | `30 2 * * 1-5` | 盘中巡检早盘额度是否被抢空变灰 |
| **14:00** | `0 6 * * 1-5` | 15:00 申购截单前终局决策窗口 |
| **16:30** | `30 8 * * 1-5` | 盘后清算最终状态 |
| **20:30** | `30 12 * * 1-5` | 晚间各大公募公告高峰 |
