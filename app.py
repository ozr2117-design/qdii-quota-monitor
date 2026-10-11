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

# 自定义苹果风格自适应响应式 CSS 样式 (支持跟随访问设备自动切换夜间/深色模式)
st.markdown("""
<style>
    /* ========================================================
       色彩设计系统 (Design Tokens) - 苹果极简主义双模式规范
       ======================================================== */
    :root {
        color-scheme: light dark;

        /* 日间浅色模式 (Apple Light Mode) */
        --bg-page: #ffffff;
        --bg-header: #ffffff;
        --bg-sidebar: #f8fafc;
        --bg-card: #ffffff;
        --bg-card-subtle: #fbfbfd;
        --bg-table-wrapper: #ffffff;
        --bg-table-th: #f1f5f9;
        --bg-table-even: #f8fafc;
        --bg-table-hover: #e2e8f0;
        
        --text-primary: #1d1d1f;
        --text-secondary: #515154;
        --text-muted: #6e6e73;
        --text-table: #1e293b;
        --text-table-th: #334155;
        
        --border-card: rgba(0, 0, 0, 0.08);
        --border-table-outer: #cbd5e1;
        --border-table-row: #e2e8f0;
        --border-table-col: #f1f5f9;
        --border-table-th: #94a3b8;
        
        --btn-sec-bg: #f0f0f5;
        --btn-sec-text: #1d1d1f;
        --btn-sec-border: rgba(0, 0, 0, 0.08);
        
        --shadow-hero: 0 4px 20px rgba(0, 0, 0, 0.03);
        --shadow-card: 0 2px 8px rgba(0, 0, 0, 0.02);
        --shadow-card-hover: 0 4px 12px rgba(0, 0, 0, 0.05);
        
        --color-code: #0284c7;
        --color-green: #15803d;
        --color-red: #dc2626;
        --color-orange: #a16207;

        /* 状态与指标标签 (Light) */
        --badge-green-bg: #f0fdf4;
        --badge-green-text: #15803d;
        --badge-green-border: #bbf7d0;

        --badge-orange-bg: #fefce8;
        --badge-orange-text: #a16207;
        --badge-orange-border: #fef08a;

        --badge-red-bg: #fef2f2;
        --badge-red-text: #b91c1c;
        --badge-red-border: #fecaca;

        --badge-gray-bg: #f1f5f9;
        --badge-gray-text: #64748b;
        --badge-gray-border: #cbd5e1;

        --badge-channel-bg: #fffbeb;
        --badge-channel-text: #92400e;
        --badge-channel-border: #fde68a;

        --badge-blue-bg: #eff6ff;
        --badge-blue-text: #1d4ed8;
        --badge-blue-border: #dbeafe;
    }

    /* 访问设备系统夜间/暗黑模式自适应 (Apple Dark Mode) */
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-page: #0f1012;
            --bg-header: #0f1012;
            --bg-sidebar: #16171b;
            --bg-card: #1c1d22;
            --bg-card-subtle: #212228;
            --bg-table-wrapper: #1c1d22;
            --bg-table-th: #262831;
            --bg-table-even: #18191e;
            --bg-table-hover: #2c2f3a;
            
            --text-primary: #f5f5f7;
            --text-secondary: #a1a1a6;
            --text-muted: #86868b;
            --text-table: #e2e8f0;
            --text-table-th: #cbd5e1;
            
            --border-card: rgba(255, 255, 255, 0.1);
            --border-table-outer: #383b46;
            --border-table-row: #292b34;
            --border-table-col: #21232b;
            --border-table-th: #4b4f5e;
            
            --btn-sec-bg: #2c2e35;
            --btn-sec-text: #f5f5f7;
            --btn-sec-border: rgba(255, 255, 255, 0.12);
            
            --shadow-hero: 0 4px 24px rgba(0, 0, 0, 0.45);
            --shadow-card: 0 2px 10px rgba(0, 0, 0, 0.35);
            --shadow-card-hover: 0 6px 16px rgba(0, 0, 0, 0.55);
            
            --color-code: #38bdf8;
            --color-green: #4ade80;
            --color-red: #f87171;
            --color-orange: #fbbf24;

            /* 状态与指标标签 (Dark 高对比度舒适色) */
            --badge-green-bg: rgba(34, 197, 94, 0.15);
            --badge-green-text: #4ade80;
            --badge-green-border: rgba(74, 222, 128, 0.3);

            --badge-orange-bg: rgba(234, 179, 8, 0.15);
            --badge-orange-text: #facc15;
            --badge-orange-border: rgba(250, 204, 21, 0.3);

            --badge-red-bg: rgba(239, 68, 68, 0.15);
            --badge-red-text: #f87171;
            --badge-red-border: rgba(248, 113, 113, 0.3);

            --badge-gray-bg: rgba(148, 163, 184, 0.14);
            --badge-gray-text: #cbd5e1;
            --badge-gray-border: rgba(148, 163, 184, 0.25);

            --badge-channel-bg: rgba(245, 158, 11, 0.15);
            --badge-channel-text: #fbbf24;
            --badge-channel-border: rgba(251, 191, 36, 0.3);

            --badge-blue-bg: rgba(59, 130, 246, 0.15);
            --badge-blue-text: #60a5fa;
            --badge-blue-border: rgba(96, 165, 250, 0.3);
        }

        /* Streamlit 自身组件暗黑适配 */
        [data-testid="stSidebar"], section[data-testid="stSidebar"] {
            background-color: var(--bg-sidebar) !important;
            border-right: 1px solid var(--border-card) !important;
        }
        [data-testid="stSidebar"] * {
            color: var(--text-primary);
        }
        [data-testid="stSidebar"] .stCaption,
        [data-testid="stSidebar"] .stMarkdown p {
            color: var(--text-secondary) !important;
        }
        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] select,
        [data-testid="stSidebar"] div[data-baseweb="select"] {
            background-color: #212228 !important;
            color: var(--text-primary) !important;
            border-color: rgba(255, 255, 255, 0.15) !important;
        }
        button[data-baseweb="tab"] {
            color: var(--text-secondary) !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #38bdf8 !important;
            border-bottom-color: #38bdf8 !important;
        }
        div[data-testid="stTabs"] {
            border-bottom-color: var(--border-card) !important;
        }
        div[data-testid="stExpander"] {
            background-color: var(--bg-card) !important;
            border: 1px solid var(--border-card) !important;
            border-radius: 12px !important;
        }
        div[data-testid="stExpander"] details summary span {
            color: var(--text-primary) !important;
        }
        .stCaption, [data-testid="stCaptionContainer"] {
            color: var(--text-secondary) !important;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--border-card) !important;
            border-radius: 12px !important;
        }

        /* 强力直达覆盖：移动端/WebView即便变量解析有偶发延迟也100%瞬间变暗 */
        .stApp {
            background-color: #0f1012 !important;
        }
        header[data-testid="stHeader"],
        .stAppHeader,
        header {
            background-color: #0f1012 !important;
            background: #0f1012 !important;
        }
        .apple-hero-banner {
            background: #212228 !important;
            border-color: rgba(255, 255, 255, 0.1) !important;
            color: #f5f5f7 !important;
        }
        .apple-hero-headline {
            color: #f5f5f7 !important;
        }
        .apple-hero-subhead {
            color: #a1a1a6 !important;
        }
        .apple-btn-secondary {
            background: #2c2e35 !important;
            color: #f5f5f7 !important;
            border-color: rgba(255, 255, 255, 0.12) !important;
        }
        .apple-stat-card {
            background: #1c1d22 !important;
            border-color: rgba(255, 255, 255, 0.1) !important;
        }
        .stat-value {
            color: #f5f5f7 !important;
        }
        .stat-sub {
            color: #a1a1a6 !important;
        }
        .top-fund-item {
            background: #1c1d22 !important;
            border-color: rgba(255, 255, 255, 0.1) !important;
        }
        .top-fund-title {
            color: #f5f5f7 !important;
        }
        .top-fund-sub {
            color: #86868b !important;
        }
        .apple-fund-card {
            background: #1c1d22 !important;
            border-color: rgba(255, 255, 255, 0.1) !important;
        }
        .fund-name {
            color: #f5f5f7 !important;
        }
        .card-meta-row {
            color: #a1a1a6 !important;
        }
        .desktop-table-view {
            background: #1c1d22 !important;
            border-color: #383b46 !important;
        }
        .apple-desktop-table th {
            background-color: #262831 !important;
            color: #cbd5e1 !important;
            border-bottom-color: #4b4f5e !important;
            border-right-color: #292b34 !important;
        }
        .apple-desktop-table td {
            color: #e2e8f0 !important;
            border-bottom-color: #292b34 !important;
            border-right-color: #21232b !important;
        }
        .apple-desktop-table tr:nth-child(even) td {
            background-color: #18191e !important;
        }
        .apple-desktop-table tr:hover td {
            background-color: #2c2f3a !important;
        }
        .col-name {
            color: #f5f5f7 !important;
        }
        .col-index {
            color: #a1a1a6 !important;
        }
        .section-title {
            color: #f5f5f7 !important;
        }
        .expander-guide-content {
            color: #a1a1a6 !important;
        }
    }

    /* 全局统一底色与字体 */
    .stApp {
        background-color: var(--bg-page) !important;
    }
    header[data-testid="stHeader"],
    .stAppHeader,
    header {
        background-color: var(--bg-header) !important;
        background: var(--bg-header) !important;
    }
    [data-testid="stDecoration"] {
        display: none !important;
    }
    html, body, [class*="css"], .stMarkdown {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", sans-serif !important;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        color: var(--text-primary);
    }
    
    /* 容器边距柔和微调 */
    .block-container {
        padding-top: 4.6rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1440px !important;
        width: 95% !important;
    }
    @media screen and (max-width: 768px) {
        .block-container {
            padding-top: 4rem !important;
            padding-left: 0.9rem !important;
            padding-right: 0.9rem !important;
            width: 100% !important;
        }
    }

    /* 苹果官网旗舰级 Hero 舞台 */
    .apple-hero-banner {
        background: var(--bg-card-subtle);
        border: 1px solid var(--border-card);
        border-radius: 18px;
        margin-top: 2px;
        margin-bottom: 16px;
        overflow: hidden;
        color: var(--text-primary);
        text-align: center;
        box-shadow: var(--shadow-hero);
    }
    .apple-hero-body {
        padding: 32px 20px 28px 20px;
    }
    .apple-hero-headline {
        font-size: 38px;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.025em;
        line-height: 1.2;
        margin: 0 0 10px 0;
    }
    @media screen and (max-width: 768px) {
        .apple-hero-headline {
            font-size: 27px;
            margin-bottom: 8px;
        }
        .apple-hero-body {
            padding: 22px 14px 20px 14px;
        }
    }
    .apple-hero-subhead {
        font-size: 17px;
        font-weight: 400;
        color: var(--text-secondary);
        letter-spacing: -0.01em;
        line-height: 1.4;
        margin: 0 0 20px 0;
    }
    @media screen and (max-width: 768px) {
        .apple-hero-subhead {
            font-size: 14px;
            margin-bottom: 16px;
        }
    }
    .apple-hero-ctas {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        flex-wrap: wrap;
    }
    .apple-btn-blue {
        background: #0071e3;
        color: #ffffff !important;
        font-size: 14px;
        font-weight: 500;
        padding: 8px 22px;
        border-radius: 980px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        letter-spacing: -0.01em;
        box-shadow: 0 2px 10px rgba(0, 113, 227, 0.25);
    }
    .apple-btn-secondary {
        background: var(--btn-sec-bg);
        color: var(--btn-sec-text) !important;
        border: 1px solid var(--btn-sec-border);
        font-size: 14px;
        font-weight: 500;
        padding: 8px 20px;
        border-radius: 980px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        letter-spacing: -0.01em;
    }

    /* 苹果小组件风格统计卡片 */
    .apple-stats-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin: 14px 0 20px 0;
    }
    @media screen and (max-width: 768px) {
        .apple-stats-grid {
            gap: 8px;
        }
    }
    .apple-stat-card {
        background: var(--bg-card);
        border: 1px solid var(--border-card);
        border-radius: 14px;
        padding: 14px 16px;
        box-shadow: var(--shadow-card);
    }
    @media screen and (max-width: 768px) {
        .apple-stat-card {
            padding: 10px 10px;
        }
    }
    .stat-label {
        font-size: 13px;
        color: var(--text-muted);
        font-weight: 500;
        margin-bottom: 4px;
        white-space: nowrap;
    }
    @media screen and (max-width: 768px) {
        .stat-label {
            font-size: 12px;
        }
    }
    .stat-value {
        font-size: 26px;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1.2;
        letter-spacing: -0.02em;
    }
    @media screen and (max-width: 768px) {
        .stat-value {
            font-size: 21px;
        }
    }
    .stat-unit {
        font-size: 13px;
        font-weight: 500;
        color: var(--text-muted);
        margin-left: 2px;
    }
    .stat-sub {
        font-size: 13px;
        color: var(--text-secondary);
        margin-top: 4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    @media screen and (max-width: 768px) {
        .stat-sub {
            font-size: 11px;
        }
    }
    .text-green {
        color: var(--color-green);
    }

    /* 分组与板块标题 */
    .section-title {
        font-size: 13px;
        font-weight: 600;
        color: var(--text-primary);
        margin: 4px 0 8px 0;
    }

    /* TOP 榜单项卡片 */
    .top-fund-item {
        background: var(--bg-card);
        border: 1px solid var(--border-card);
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 10px;
        box-shadow: var(--shadow-card);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .top-fund-item:hover {
        box-shadow: var(--shadow-card-hover);
    }
    .top-fund-title {
        font-size: 15px;
        font-weight: 600;
        color: var(--text-primary);
    }
    .top-fund-code {
        color: var(--color-code);
        font-family: -apple-system-monospaced, "SF Pro Text", Consolas, monospace;
        margin-right: 4px;
    }
    .top-fund-sub {
        font-size: 13px;
        color: var(--text-muted);
        margin-top: 6px;
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 6px;
    }
    .badge-limit-unlimited {
        font-size: 13px;
        font-weight: 600;
        color: var(--badge-green-text);
        background: var(--badge-green-bg);
        border: 1px solid var(--badge-green-border);
        padding: 3px 9px;
        border-radius: 8px;
        white-space: nowrap;
        flex-shrink: 0;
    }
    .badge-limit-warning {
        font-size: 13px;
        font-weight: 600;
        color: var(--badge-orange-text);
        background: var(--badge-orange-bg);
        border: 1px solid var(--badge-orange-border);
        padding: 3px 9px;
        border-radius: 8px;
        white-space: nowrap;
        flex-shrink: 0;
    }
    .badge-channel-note {
        color: var(--badge-channel-text);
        font-weight: 500;
        background: var(--badge-channel-bg);
        padding: 2px 8px;
        border-radius: 6px;
        border: 1px solid var(--badge-channel-border);
    }
    .tag-dca-active {
        color: var(--color-green);
        font-weight: 600;
    }

    /* 说明面板样式 */
    .expander-guide-content {
        font-size: 13.5px;
        line-height: 1.65;
        color: var(--text-secondary);
        padding: 4px 0;
    }
    .guide-divider {
        margin: 8px 0;
        border: none;
        border-top: 1px dashed var(--border-card);
    }

    /* 移动端卡片流 */
    .apple-fund-card {
        background: var(--bg-card);
        border: 1px solid var(--border-card);
        border-radius: 14px;
        padding: 14px 16px;
        margin-bottom: 12px;
        box-shadow: var(--shadow-card);
    }
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 8px;
        gap: 8px;
    }
    .fund-name {
        font-size: 15px;
        font-weight: 600;
        color: var(--text-primary);
        line-height: 1.4;
        word-break: break-all;
    }
    .fund-code {
        color: var(--color-code);
        font-weight: 600;
        margin-right: 4px;
        font-family: -apple-system-monospaced, "SF Pro Text", Consolas, monospace;
    }
    .card-meta-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: var(--text-secondary);
        font-size: 14px;
        margin-bottom: 8px;
    }
    .card-metrics-row {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 8px;
    }
    .card-channel-note {
        margin-top: 8px;
        background: var(--badge-channel-bg);
        border-left: 3px solid #f59e0b;
        border-radius: 4px;
        padding: 6px 10px;
        color: var(--badge-channel-text);
        font-size: 13px;
        font-weight: 500;
    }
    .limit-val-highlight {
        color: var(--color-green);
        font-size: 14px;
    }
    .dca-val-highlight {
        color: var(--color-green);
        font-size: 13px;
        font-weight: 600;
    }
    .dca-status-yes {
        font-size: 12px;
        color: var(--color-green);
        font-weight: 600;
        margin-top: 3px;
    }
    .dca-status-no {
        font-size: 12px;
        color: var(--text-muted);
        margin-top: 3px;
    }
    .text-empty {
        color: var(--text-muted);
        opacity: 0.6;
    }

    /* 标签与徽章 */
    .metric-tag {
        font-size: 12px;
        padding: 3px 8px;
        border-radius: 6px;
        display: inline-flex;
        align-items: center;
        gap: 2px;
        font-weight: 500;
    }
    .tag-blue {
        background: var(--badge-blue-bg);
        color: var(--badge-blue-text);
        border: 1px solid var(--badge-blue-border);
    }
    .tag-green {
        background: var(--badge-green-bg);
        color: var(--badge-green-text);
        border: 1px solid var(--badge-green-border);
    }
    .tag-orange {
        background: var(--badge-orange-bg);
        color: var(--badge-orange-text);
        border: 1px solid var(--badge-orange-border);
    }
    .tag-red {
        background: var(--badge-red-bg);
        color: var(--badge-red-text);
        border: 1px solid var(--badge-red-border);
    }
    .tag-gray {
        background: var(--badge-gray-bg);
        color: var(--badge-gray-text);
        border: 1px solid var(--badge-gray-border);
    }

    /* 桌面端高标准金融数据表格 */
    .desktop-table-view {
        display: block !important;
        margin-top: 14px;
        margin-bottom: 24px;
        background: var(--bg-table-wrapper);
        border: 1px solid var(--border-table-outer);
        border-radius: 12px;
        box-shadow: var(--shadow-card);
        overflow-x: auto;
    }
    .apple-desktop-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
        text-align: left;
    }
    .apple-desktop-table th {
        background-color: var(--bg-table-th);
        color: var(--text-table-th);
        font-weight: 600;
        text-align: left;
        padding: 13px 14px;
        border-bottom: 2px solid var(--border-table-th);
        border-right: 1px solid var(--border-table-row);
        white-space: nowrap;
        font-size: 13px;
        letter-spacing: -0.01em;
    }
    .apple-desktop-table th:last-child {
        border-right: none;
    }
    .apple-desktop-table td {
        padding: 13px 14px;
        border-bottom: 1px solid var(--border-table-row);
        border-right: 1px solid var(--border-table-col);
        color: var(--text-table);
        vertical-align: middle;
        line-height: 1.5;
        font-size: 14px;
    }
    .apple-desktop-table td:last-child {
        border-right: none;
    }
    .apple-desktop-table tr:nth-child(even) td {
        background-color: var(--bg-table-even);
    }
    .apple-desktop-table tr:hover td {
        background-color: var(--bg-table-hover) !important;
    }
    .apple-desktop-table tr:last-child td {
        border-bottom: none;
    }
    .col-code {
        font-family: -apple-system-monospaced, "SF Pro Text", Consolas, monospace;
        color: var(--color-code);
        font-weight: 700;
        font-size: 14px;
        white-space: nowrap;
    }
    .col-name {
        font-weight: 600;
        font-size: 14px;
        color: var(--text-primary);
        white-space: normal;
        word-break: break-all;
        line-height: 1.4;
    }
    .col-index {
        white-space: nowrap;
        font-size: 14px;
        color: var(--text-secondary);
        font-weight: 500;
    }
    .col-limit {
        white-space: nowrap;
        font-weight: 700;
        font-size: 14px;
        color: var(--color-green);
    }
    .col-error {
        white-space: nowrap;
        font-weight: 500;
        font-size: 14px;
    }
    .badge-ms-green {
        background: var(--badge-green-bg);
        color: var(--badge-green-text);
        border: 1px solid var(--badge-green-border);
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-ms-orange {
        background: var(--badge-orange-bg);
        color: var(--badge-orange-text);
        border: 1px solid var(--badge-orange-border);
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-ms-red {
        background: var(--badge-red-bg);
        color: var(--badge-red-text);
        border: 1px solid var(--badge-red-border);
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-ms-gray {
        background: var(--badge-gray-bg);
        color: var(--badge-gray-text);
        border: 1px solid var(--badge-gray-border);
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 12px;
    }
    .col-return {
        white-space: nowrap;
        color: var(--color-red);
        font-weight: 700;
        font-size: 14px;
    }
    .col-fee {
        white-space: nowrap;
        font-weight: 500;
        font-size: 14px;
        color: var(--text-table);
    }
    .badge-fee-low {
        background: var(--badge-green-bg);
        color: var(--badge-green-text);
        border: 1px solid var(--badge-green-border);
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-fee-mid {
        background: var(--badge-gray-bg);
        color: var(--badge-gray-text);
        border: 1px solid var(--badge-gray-border);
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 12px;
    }
    .badge-fee-high {
        background: var(--badge-orange-bg);
        color: var(--badge-orange-text);
        border: 1px solid var(--badge-orange-border);
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
    }
    .col-channel {
        display: inline-block;
        background: var(--badge-channel-bg);
        border: 1px solid var(--badge-channel-border);
        border-radius: 6px;
        padding: 5px 9px;
        color: var(--badge-channel-text);
        font-size: 12px;
        line-height: 1.45;
        font-weight: 500;
        word-break: break-word;
    }

    /* 响应式适配：大屏显示表格，小屏显示卡片流 */
    .desktop-table-view {
        display: block !important;
    }
    .mobile-cards-view {
        display: none !important;
    }
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

header_html = f"""<div class="apple-hero-banner">
    <div class="apple-hero-body">
        <div class="apple-hero-headline">小鸡观察基地</div>
        <div class="apple-hero-subhead">专注美股被动 QDII · 场外额度实时雷达。</div>
        <div class="apple-hero-ctas">
            <span class="apple-btn-blue">今日可买 {can_buy_funds} 只标的</span>
            <span class="apple-btn-secondary">实时监控中 · 🕒 {updated_at}</span>
        </div>
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
                amt_badge_cls = "badge-limit-unlimited"
            elif amt >= 10000:
                amt_str = f"限额 {amt/10000:.1f}万/日"
                amt_badge_cls = "badge-limit-warning"
            else:
                amt_str = f"限额 {int(amt):,}元/日"
                amt_badge_cls = "badge-limit-warning"

            note_badge = f'<span class="badge-channel-note">💡 {r["channel_note"]}</span>' if r.get('channel_note') else ''
            dca_tag = ' · <span class="tag-dca-active">● 支持定投</span>' if r.get('can_dca') else ''

            item = (
                f'<div class="top-fund-item">'
                f'<div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">'
                f'<span class="top-fund-title"><span class="top-fund-code">{r["code"]}</span> {r["name"]}</span>'
                f'<span class="{amt_badge_cls}">{amt_str}</span>'
                f'</div>'
                f'<div class="top-fund-sub">'
                f'<span>起购: {r.get("min_buy", "10")}元</span>'
                f'{dca_tag}'
                f'{note_badge}'
                f'</div>'
                f'</div>'
            )
            items_html.append(item)
        return "".join(items_html)

    with col_l:
        st.markdown('<div class="section-title">🟢 标普500 可用额度最高 TOP 10</div>', unsafe_allow_html=True)
        sp500_top = top_funds[top_funds["index"] == "标普500"].head(10)
        if len(sp500_top) > 0:
            st.markdown(render_top_list(sp500_top), unsafe_allow_html=True)
        else:
            st.info("标普500当前暂无可申购份额")

    with col_r:
        st.markdown('<div class="section-title">🔵 纳斯达克100 可用额度最高 TOP 10</div>', unsafe_allow_html=True)
        nasdaq_top = top_funds[top_funds["index"].isin(["纳斯达克100", "纳斯达克科技"])].head(10)
        if len(nasdaq_top) > 0:
            st.markdown(render_top_list(nasdaq_top), unsafe_allow_html=True)
        else:
            st.info("纳斯达克相关基金当前暂无可申购份额")

with tab2:
    st.caption(f"当前显示 **{len(filtered_df)}** 只可买基金（已自动过滤暂停申购标的，可在左侧切换）")

    with st.expander("💡 什么是「相对基准」「综合年费率」与 A/C 选基秘籍？", expanded=False):
        st.markdown("""<div class="expander-guide-content">
<b>核心指标解读：</b><br>
• <span class="badge-ms-green">极佳 / 跑赢</span> <b>相对基准跑输 &lt; 1.0% 或跑赢</b>：复制精度极高，超额摩擦损耗极小，属于<b>首选优质标的</b>。<br>
• <span class="badge-ms-orange">正常</span> <b>跑输 1.0% ~ 2.0%</b>：处于正常的 QDII 外汇与运营摩擦区间。<br>
• <span class="badge-ms-red">偏大</span> <b>跑输 &gt; 2.0%</b>：跟踪磨损较大，长期持有易被吃掉收益，需谨慎。<br>
• <span class="badge-fee-low">极省</span> <b>综合年费率 &le; 0.35%</b>：管理费+托管费极低，长期定投省出大量收益。<br>
• <span class="badge-fee-mid">常规</span> <b>综合年费率 0.35% ~ 0.85%</b>：主流公募指数基金常规费率。<br>
• <span class="badge-fee-high">偏高</span> <b>综合年费率 &gt; 0.85%</b>：通常为 C 类（含销售服务费）或老一代高费率 QDII。<br>
<hr class="guide-divider">
<b>🎯 场外避坑与实操秘籍：</b><br>
• <b>A类 vs C类怎么选？</b> 长期定投持有（&gt; 1年）<b>必选 A 类</b>（无年化销售服务费，长期省大钱）；短期波段（&lt; 1年）选 <b>C 类</b>（免申购费更灵活）。<br>
• <b>美元现汇大水管：</b> 若手头有美元现汇，可直接在平台搜索对应基金的<b>【美元现汇份额】</b>，通常不占换汇额度，限额极其充裕！<br>
• <b>定投偷渡通道：</b> 若部分基金单笔限额较小，可直接在交易 App 中设置<b>【每日定期定额】</b>，每天自动稳定积攒额度。
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
            f'<div class="card-channel-note">💡 {row["channel_note"]}</div>'
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

        dca_card_text = " · 支持定投" if row.get("can_dca") else ""

        card = (
            f'<div class="apple-fund-card">'
            f'<div class="card-header">'
            f'<div class="fund-name"><span class="fund-code">{row["code"]}</span> {row["name"]}</div>'
            f'</div>'
            f'<div class="card-meta-row">'
            f'<span>🎯 标的: <b>{row["index"]}</b></span>'
            f'<span>💰 单日限额: <b class="limit-val-highlight">{row["单日限额"]}</b><span class="dca-val-highlight">{dca_card_text}</span></span>'
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

    # 2. 电脑端数据表格 (专业现代设计：字号清晰、对比度高、零横向滚动条)
    table_rows = []
    for _, row in display_df.iterrows():
        channel_content = (
            f'<div class="col-channel">💡 {row["channel_note"].replace("💡 ", "")}</div>'
            if row["channel_note"] else '<span class="text-empty">--</span>'
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
            ms_cell_html = f'<div title="{tooltip}" style="display:inline-flex; align-items:center; gap:5px; cursor:help;"><span>{diff}</span><span class="{badge_cls}">{eval_label}</span></div>'

        total_fee = row.get("total_fee", "--")
        mgmt_fee = row.get("mgmt_fee", "--")
        cust_fee = row.get("custody_fee", "--")
        serv_fee = row.get("service_fee", "--")
        fee_badge = row.get("fee_badge", "normal")
        fee_tooltip = f"管理费: {mgmt_fee} | 托管费: {cust_fee} | 销售服务费: {serv_fee}"
        
        if total_fee == "--":
            fee_cell_html = '<span class="text-empty">--</span>'
        else:
            badge_cls = "badge-fee-low" if fee_badge == "low" else ("badge-fee-high" if fee_badge == "high" else "badge-fee-mid")
            badge_lbl = "极省" if fee_badge == "low" else ("偏高" if fee_badge == "high" else "常规")
            fee_cell_html = f'<div title="{fee_tooltip}" style="display:inline-flex; align-items:center; gap:5px; cursor:help;"><span>{total_fee}</span><span class="{badge_cls}">{badge_lbl}</span></div>'

        dca_badge = '<div class="dca-status-yes">● 支持定投</div>' if row.get("can_dca") else '<div class="dca-status-no">暂停定投</div>'

        tr = (
            f'<tr>'
            f'<td class="col-code">{row["code"]}</td>'
            f'<td class="col-name">{row["name"]}</td>'
            f'<td class="col-index">{row["index"]}</td>'
            f'<td class="col-limit"><div>{row["单日限额"]}</div>{dca_badge}</td>'
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
        f'<th style="width:75px;">代码</th>'
        f'<th style="min-width:180px;">基金名称</th>'
        f'<th style="width:95px;">标的指数</th>'
        f'<th style="width:115px;">单日最高限额</th>'
        f'<th style="min-width:145px;">近1年相对基准 (晨星)</th>'
        f'<th style="width:90px;">近1年收益</th>'
        f'<th style="width:105px;">综合年费率</th>'
        f'<th style="min-width:210px;">💡 直销渠道情报</th>'
        f'</tr></thead>'
        f'<tbody>{"".join(table_rows)}</tbody>'
        f'</table>'
        f'</div>'
    )
    st.markdown(desktop_table_html, unsafe_allow_html=True)


with tab3:
    st.caption("📜 每日各标的限购额度升降与状态变更明细")
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
        cols = ["time", "code", "name", "index", "变动说明"]
        rename_map = {
            "time": "变动时间",
            "code": "代码",
            "name": "基金名称",
            "index": "标的指数"
        }
        if "notice_title" in hist_df.columns:
            cols.append("notice_title")
            rename_map["notice_title"] = "关联法定公告"

        st.dataframe(
            hist_df[cols].rename(columns=rename_map),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("暂无额度变动记录。")


