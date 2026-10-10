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
    .badge-open {
        background-color: #E8F5E9;
        color: #2E7D32;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .badge-warn {
        background-color: #FFF3E0;
        color: #EF6C00;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .badge-danger {
        background-color: #FFEBEE;
        color: #C62828;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: bold;
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

# 侧边栏筛选器
index_options = ["全部"] + sorted(list(df["index"].unique()))
selected_index = st.sidebar.selectbox("🎯 标的指数", index_options)

share_options = ["全部", "仅看A类", "仅看C类"]
selected_share = st.sidebar.selectbox("🏷️ 份额类别", share_options)

quota_options = [
    "全部",
    "仅看有额度 (＞0元)",
    "大额/开放 (≥10,000元 或 充足)",
    "中度限额 (101~1,000元)",
    "严厉限购 (≤100元)",
    "极度限购 (≤10元)",
    "暂停申购 (0元)"
]
selected_quota = st.sidebar.selectbox("⚡ 额度状态", quota_options)

company_options = ["全部"] + sorted([c for c in df["company"].unique() if c != "--"])
selected_company = st.sidebar.selectbox("🏢 基金公司", company_options)

search_query = st.sidebar.text_input("🔎 搜索基金代码 / 名称", "")

# 过滤逻辑
filtered_df = df.copy()

if selected_index != "全部":
    filtered_df = filtered_df[filtered_df["index"] == selected_index]

if selected_share == "仅看A类":
    filtered_df = filtered_df[filtered_df["share_type"] == "A类"]
elif selected_share == "仅看C类":
    filtered_df = filtered_df[filtered_df["share_type"] == "C类"]

if selected_company != "全部":
    filtered_df = filtered_df[filtered_df["company"] == selected_company]

if selected_quota == "仅看有额度 (＞0元)":
    filtered_df = filtered_df[filtered_df["limit_amount"] > 0]
elif selected_quota == "大额/开放 (≥10,000元 或 充足)":
    filtered_df = filtered_df[filtered_df["limit_amount"] >= 10000]
elif selected_quota == "中度限额 (101~1,000元)":
    filtered_df = filtered_df[(filtered_df["limit_amount"] > 100) & (filtered_df["limit_amount"] <= 1000)]
elif selected_quota == "严厉限购 (≤100元)":
    filtered_df = filtered_df[(filtered_df["limit_amount"] > 0) & (filtered_df["limit_amount"] <= 100)]
elif selected_quota == "极度限购 (≤10元)":
    filtered_df = filtered_df[(filtered_df["limit_amount"] > 0) & (filtered_df["limit_amount"] <= 10)]
elif selected_quota == "暂停申购 (0元)":
    filtered_df = filtered_df[filtered_df["limit_amount"] == 0]

if search_query:
    q = search_query.strip().lower()
    filtered_df = filtered_df[
        filtered_df["code"].str.lower().str.contains(q) |
        filtered_df["name"].str.lower().str.contains(q) |
        filtered_df["company"].str.lower().str.contains(q)
    ]

# 主页面渲染
st.title("📊 场外标普500 / 纳斯达克指数基金额度监控")
st.caption(f"🕒 数据最新更新时间: **{updated_at}** | 监控标的数量: **{len(df)}** 只 | 💡 自动跟踪全市场主流美股被动指数QDII")

# 顶部指标卡片
col1, col2, col3, col4, col5 = st.columns(5)
total_funds = len(df)
open_funds = len(df[df["limit_amount"] >= 999999999])
limited_funds = len(df[(df["limit_amount"] > 0) & (df["limit_amount"] < 999999999)])
suspended_funds = len(df[df["limit_amount"] == 0])
has_quota_count = len(df[df["limit_amount"] > 0])

with col1:
    st.metric("监控总标的", f"{total_funds} 只")
with col2:
    st.metric("今日有额度", f"{has_quota_count} 只", delta=f"{has_quota_count/total_funds*100:.0f}% 可买")
with col3:
    st.metric("开放申购 (充足)", f"{open_funds} 只")
with col4:
    st.metric("限额申购", f"{limited_funds} 只")
with col5:
    st.metric("完全暂停申购", f"{suspended_funds} 只", delta_color="inverse")

st.divider()

# Tab 布局
tab1, tab2, tab3 = st.tabs(["📋 额度监控列表", "🏆 今日额度排行榜", "📜 额度变动历史"])

with tab1:
    st.subheader(f"监控明细 (当前显示: {len(filtered_df)} 只)")

    # 格式化展示 DataFrame
    display_df = filtered_df.copy()
    
    # 格式化展示金额
    def format_limit(val):
        if val >= 999999999:
            return "开放申购 (充足)"
        elif val == 0:
            return "暂停申购 (0元)"
        elif val >= 10000:
            return f"{val/10000:.1f}万元"
        else:
            return f"{int(val):,}元"

    display_df["单日限额"] = display_df["limit_amount"].apply(format_limit)
    display_df["日涨跌幅"] = display_df["day_change"].apply(lambda x: f"{x}%" if x != "--" else "--")
    
    table_view = display_df[[
        "code", "name", "index", "share_type", "单日限额", 
        "sgzt_raw", "shzt", "nav", "日涨跌幅", "nav_date", "company"
    ]].rename(columns={
        "code": "代码",
        "name": "基金名称",
        "index": "标的指数",
        "share_type": "份额",
        "sgzt_raw": "官方申购状态",
        "shzt": "赎回状态",
        "nav": "最新净值",
        "nav_date": "净值日期",
        "company": "基金公司"
    })

    st.dataframe(
        table_view,
        use_container_width=True,
        hide_index=True,
        column_config={
            "代码": st.column_config.TextColumn("基金代码", width="small"),
            "基金名称": st.column_config.TextColumn("基金名称", width="large"),
            "标的指数": st.column_config.TextColumn("指数分类", width="medium"),
            "单日限额": st.column_config.TextColumn("单日最高限额", width="medium"),
            "官方申购状态": st.column_config.TextColumn("官方申购状态", width="large"),
            "最新净值": st.column_config.TextColumn("净值", width="small"),
            "日涨跌幅": st.column_config.TextColumn("日涨跌", width="small"),
            "基金公司": st.column_config.TextColumn("基金公司", width="small"),
        }
    )

    # 导出 CSV
    csv_data = table_view.to_csv(index=False).encode('utf_8_sig')
    st.download_button(
        label="📥 导出当前数据为 CSV",
        data=csv_data,
        file_name=f"qdii_quota_{datetime.date.today()}.csv",
        mime="text/csv"
    )

with tab2:
    st.subheader("🏆 今日可用额度 TOP 榜单")
    
    top_funds = df[df["limit_amount"] > 0].sort_values(by="limit_amount", ascending=False)
    
    col_l, col_r = st.columns(2)
    
    with col_l:
        st.markdown("#### 🟢 标普500可用额度最高")
        sp500_top = top_funds[top_funds["index"] == "标普500"].head(10)
        if len(sp500_top) > 0:
            for _, r in sp500_top.iterrows():
                amt_str = "开放申购 (充足)" if r["limit_amount"] >= 999999999 else f"{int(r['limit_amount']):,} 元/日"
                st.markdown(f"**[{r['code']}] {r['name']}**  \n💰 单日上限: `{amt_str}` | {r['company']}")
        else:
            st.info("标普500当前暂无可申购份额")

    with col_r:
        st.markdown("#### 🔵 纳斯达克100可用额度最高")
        nasdaq_top = top_funds[top_funds["index"].isin(["纳斯达克100", "纳斯达克科技"])].head(10)
        if len(nasdaq_top) > 0:
            for _, r in nasdaq_top.iterrows():
                amt_str = "开放申购 (充足)" if r["limit_amount"] >= 999999999 else f"{int(r['limit_amount']):,} 元/日"
                st.markdown(f"**[{r['code']}] {r['name']}**  \n💰 单日上限: `{amt_str}` | {r['company']}")
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

# 页脚
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray; font-size: 13px;">
    场外QDII额度实时监控系统 · 开源免费 · 基于 Streamlit & GitHub Actions 自动更新<br>
    数据源自天天基金/东财公开信息，数据仅供参考，实际申购请以基金公司最新公告与各销售渠道为准。
</div>
""", unsafe_allow_html=True)
