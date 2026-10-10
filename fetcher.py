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


def parse_quota_limit(sgzt_text: str):
    """
    从申购状态文字中解析限额数值与分类
    例如：
    - "暂停申购(单日投资上限100元)" -> 100, "严厉限额(≤100元)"
    - "暂停申购(单日投资上限10元)" -> 10, "极度限额(≤10元)"
    - "限大额(单日投资上限1000元)" -> 1000, "常规限额(≤1000元)"
    - "暂停申购" -> 0, "暂停申购"
    - "开放申购" -> 999999999, "开放申购"
    """
    if not sgzt_text:
        return 0, "未知状态", "暂停申购"

    sgzt = sgzt_text.strip()
    match = re.search(r"上限\s*([\d\.]+)\s*(万)?元", sgzt)
    if match:
        val = float(match.group(1))
        if match.group(2) == "万":
            val *= 10000
        
        limit_val = int(val) if val.is_integer() else val
        if limit_val <= 10:
            category = "极度限额(≤10元)"
            tag = "LIMIT_10"
        elif limit_val <= 100:
            category = "严厉限额(≤100元)"
            tag = "LIMIT_100"
        elif limit_val <= 1000:
            category = "适度限额(≤1000元)"
            tag = "LIMIT_1000"
        elif limit_val <= 10000:
            category = "宽松限额(≤1万元)"
            tag = "LIMIT_10000"
        else:
            category = f"大额限额(≤{limit_val}元)"
            tag = "LIMIT_LARGE"
        return limit_val, category, tag

    if "暂停申购" in sgzt or "暂停交易" in sgzt or "封闭" in sgzt:
        return 0, "暂停申购", "SUSPENDED"

    if "开放申购" in sgzt or "正常" in sgzt:
        return 999999999, "开放申购(充足)", "OPEN"

    return 0, sgzt, "OTHER"


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
            sgzt = data.get("SGZT", "")
            limit_val, category, tag = parse_quota_limit(sgzt)
            
            return {
                "code": code,
                "name": data.get("SHORTNAME") or item.get("name", ""),
                "index": item.get("index", "其他"),
                "share_type": item.get("type", "A类"),
                "currency": item.get("currency", "人民币"),
                "sgzt_raw": sgzt,
                "limit_amount": limit_val,
                "limit_category": category,
                "status_tag": tag,
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

    print(f"Successfully updated {len(results)} funds at {now_str}. Changes detected: {len(changes)}.")
    return payload, changes


if __name__ == "__main__":
    update_all_funds()
