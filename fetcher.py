import os
import json
import re
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
FUNDS_FILE = os.path.join(os.path.dirname(__file__), "funds.json")
STATUS_FILE = os.path.join(DATA_DIR, "fund_status.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
DIRECT_SALES_FILE = os.path.join(DATA_DIR, "direct_sales.json")


def parse_quota_limit(sgzt_text: str, buy_flag: bool = None):
    """
    严谨购买判断逻辑（经实盘验证）：
    1. 只要状态以“暂停申购”、“暂停交易”、“封闭”开头，或者 buy_flag 为 False：
       无论后面括号写什么，一律为【不能买 (已完全暂停)】，限额为 0 元！
    2. 只有以“限大额”开头且有金额：
       才为【能买 (限额 X 元)】！
    3. 以“开放申购”或“正常”开头：
       为【能买 (不限额)】！
    """
    if not sgzt_text:
        return 0, False, "不能买 (状态未知)", "CANNOT_BUY"

    sgzt = sgzt_text.strip()

    # 1. 如果明确以暂停申购开头，或者系统关闭了购买入口
    if sgzt.startswith("暂停申购") or sgzt.startswith("暂停交易") or sgzt.startswith("封闭") or buy_flag is False:
        return 0, False, "🔴 不能买 (完全暂停)", "CANNOT_BUY"

    # 2. 如果是限大额，提取具体可用额度
    if "限大额" in sgzt or "限购" in sgzt:
        match = re.search(r"上限\s*([\d\.]+)\s*(万)?元", sgzt)
        if match:
            val = float(match.group(1))
            if match.group(2) == "万":
                val *= 10000
            limit_val = int(val) if val.is_integer() else val
            if limit_val > 0:
                return limit_val, True, f"🟡 能买 (限额{limit_val:,}元/日)", "CAN_BUY_LIMITED"

    # 3. 如果是开放申购
    if "开放申购" in sgzt or "正常" in sgzt:
        return 999999999, True, "🟢 能买 (不限额/充足)", "CAN_BUY_OPEN"

    # 其他情况兜底
    return 0, False, "🔴 不能买 (不可申购)", "CANNOT_BUY"


def fetch_single_fund(item: dict) -> dict:
    code = item["code"]
    url = f"https://fundmobapi.eastmoney.com/FundMApi/FundBaseTypeInformation.ashx?FCODE={code}&deviceid=Wap&plat=Wap&product=EFund&version=2.0.0"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://fund.eastmoney.com/{code}.html"
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            resp = r.json()
            data = resp.get("Datas") or {}
            official_name = data.get("SHORTNAME") or item.get("name", "")
            sgzt = data.get("SGZT", "")
            buy_flag = data.get("BUY")
            limit_val, can_buy, status_label, tag = parse_quota_limit(sgzt, buy_flag)
            
            # 严格根据官方名称动态解析，绝不依赖人工猜测
            idx = "标普500" if "500" in official_name else ("纳斯达克科技" if "科技" in official_name else "纳斯达克100")
            if official_name.endswith("A") or "A类" in official_name:
                stype = "A类"
            elif official_name.endswith("C") or "C类" in official_name:
                stype = "C类"
            elif official_name.endswith("I") or "I类" in official_name:
                stype = "I类 (直销专属)"
            elif official_name.endswith("E") or "E类" in official_name:
                stype = "E类"
            else:
                stype = item.get("type", "其他")

            # 检查直销渠道特殊额度配置 (如南方App自营限额200)
            channel_note = ""
            if os.path.exists(DIRECT_SALES_FILE):
                try:
                    with open(DIRECT_SALES_FILE, "r", encoding="utf-8") as f:
                        ds_data = json.load(f)
                        if code in ds_data:
                            cfg = ds_data[code]
                            can_buy = True
                            limit_val = cfg.get("limit", limit_val)
                            status_label = f"🟡 能买 ({cfg.get('channel', '自营App')}限额 {limit_val:,}元/日)"
                            tag = "CAN_BUY_DIRECT"
                            channel_note = cfg.get("note", "")
                except Exception as e:
                    print(f"Error reading direct sales config: {e}")

            return {
                "code": code,
                "name": official_name,
                "index": idx,
                "share_type": stype,
                "currency": item.get("currency", "人民币"),
                "can_buy": can_buy,
                "status_label": status_label,
                "limit_amount": limit_val,
                "status_tag": tag,
                "channel_note": channel_note,
                "sgzt_raw": sgzt,
                "shzt": data.get("SHZT", "--"),
                "nav": data.get("DWJZ", "--"),
                "nav_date": data.get("FSRQ", "--"),
                "day_change": data.get("RZDF", "--"),
                "company": data.get("JJGS", "--"),
                "manager": data.get("JJJL", "--"),
                "min_buy": data.get("MINSG", "10"),
                "fund_size": data.get("ENDNAV", "--"),
                "success": True
            }
    except Exception as e:
        print(f"Error fetching {code}: {e}")

    return {
        "code": code,
        "name": item.get("name", ""),
        "index": item.get("index", "其他"),
        "share_type": item.get("type", "A类"),
        "currency": item.get("currency", "人民币"),
        "sgzt_raw": "拉取失败",
        "limit_amount": 0,
        "limit_category": "获取失败",
        "status_tag": "ERROR",
        "shzt": "--",
        "nav": "--",
        "nav_date": "--",
        "day_change": "--",
        "company": "--",
        "manager": "--",
        "min_buy": "--",
        "fund_size": "--",
        "success": False
    }


def update_all_funds():
    if not os.path.exists(FUNDS_FILE):
        raise FileNotFoundError(f"Missing {FUNDS_FILE}")

    with open(FUNDS_FILE, "r", encoding="utf-8") as f:
        funds = json.load(f)

    os.makedirs(DATA_DIR, exist_ok=True)

    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_single_fund, item): item for item in funds}
        for future in as_completed(futures):
            results.append(future.result())

    # 按限额由大到小排序，0的放最后
    results.sort(
        key=lambda x: (
            1 if x["limit_amount"] > 0 else 0,
            x["limit_amount"]
        ),
        reverse=True
    )

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "updated_at": now_str,
        "count": len(results),
        "funds": results
    }

    # 读取旧状态以比较变动
    changes = []
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                old_data = json.load(f)
                old_funds_map = {f["code"]: f for f in old_data.get("funds", [])}
                for nf in results:
                    code = nf["code"]
                    if code in old_funds_map:
                        of = old_funds_map[code]
                        if of.get("limit_amount") != nf.get("limit_amount") or of.get("sgzt_raw") != nf.get("sgzt_raw"):
                            changes.append({
                                "code": code,
                                "name": nf["name"],
                                "index": nf["index"],
                                "old_limit": of.get("limit_amount"),
                                "old_sgzt": of.get("sgzt_raw"),
                                "new_limit": nf.get("limit_amount"),
                                "new_sgzt": nf.get("sgzt_raw"),
                                "time": now_str
                            })
        except Exception as e:
            print(f"Error reading old status: {e}")

    # 保存最新状态
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # 保存历史变动记录
    history_records = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history_records = json.load(f)
        except Exception:
            history_records = []

    if changes:
        history_records = changes + history_records
        # 保留最近 100 条变动
        history_records = history_records[:100]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history_records, f, ensure_ascii=False, indent=2)

        # 触发微信 PushPlus 通知
        send_pushplus_notification(changes, now_str)

    print(f"Successfully updated {len(results)} funds at {now_str}. Changes detected: {len(changes)}.")
    return payload, changes


