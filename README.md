# 📈 中国场外标普500 / 纳斯达克100被动基金额度监控

本项目专为国内投资者打造，用于**全自动监控全市场场外标普500与纳斯达克100（QDII指数基金/ETF联接）的每日申购限额与状态**。

- 💻 **100% 永久免费**：代码托管在 GitHub，Web 界面免费运行于 Streamlit Community Cloud。
- 🤖 **全自动免运维**：内置 GitHub Actions 定时任务，交易日自动更新最新限额并同步页面。
- ⚡ **交互功能全面**：支持指数分类筛选、额度区间筛选、模糊搜索、可用额度排行榜、变动历史与数据一键导出。

---

## 🚀 3 步部署上线指南

### 第一步：将代码推送到你的 GitHub 仓库

1. 打开 [GitHub](https://github.com/) 并登录，点击右上角 **New repository** 创建一个新仓库（例如命名为 `fund-quota-monitor`），选择 **Public**。
2. 在本机此项目文件夹终端中运行以下命令（将 `<你的仓库地址>` 替换为你在 GitHub 上创建的仓库地址）：

```bash
git init
git add .
git commit -m "feat: init fund quota monitor"
git branch -M main
git remote add origin <你的仓库地址>
git push -u origin main
```

---

### 第二步：开启 GitHub Actions 自动更新权限

为了让 GitHub Actions 每天自动更新数据并推回仓库：
1. 在你的 GitHub 仓库页面，点击 **Settings** -> 左侧 **Actions** -> **General**。
2. 滚动到底部的 **Workflow permissions**，选中 **Read and write permissions**。
3. 点击 **Save** 保存。

---

### 第三步：在 Streamlit Cloud 一键上线

1. 打开 [share.streamlit.io](https://share.streamlit.io/)，使用你的 GitHub 账号直接登录。
2. 点击右上角 **Create app** -> **Deploy a public app from GitHub**。
3. 填入参数（极为简单）：
   - **Repository**：选择你刚刚创建的仓库（如 `yourname/fund-quota-monitor`）
   - **Branch**：`main`
   - **Main file path**：`app.py`
4. 点击 **Deploy!** 部署按钮。
5. 等待约 1~2 分钟，你的专属监控网页就上线了！Streamlit 会提供一个永久公开的免费网址（如 `https://fund-quota-monitor.streamlit.app`）。

---

## ⚙️ 本地调试运行（可选）

如果你想在本地先预览网页效果：

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动 Streamlit
streamlit run app.py
```

浏览器会自动打开 `http://localhost:8501`。

---

## 🛠️ 核心文件说明

- `app.py`：Streamlit Web 端主程序，负责交互式展示与数据筛选。
- `fetcher.py`：全市场场外美股被动指数基金数据抓取引擎，包含多线程请求与额度解析器。
- `funds.json`：监控的场外标普500/纳指被动指数基金池。
- `data/fund_status.json`：抓取后的最新限额与净值数据快照。
- `.github/workflows/update.yml`：GitHub Actions 自动化定时任务配置（交易日早盘、盘后、晚间自动更新）。
