import os
import json
import pandas as pd
import streamlit as st
import datetime
from fetcher import update_all_funds, STATUS_FILE, HISTORY_FILE

# 页面基础配置
st.set_page_config(
    page_title="场外标普/纳指被动基金额度监控",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS 样式
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        border-left: 5px solid #1E88E5;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
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
    "全部标的",
    "🟢 只要能买的 (含限额与不限额)",
    "🟢 只要能买且不限额的 (大额充足)",
    "🟡 只要能买但有限额的 (额度紧张)",
    "🔴 只要不能买的 (完全暂停)"
]
selected_buy_filter = st.sidebar.radio("⚡ 能买还是不能买？", buy_filter_options, index=0)

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

# 数据过滤
filtered_df = df.copy()

if selected_buy_filter == "🟢 只要能买的 (含限额与不限额)":
    filtered_df = filtered_df[filtered_df["limit_amount"] > 0]
elif selected_buy_filter == "🟢 只要能买且不限额的 (大额充足)":
    filtered_df = filtered_df[filtered_df["limit_amount"] >= 999999999]
elif selected_buy_filter == "🟡 只要能买但有限额的 (额度紧张)":
    filtered_df = filtered_df[(filtered_df["limit_amount"] > 0) & (filtered_df["limit_amount"] < 999999999)]
elif selected_buy_filter == "🔴 只要不能买的 (完全暂停)":
    filtered_df = filtered_df[filtered_df["limit_amount"] == 0]

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

# 主页面渲染
st.title("📊 场外标普500 / 纳斯达克指数基金额度监控")
st.caption(f"🕒 数据更新时间: **{updated_at}** | 监控标的: **{len(df)}** 只 | 💡 专注追踪场外美股被动QDII指数基金")

# 顶部指标卡片
col1, col2, col3, col4 = st.columns(4)
total_funds = len(df)
can_buy_funds = len(df[df["limit_amount"] > 0])
open_funds = len(df[df["limit_amount"] >= 999999999])
suspended_funds = len(df[df["limit_amount"] == 0])

with col1:
    st.metric("监控总基金数", f"{total_funds} 只")
with col2:
    st.metric("🟢 今日能买 (总计)", f"{can_buy_funds} 只", delta=f"{can_buy_funds/total_funds*100:.0f}% 可买")
with col3:
    st.metric("🟢 能买且不限额", f"{open_funds} 只", delta="大额充足")
with col4:
    st.metric("🔴 不能买 (完全暂停)", f"{suspended_funds} 只", delta_color="inverse")

st.divider()

# Tab 布局
tab1, tab2, tab3 = st.tabs(["📋 额度监控列表 (清晰直观)", "🏆 今日能买额度 TOP 榜", "📜 额度变动历史"])

