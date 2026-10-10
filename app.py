import os
import json
import pandas as pd
import streamlit as st
import datetime
from fetcher import update_all_funds, STATUS_FILE, HISTORY_FILE

# 页面基础配置
st.set_page_config(
    page_title="小鸡观察基地",
    page_icon="🐣",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义苹果风格响应式 CSS 样式
st.markdown("""
<style>
    /* 全局苹果字体与柔和渲染 */
    html, body, [class*="css"], .stMarkdown {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", sans-serif !important;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    /* 容器边距柔和微调 (预留顶部工具栏安全距离，防止标题被遮挡) */
    .block-container {
        padding-top: 5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px !important;
    }
    @media screen and (max-width: 768px) {
        .block-container {
            padding-top: 4.2rem !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
        }
    }

    /* 苹果风头部组件 */
    .apple-header {
        margin-top: 6px;
        margin-bottom: 12px;
        padding-top: 6px;
    }
    .apple-title {
        font-size: 20px;
        font-weight: 600;
        color: #1d1d1f;
        letter-spacing: -0.015em;
        line-height: 1.4;
        margin-bottom: 6px;
    }
    @media screen and (min-width: 769px) {
        .apple-title {
            font-size: 25px;
        }
    }
    .apple-meta-bar {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        align-items: center;
    }
    .apple-pill {
        background: #f5f5f7;
        color: #86868b;
        font-size: 11px;
        padding: 3px 8px;
        border-radius: 12px;
        font-weight: 400;
    }

    /* 苹果小组件风格统计卡片 (紧凑精致，横向网格) */
    .apple-stats-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        margin: 12px 0 16px 0;
    }
    .apple-stat-card {
        background: #ffffff;
        border: 1px solid rgba(0, 0, 0, 0.06);
        border-radius: 12px;
        padding: 10px 12px;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02);
    }
    .stat-label {
        font-size: 11px;
        color: #86868b;
        font-weight: 500;
        margin-bottom: 3px;
        white-space: nowrap;
    }
    .stat-value {
        font-size: 19px;
        font-weight: 700;
        color: #1d1d1f;
        line-height: 1.2;
        letter-spacing: -0.02em;
    }
    .stat-unit {
        font-size: 12px;
        font-weight: 400;
        color: #86868b;
        margin-left: 2px;
    }
    .stat-sub {
        font-size: 11px;
        color: #86868b;
        margin-top: 3px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .text-green {
        color: #2e7d32;
    }

    /* 移动端卡片流苹果风 */
    .apple-fund-card {
        background: #ffffff;
        border: 1px solid rgba(0, 0, 0, 0.06);
        border-radius: 12px;
        padding: 12px 14px;
        margin-bottom: 9px;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02);
    }
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 7px;
        gap: 8px;
    }
    .fund-name {
        font-size: 14px;
        font-weight: 600;
        color: #1d1d1f;
        line-height: 1.35;
        word-break: break-all;
    }
    .fund-code {
        color: #0071e3;
        font-weight: 600;
        margin-right: 4px;
    }
    .badge {
        padding: 2px 7px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        white-space: nowrap;
        flex-shrink: 0;
    }
    .card-meta-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: #48484a;
        font-size: 12px;
        margin-bottom: 6px;
    }
    .card-metrics-row {
        display: flex;
        gap: 6px;
        margin-bottom: 6px;
    }
    .metric-tag {
        font-size: 11px;
        padding: 2px 7px;
        border-radius: 6px;
        display: inline-flex;
        align-items: center;
        gap: 2px;
    }
    .tag-blue {
        background: #f0f6ff;
        color: #0066cc;
    }
    .tag-green {
        background: #e8f5e9;
        color: #2e7d32;
    }
    .tag-orange {
        background: #fff8e1;
        color: #b78103;
    }
    .tag-red {
        background: #fff2f2;
        color: #d32f2f;
    }
    .tag-gray {
        background: #f5f5f7;
        color: #48484a;
    }
    .card-footer-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: #86868b;
        font-size: 11px;
        margin-top: 4px;
        border-top: 1px dashed #f0f0f2;
        padding-top: 6px;
    }
    .apple-link {
        color: #0071e3 !important;
        text-decoration: none;
        font-size: 11px;
        font-weight: 500;
    }

    .top-fund-item {
        background: #ffffff;
        border: 1px solid rgba(0, 0, 0, 0.06);
        border-radius: 10px;
        padding: 9px 12px;
        margin-bottom: 7px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
    }

    /* 电脑端苹果风精简表格 */
    .apple-desktop-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        background: #ffffff;
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 12px;
        overflow: hidden;
        font-size: 12px;
        margin-top: 8px;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02);
    }
    .apple-desktop-table th {
        background-color: #fafafc;
        color: #86868b;
        font-weight: 600;
        text-align: left;
        padding: 9px 10px;
        border-bottom: 1px solid rgba(0, 0, 0, 0.06);
        white-space: nowrap;
        font-size: 11px;
    }
    .apple-desktop-table td {
        padding: 8px 10px;
        border-bottom: 1px solid rgba(0, 0, 0, 0.04);
        color: #1d1d1f;
        vertical-align: middle;
        line-height: 1.4;
    }
    .apple-desktop-table tr:last-child td {
        border-bottom: none;
    }
    .apple-desktop-table tr:hover td {
        background-color: #fbfbfd;
    }
    .col-code {
        font-family: -apple-system-monospaced, "SF Pro Text", monospace;
        color: #0071e3;
        font-weight: 600;
        white-space: nowrap;
    }
    .col-name {
        font-weight: 500;
        white-space: normal;
        word-break: break-all;
    }
    .col-index {
        white-space: nowrap;
    }
    .col-limit {
        white-space: nowrap;
        font-weight: 600;
        color: #2e7d32;
    }
    .col-error {
        white-space: nowrap;
        font-weight: 500;
    }
    .badge-ms-green {
        background: #e8f5e9;
        color: #2e7d32;
        border: 1px solid rgba(46, 125, 50, 0.2);
        padding: 1px 6px;
        border-radius: 6px;
        font-size: 10px;
        font-weight: 600;
    }
    .badge-ms-orange {
        background: #fff8e1;
        color: #b78103;
        border: 1px solid rgba(183, 129, 3, 0.2);
        padding: 1px 6px;
        border-radius: 6px;
        font-size: 10px;
        font-weight: 600;
    }
    .badge-ms-red {
        background: #ffebee;
        color: #c62828;
        border: 1px solid rgba(198, 40, 40, 0.2);
        padding: 1px 6px;
        border-radius: 6px;
        font-size: 10px;
        font-weight: 600;
    }
    .badge-ms-gray {
        background: #f5f5f7;
        color: #86868b;
        padding: 1px 6px;
        border-radius: 6px;
        font-size: 10px;
    }
    .col-return {
        white-space: nowrap;
        color: #d32f2f;
        font-weight: 500;
    }
    .col-fee {
        white-space: nowrap;
        font-weight: 500;
        color: #1d1d1f;
    }
    .badge-fee-low {
        background: #e8f5e9;
        color: #2e7d32;
        border: 1px solid rgba(46, 125, 50, 0.2);
        padding: 1px 5px;
        border-radius: 6px;
        font-size: 10px;
        font-weight: 600;
    }
    .badge-fee-mid {
        background: #f5f5f7;
        color: #6e6e73;
        padding: 1px 5px;
        border-radius: 6px;
        font-size: 10px;
    }
    .badge-fee-high {
        background: #fff3e0;
        color: #e65100;
        border: 1px solid rgba(230, 81, 0, 0.2);
        padding: 1px 5px;
        border-radius: 6px;
        font-size: 10px;
        font-weight: 600;
    }
    .col-min {
        white-space: nowrap;
        color: #86868b;
    }
    .col-channel {
        white-space: normal;
        word-break: break-word;
        color: #c45100;
        font-size: 11px;
        line-height: 1.35;
    }

    /* 默认电脑大屏：显示表格，隐藏手机卡片流 */
    .desktop-table-view {
        display: block !important;
    }
    .mobile-cards-view {
        display: none !important;
    }

    /* 移动端屏幕 (宽度 <= 768px)：自动隐藏大表格，自动展示舒适卡片流 */
    @media screen and (max-width: 768px) {
        .desktop-table-view {
            display: none !important;
        }
        .mobile-cards-view {
            display: block !important;
        }
    }
</style>
""", unsafe_allow_html=True)


def load_data():
    if not os.path.exists(STATUS_FILE):
        update_all_funds()

    with open(STATUS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

    return data, history


# 侧边栏控制
st.sidebar.title("🔍 筛选与控制")

# 手动刷新数据
if st.sidebar.button("🔄 立即在线刷新数据", use_container_width=True):
    with st.spinner("正在从公开接口实时抓取最新限额数据..."):
        try:
            update_all_funds()
            st.sidebar.success("刷新成功！")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"刷新失败: {e}")

data, history = load_data()
funds_list = data.get("funds", [])
updated_at = data.get("updated_at", "--")

df = pd.DataFrame(funds_list)

# 确保 can_buy 字段存在（兼容老数据）
if "can_buy" not in df.columns:
    df["can_buy"] = df["limit_amount"] > 0

# 侧边栏：核心逻辑筛选（能买 / 不能买）
buy_filter_options = [
    "🟢 仅看今日能买 (默认)",
    "🟢 仅看能买且不限额 (大额充足)",
    "🟡 仅看限额基金 (额度紧张)",
    "⚪ 查看全部标的 (含已暂停)"
]
selected_buy_filter = st.sidebar.radio("⚡ 购买状态筛选", buy_filter_options, index=0)

# 指数类型筛选
index_options = ["全部"] + sorted(list(df["index"].unique()))
selected_index = st.sidebar.selectbox("🎯 标的指数", index_options)

# 份额类别筛选
share_options = ["全部", "仅看A类", "仅看C类"]
selected_share = st.sidebar.selectbox("🏷️ 份额类别", share_options)

# 基金公司筛选
company_options = ["全部"] + sorted([c for c in df["company"].unique() if c != "--"])
selected_company = st.sidebar.selectbox("🏢 基金公司", company_options)

# 模糊搜索
search_query = st.sidebar.text_input("🔎 搜索基金代码 / 名称", "")

# 排序方式
sort_options = ["默认 (限额优先)", "综合年费率最低 (省钱优先)", "近1年收益率最高"]
selected_sort = st.sidebar.selectbox("📊 列表排序依据", sort_options, index=0)

# 数据过滤
filtered_df = df.copy()

if selected_buy_filter == "🟢 仅看今日能买 (默认)":
    filtered_df = filtered_df[filtered_df["limit_amount"] > 0]
elif selected_buy_filter == "🟢 仅看能买且不限额 (大额充足)":
    filtered_df = filtered_df[filtered_df["limit_amount"] >= 999999999]
elif selected_buy_filter == "🟡 仅看限额基金 (额度紧张)":
    filtered_df = filtered_df[(filtered_df["limit_amount"] > 0) & (filtered_df["limit_amount"] < 999999999)]

if selected_index != "全部":
    filtered_df = filtered_df[filtered_df["index"] == selected_index]

if selected_share == "仅看A类":
    filtered_df = filtered_df[filtered_df["share_type"] == "A类"]
elif selected_share == "仅看C类":
    filtered_df = filtered_df[filtered_df["share_type"] == "C类"]

if selected_company != "全部":
    filtered_df = filtered_df[filtered_df["company"] == selected_company]

if search_query:
    q = search_query.strip().lower()
    filtered_df = filtered_df[
        filtered_df["code"].str.lower().str.contains(q) |
        filtered_df["name"].str.lower().str.contains(q) |
        filtered_df["company"].str.lower().str.contains(q)
    ]

# 执行排序
if selected_sort == "综合年费率最低 (省钱优先)":
    if "total_fee_num" in filtered_df.columns:
        filtered_df = filtered_df.sort_values(by="total_fee_num", ascending=True)
elif selected_sort == "近1年收益率最高":
    filtered_df["_syl_num"] = pd.to_numeric(filtered_df["syl_1y"], errors="coerce").fillna(-999)
    filtered_df = filtered_df.sort_values(by="_syl_num", ascending=False)

# 主页面渲染 (苹果风格设计：精致字号、圆角卡片、柔和间距)
total_funds = len(df)
can_buy_funds = len(df[df["limit_amount"] > 0])
sp500_can_buy = len(df[(df["index"] == "标普500") & (df["limit_amount"] > 0)])
ndx_can_buy = len(df[(df["index"].isin(["纳斯达克100", "纳斯达克科技"])) & (df["limit_amount"] > 0)])
can_buy_pct = int(round(can_buy_funds / total_funds * 100)) if total_funds > 0 else 0

header_html = f"""<div class="apple-header">
<div class="apple-title">小鸡观察基地</div>
<div class="apple-meta-bar">
<span class="apple-pill">🕒 更新时间: {updated_at}</span>
<span class="apple-pill">💡 专注美股被动QDII</span>
<span class="apple-pill">🎯 已自动过滤不可买标的</span>
</div>
</div>
<div class="apple-stats-grid">
<div class="apple-stat-card">
<div class="stat-label">今日可买基金</div>
<div class="stat-value text-green">{can_buy_funds} <span class="stat-unit">只</span></div>
<div class="stat-sub">{can_buy_pct}% 标的开放申购</div>
</div>
<div class="apple-stat-card">
<div class="stat-label">标普500 可买</div>
<div class="stat-value">{sp500_can_buy} <span class="stat-unit">只</span></div>
<div class="stat-sub">支持定投或大额</div>
</div>
<div class="apple-stat-card">
<div class="stat-label">纳斯达克100 可买</div>
<div class="stat-value">{ndx_can_buy} <span class="stat-unit">只</span></div>
<div class="stat-sub">含直销渠道放水</div>
</div>
</div>"""

st.markdown(header_html, unsafe_allow_html=True)

# Tab 布局
tab1, tab2, tab3 = st.tabs(["🏆 今日额度最高 TOP 榜", "🟢 额度监控列表", "📜 额度变动历史"])

with tab1:
    st.caption("🏆 今日各指数可买标的中单日限额最高的前 10 只份额")
    
    top_funds = df[df["limit_amount"] > 0].sort_values(by="limit_amount", ascending=False)
    
    col_l, col_r = st.columns(2)
    
    def render_top_list(funds_subset):
        items_html = []
        for _, r in funds_subset.iterrows():
            amt = r["limit_amount"]
            if amt >= 999999999:
                amt_str = "不限额"
                amt_color = "#2e7d32"
                amt_bg = "#e8f5e9"
            elif amt >= 10000:
                amt_str = f"限额 {amt/10000:.1f}万/日"
                amt_color = "#b78103"
                amt_bg = "#fff8e1"
            else:
                amt_str = f"限额 {int(amt):,}元/日"
                amt_color = "#b78103"
                amt_bg = "#fff8e1"

            note_badge = f'<span style="color:#e65100; font-weight:500;"> · {r["channel_note"]}</span>' if r.get('channel_note') else ''

            item = (
                f'<div class="top-fund-item">'
                f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                f'<span style="font-size:13px; font-weight:600; color:#1d1d1f;"><span style="color:#0071e3;">{r["code"]}</span> {r["name"]}</span>'
                f'<span style="font-size:11px; font-weight:600; color:{amt_color}; background:{amt_bg}; padding:2px 7px; border-radius:10px; white-space:nowrap; margin-left:6px;">{amt_str}</span>'
                f'</div>'
                f'<div style="font-size:11px; color:#86868b; margin-top:3px;">'
                f'<span>起购: {r.get("min_buy", "10")}元</span>'
                f'{note_badge}'
                f'</div>'
                f'</div>'
            )
            items_html.append(item)
        return "".join(items_html)

    with col_l:
        st.markdown('<div style="font-size:13px; font-weight:600; color:#1d1d1f; margin:4px 0 8px 0;">🟢 标普500 可用额度最高 TOP 10</div>', unsafe_allow_html=True)
        sp500_top = top_funds[top_funds["index"] == "标普500"].head(10)
        if len(sp500_top) > 0:
            st.markdown(render_top_list(sp500_top), unsafe_allow_html=True)
        else:
            st.info("标普500当前暂无可申购份额")

    with col_r:
        st.markdown('<div style="font-size:13px; font-weight:600; color:#1d1d1f; margin:4px 0 8px 0;">🔵 纳斯达克100 可用额度最高 TOP 10</div>', unsafe_allow_html=True)
        nasdaq_top = top_funds[top_funds["index"].isin(["纳斯达克100", "纳斯达克科技"])].head(10)
        if len(nasdaq_top) > 0:
            st.markdown(render_top_list(nasdaq_top), unsafe_allow_html=True)
        else:
            st.info("纳斯达克相关基金当前暂无可申购份额")

with tab2:
    st.caption(f"当前显示 **{len(filtered_df)}** 只可买基金（已自动过滤暂停申购标的，可在左侧切换）")

    with st.expander("💡 什么是「近1年相对基准」与「综合年费率」？怎么看？", expanded=False):
        st.markdown("""<div style="font-size:12px; line-height:1.6; color:#48484a; padding:4px 0;">
<b>核心指标解读：</b><br>
• <span class="badge-ms-green">极佳 / 跑赢</span> <b>相对基准跑输 &lt; 1.0% 或跑赢</b>：复制精度极高，超额摩擦损耗极小，属于<b>首选优质标的</b>。<br>
• <span class="badge-ms-orange">正常</span> <b>跑输 1.0% ~ 2.0%</b>：处于正常的 QDII 外汇与运营摩擦区间。<br>
• <span class="badge-ms-red">偏大</span> <b>跑输 &gt; 2.0%</b>：跟踪磨损较大，长期持有易被吃掉收益，需谨慎。<br>
• <span class="badge-fee-low">极省</span> <b>综合年费率 &le; 0.35%</b>：管理费+托管费极低，长期定投省出大量收益。<br>
• <span class="badge-fee-mid">常规</span> <b>综合年费率 0.35% ~ 0.85%</b>：主流公募指数基金常规费率。<br>
• <span class="badge-fee-high">偏高</span> <b>综合年费率 &gt; 0.85%</b>：通常为 C 类（含销售服务费）或老一代高费率 QDII。
</div>""", unsafe_allow_html=True)

    # 格式化展示数据
    display_df = filtered_df.copy()
    
    def format_limit_text(amt):
        if amt >= 999999999:
            return "不限额 (充足)"
        elif amt == 0:
            return "0 元 (不可买)"
        elif amt >= 10000:
            return f"{amt/10000:.1f} 万元/日"
        else:
            return f"{int(amt):,} 元/日"

    display_df["单日限额"] = display_df["limit_amount"].apply(format_limit_text)
    display_df["近1年收益"] = display_df.get("syl_1y", pd.Series(["--"] * len(display_df))).apply(lambda x: f"{x}%" if str(x) != "--" else "--")
    display_df["直销渠道情报"] = display_df["channel_note"].apply(lambda x: x if x else "--")
    display_df["近1年相对基准"] = display_df.apply(lambda r: f"{r.get('ms_diff', '--')} ({r.get('ms_eval_label', '--')})" if r.get('ms_diff') not in [None, "--"] else "次新标的", axis=1)

    table_view = display_df[[
        "code", "name", "index", "单日限额", "近1年相对基准", "近1年收益", "total_fee", "直销渠道情报"
    ]].rename(columns={
        "code": "代码",
        "name": "基金名称",
        "index": "标的指数",
        "total_fee": "综合年费率"
    })

    # 1. 移动端自适应卡片流 (手机屏幕下自动显示，电脑大屏下由 CSS 自动隐藏)
    cards_html_list = []
    for _, row in display_df.iterrows():
        note_html = (
            f'<div style="margin-top:6px; background:#fff9f0; border-left:3px solid #ff9500; border-radius:4px; padding:4px 8px; color:#c45100; font-size:11px; font-weight:500;">{row["channel_note"]}</div>'
            if row["channel_note"] else ""
        )

        diff = row.get("ms_diff", "--")
        eval_label = row.get("ms_eval_label", "--")
        badge_type = row.get("ms_badge_type", "gray")
        if badge_type == "green":
            ms_card_tag = f'<span class="metric-tag tag-green">🎯 基准 <b>{diff} ({eval_label})</b></span>'
        elif badge_type == "orange":
            ms_card_tag = f'<span class="metric-tag tag-orange">🎯 基准 <b>{diff} ({eval_label})</b></span>'
        elif badge_type == "red":
            ms_card_tag = f'<span class="metric-tag tag-red">🎯 基准 <b>{diff} ({eval_label})</b></span>'
        else:
            ms_card_tag = f'<span class="metric-tag tag-gray">🎯 基准 <b>次新</b></span>'

        total_fee = row.get("total_fee", "--")
        fee_badge = row.get("fee_badge", "normal")
        if total_fee == "--":
            fee_card_tag = '<span class="metric-tag tag-gray">💸 年费 --</span>'
        elif fee_badge == "low":
            fee_card_tag = f'<span class="metric-tag tag-green">💸 年费 <b>{total_fee} (省)</b></span>'
        elif fee_badge == "high":
            fee_card_tag = f'<span class="metric-tag tag-orange">💸 年费 <b>{total_fee}</b></span>'
        else:
            fee_card_tag = f'<span class="metric-tag tag-gray">💸 年费 <b>{total_fee}</b></span>'

        card = (
            f'<div class="apple-fund-card">'
            f'<div class="card-header">'
            f'<div class="fund-name"><span class="fund-code">{row["code"]}</span> {row["name"]}</div>'
            f'</div>'
            f'<div class="card-meta-row">'
            f'<span>🎯 标的: <b>{row["index"]}</b></span>'
            f'<span>💰 单日限额: <b style="color:#2e7d32; font-size:13px;">{row["单日限额"]}</b></span>'
            f'</div>'
            f'<div class="card-metrics-row">'
            f'{ms_card_tag}'
            f'<span class="metric-tag tag-red">📈 近1年 <b>{row["近1年收益"]}</b></span>'
            f'{fee_card_tag}'
            f'</div>'
            f'{note_html}'
            f'</div>'
        )
        cards_html_list.append(card)

    mobile_container_html = f'<div class="mobile-cards-view">{"".join(cards_html_list)}</div>'
    st.markdown(mobile_container_html, unsafe_allow_html=True)

    # 2. 电脑端数据表格 (纯正苹果风设计：支持任意列自动换行、小字号、无横向滚动条)
    table_rows = []
    for _, row in display_df.iterrows():
        channel_content = (
            f'<div class="col-channel">💡 {row["channel_note"].replace("💡 ", "")}</div>'
            if row["channel_note"] else '<span style="color:#c7c7cc;">--</span>'
        )

        diff = row.get("ms_diff", "--")
        eval_label = row.get("ms_eval_label", "--")
        badge_type = row.get("ms_badge_type", "gray")
        fund_1y = row.get("ms_fund_1y", "--")
        bm_1y = row.get("ms_benchmark_1y", "--")
        
        if fund_1y != "--" and bm_1y != "--":
            tooltip = f"近1年: 基金 {fund_1y} vs 指数基准 {bm_1y}"
        else:
            tooltip = "成立不足1年暂无对比"
            
        if diff == "--" or not diff:
            ms_cell_html = f'<span class="badge-ms-gray" title="{tooltip}">次新标的</span>'
        else:
            badge_cls = "badge-ms-green" if badge_type == "green" else ("badge-ms-orange" if badge_type == "orange" else ("badge-ms-red" if badge_type == "red" else "badge-ms-gray"))
            ms_cell_html = f'<div title="{tooltip}" style="display:inline-flex; align-items:center; gap:4px; cursor:help;"><span>{diff}</span><span class="{badge_cls}">{eval_label}</span></div>'

        total_fee = row.get("total_fee", "--")
        mgmt_fee = row.get("mgmt_fee", "--")
        cust_fee = row.get("custody_fee", "--")
        serv_fee = row.get("service_fee", "--")
        fee_badge = row.get("fee_badge", "normal")
        fee_tooltip = f"管理费: {mgmt_fee} | 托管费: {cust_fee} | 销售服务费: {serv_fee}"
        
        if total_fee == "--":
            fee_cell_html = '<span style="color:#c7c7cc;">--</span>'
        else:
            badge_cls = "badge-fee-low" if fee_badge == "low" else ("badge-fee-high" if fee_badge == "high" else "badge-fee-mid")
            badge_lbl = "极省" if fee_badge == "low" else ("偏高" if fee_badge == "high" else "常规")
            fee_cell_html = f'<div title="{fee_tooltip}" style="display:inline-flex; align-items:center; gap:4px; cursor:help;"><span>{total_fee}</span><span class="{badge_cls}">{badge_lbl}</span></div>'

        tr = (
            f'<tr>'
            f'<td class="col-code">{row["code"]}</td>'
            f'<td class="col-name">{row["name"]}</td>'
            f'<td class="col-index">{row["index"]}</td>'
            f'<td class="col-limit">{row["单日限额"]}</td>'
            f'<td class="col-error">{ms_cell_html}</td>'
            f'<td class="col-return">{row["近1年收益"]}</td>'
            f'<td class="col-fee">{fee_cell_html}</td>'
            f'<td>{channel_content}</td>'
            f'</tr>'
        )
        table_rows.append(tr)

    desktop_table_html = (
        f'<div class="desktop-table-view">'
        f'<table class="apple-desktop-table">'
        f'<thead><tr>'
        f'<th style="width:70px;">代码</th>'
        f'<th>基金名称</th>'
        f'<th style="width:85px;">标的指数</th>'
        f'<th style="width:105px;">单日最高限额</th>'
        f'<th style="min-width:135px;">近1年相对基准 (晨星)</th>'
        f'<th style="width:80px;">近1年收益</th>'
        f'<th style="width:95px;">综合年费率</th>'
        f'<th style="min-width:180px;">💡 直销渠道情报</th>'
        f'</tr></thead>'
        f'<tbody>{"".join(table_rows)}</tbody>'
        f'</table>'
        f'</div>'
    )
    st.markdown(desktop_table_html, unsafe_allow_html=True)

    # 导出 CSV
    csv_data = table_view.to_csv(index=False).encode('utf_8_sig')
    st.download_button(
        label="📥 导出当前筛选表格为 CSV",
        data=csv_data,
        file_name=f"qdii_quota_{datetime.date.today()}.csv",
        mime="text/csv"
    )

with tab3:
    st.caption("📜 自动监测每日各标的限购额度升降与状态变更明细")
    if history:
        hist_df = pd.DataFrame(history)
        
        def format_hist_change(r):
            old_l = r.get("old_limit", 0)
            new_l = r.get("new_limit", 0)
            old_str = "不限额" if old_l >= 999999999 else (f"{int(old_l):,}元/日" if old_l > 0 else "暂停申购")
            new_str = "不限额" if new_l >= 999999999 else (f"{int(new_l):,}元/日" if new_l > 0 else "暂停申购")
            if new_l > old_l:
                return f"🟢 放宽：从【{old_str}】上调至【{new_str}】"
            elif new_l < old_l:
                return f"🔴 收紧：从【{old_str}】下调至【{new_str}】"
            else:
                return f"⚪ 状态更新：【{r.get('old_sgzt', '')}】➔【{r.get('new_sgzt', '')}】"

        hist_df["变动说明"] = hist_df.apply(format_hist_change, axis=1)
        st.dataframe(
            hist_df[["time", "code", "name", "index", "变动说明"]].rename(columns={
                "time": "变动时间",
                "code": "代码",
                "name": "基金名称",
                "index": "标的指数"
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("暂无额度变动记录（历史已重置。系统每日自动巡检，一旦基金公司放宽或收紧限额，将第一时间在此清晰记录）。")