def send_pushplus_notification(changes, time_str):
    token = os.environ.get("PUSHPLUS_TOKEN") or "36e8f929dd944cd08d38131e9995b3ad"
    if not token:
        return

    title = f"📢 发现 {len(changes)} 只标普/纳指基金限购额度变动！"
    
    html_items = []
    for c in changes:
        old_val = c.get('old_limit', 0)
        new_val = c.get('new_limit', 0)
        
        # 判断是放宽还是收紧
        if new_val > old_val:
            badge = "<span style='color:green;font-weight:bold;'>【🟢 额度放宽】</span>"
        elif new_val < old_val:
            badge = "<span style='color:red;font-weight:bold;'>【🔴 额度收紧】</span>"
        else:
            badge = "<span style='color:blue;font-weight:bold;'>【🔄 规则变动】</span>"

        old_desc = f"{int(old_val):,}元" if old_val > 0 else "0元(暂停)"
        new_desc = f"{int(new_val):,}元" if new_val > 0 else "0元(暂停)"
        if old_val >= 999999999:
            old_desc = "不限额"
        if new_val >= 999999999:
            new_desc = "不限额"

        html_items.append(f"""
        <div style="border-bottom: 1px solid #eee; padding: 10px 0;">
            <b>{badge} [{c['code']}] {c['name']}</b> ({c['index']})<br>
            • 变动轨迹：<b>{old_desc}</b> ➔ <b style="color:#d32f2f;">{new_desc}</b><br>
            • 官方描述：{c.get('new_sgzt', '--')}
        </div>
        """)

    content = f"""
    <div style="font-family: sans-serif; line-height: 1.6;">
        <h3 style="color: #1976d2; margin-bottom: 5px;">📈 场外QDII指数基金限额异动通报</h3>
        <p style="color: #666; font-size: 13px;">检测时间：{time_str} | 监控标的：59只主流标普/纳指</p>
        {"".join(html_items)}
        <p style="margin-top: 15px; font-size: 13px; color: #888;">
            👉 手机网页随时查看完整明细：<a href="https://qdii-quota-monitor.streamlit.app">qdii-quota-monitor.streamlit.app</a>
        </p>
    </div>
    """

    try:
        url = "http://www.pushplus.plus/send"
        payload = {
            "token": token,
            "title": title,
            "content": content,
            "template": "html"
        }
        res = requests.post(url, json=payload, timeout=8)
        print("PushPlus notification sent status:", res.status_code, res.text[:100])
    except Exception as e:
        print("Error sending PushPlus notification:", e)


if __name__ == "__main__":
    update_all_funds()