with tab1:
    st.subheader(f"监控明细 (当前显示: {len(filtered_df)} 只)")

    # 格式化展示数据
    display_df = filtered_df.copy()
    
    # 购买状态与额度直观文案
    def get_buy_status(row):
        amt = row["limit_amount"]
        if amt >= 999999999:
            return "🟢 能买 (不限额)"
        elif amt > 0:
            return f"🟡 能买 (限额 {int(amt):,}元/天)"
        else:
            return "🔴 不能买 (已暂停)"

    def format_limit_text(amt):
        if amt >= 999999999:
            return "不限额 (充足)"
        elif amt == 0:
            return "0 元 (不可买)"
        elif amt >= 10000:
            return f"{amt/10000:.1f} 万元/日"
        else:
            return f"{int(amt):,} 元/日"

    display_df["能否购买"] = display_df.apply(get_buy_status, axis=1)
    display_df["单日限额"] = display_df["limit_amount"].apply(format_limit_text)
    display_df["起购金额"] = display_df["min_buy"].apply(lambda x: f"{x}元" if str(x) != "--" else "--")
    display_df["日涨跌幅"] = display_df["day_change"].apply(lambda x: f"{x}%" if x != "--" else "--")
    display_df["官方验证链接"] = display_df["code"].apply(lambda c: f"https://fund.eastmoney.com/{c}.html")

    table_view = display_df[[
        "code", "官方验证链接", "name", "index", "share_type", "能否购买", "单日限额", "起购金额", 
        "sgzt_raw", "nav", "日涨跌幅", "company"
    ]].rename(columns={
        "code": "代码",
        "name": "基金名称",
        "index": "标的指数",
        "share_type": "份额",
        "sgzt_raw": "官方原始描述 (参考)",
        "nav": "最新净值",
        "日涨跌幅": "日涨跌",
        "company": "基金公司"
    })

    st.dataframe(
        table_view,
        use_container_width=True,
        hide_index=True,
        column_config={
            "代码": st.column_config.TextColumn("基金代码", width="small"),
            "官方验证链接": st.column_config.LinkColumn("官方页面", display_text="🔗 官网核验", width="small"),
            "基金名称": st.column_config.TextColumn("基金名称", width="large"),
            "标的指数": st.column_config.TextColumn("指数分类", width="medium"),
            "能否购买": st.column_config.TextColumn("购买权限", width="medium"),
            "单日限额": st.column_config.TextColumn("单日最高可买", width="medium"),
            "起购金额": st.column_config.TextColumn("最低起购", width="small"),
            "最新净值": st.column_config.TextColumn("净值", width="small"),
            "日涨跌": st.column_config.TextColumn("涨跌幅", width="small"),
            "基金公司": st.column_config.TextColumn("基金公司", width="small"),
            "官方原始描述 (参考)": st.column_config.TextColumn("官方描述", width="medium")
        }
    )

    # 导出 CSV
    csv_data = table_view.to_csv(index=False).encode('utf_8_sig')
    st.download_button(
        label="📥 导出当前筛选表格为 CSV",
        data=csv_data,
        file_name=f"qdii_quota_{datetime.date.today()}.csv",
        mime="text/csv"
    )

with tab2:
    st.subheader("🏆 今日能买且额度最高 TOP 榜单")
    
    top_funds = df[df["limit_amount"] > 0].sort_values(by="limit_amount", ascending=False)
    
    col_l, col_r = st.columns(2)
    
    with col_l:
        st.markdown("#### 🟢 标普500可用额度最高")
        sp500_top = top_funds[top_funds["index"] == "标普500"].head(10)
        if len(sp500_top) > 0:
            for _, r in sp500_top.iterrows():
                amt_str = "🟢 不限额 (充足)" if r["limit_amount"] >= 999999999 else f"🟡 限额 {int(r['limit_amount']):,} 元/日"
                st.markdown(f"**[{r['code']}] {r['name']}**  \n👉 权限: `{amt_str}` | 起购: `{r.get('min_buy', '10')}元` | {r['company']}")
        else:
            st.info("标普500当前暂无可申购份额")

    with col_r:
        st.markdown("#### 🔵 纳斯达克100可用额度最高")
        nasdaq_top = top_funds[top_funds["index"].isin(["纳斯达克100", "纳斯达克科技"])].head(10)
        if len(nasdaq_top) > 0:
            for _, r in nasdaq_top.iterrows():
                amt_str = "🟢 不限额 (充足)" if r["limit_amount"] >= 999999999 else f"🟡 限额 {int(r['limit_amount']):,} 元/日"
                st.markdown(f"**[{r['code']}] {r['name']}**  \n👉 权限: `{amt_str}` | 起购: `{r.get('min_buy', '10')}元` | {r['company']}")
        else:
            st.info("纳斯达克相关基金当前暂无可申购份额")

with tab3:
    st.subheader("📜 最近额度变动记录")
    if history:
        hist_df = pd.DataFrame(history)
        hist_df["变动说明"] = hist_df.apply(
            lambda x: f"从【{x.get('old_sgzt', '--')}】变更为【{x.get('new_sgzt', '--')}】",
            axis=1
        )
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
        st.info("暂无历史变动记录（每日定时运行后，如果基金公司修改了限购金额，将自动在此记录变动详情）。")

# 页脚说明
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray; font-size: 13px;">
    <b>购买权限逻辑说明：</b><br>
    🟢 <b>能买 (不限额)</b>：额度充足，可随意大额申购。<br>
    🟡 <b>能买 (限额 X 元)</b>：可以买！单日累计不可超过此金额（如限额100元，每天买100元定投即可成交）。<br>
    🔴 <b>不能买 (已暂停)</b>：完全关闭申购，单日限额为 0 元。<br>
    <i>数据源自公开交易接口，实际申购请以基金公司最新公告与各销售渠道为准。</i>
</div>
""", unsafe_allow_html=True)
