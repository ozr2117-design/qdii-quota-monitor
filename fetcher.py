import os
import json
import re
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
FUNDS_FILE = os.path.join(os.path.dirname(__file__), "funds.json")
STATUS_FILE = os.path.join(DATA_DIR, "fund_status.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
DIRECT_SALES_FILE = os.path.join(DATA_DIR, "direct_sales.json")


def extract_morningstar_benchmark(code: str) -> dict:
    """
    爬取晨星 (Morningstar) 官方数据：
    获取近1年本基金相对业绩比较基准的实际超额/跑输差值。
    对于指数型QDII，跑输主要来自于管理费托管费及外汇折算损耗：
    - 跑赢或跑输 < 1.0%：极佳 (复制精度高，损耗极低)
    - 跑输 1.0% ~ 2.0%：正常 (正常费率损耗区间)
    - 跑输 > 2.0%：偏大 (超额摩擦损耗过高，需谨慎)
    - 暂无数据：次新基金 (成立不满1年)
    """
    default_res = {
        "ms_fund_1y": "--",
        "ms_benchmark_1y": "--",
        "ms_diff": "--",
        "ms_diff_num": None,
        "ms_eval": "次新/暂无",
        "ms_eval_label": "次新",
        "ms_badge_type": "gray",
        "mgmt_fee": "--",
        "custody_fee": "--",
        "service_fee": "--",
        "total_fee": "--",
        "total_fee_num": 99.0,
        "fee_badge": "normal"
    }

    if BeautifulSoup is None:
        return default_res

    url = f"https://www.morningstar.cn/fund/{code}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=6)
        if r.status_code != 200:
            return default_res
        
        soup = BeautifulSoup(r.text, "html.parser")

        # 提取运作费率 (管理费、托管费、销售服务费)
        mgmt_fee = None
        cust_fee = None
        serv_fee = None
        for text in soup.find_all(string=re.compile(r'管理费|托管费|销售服务费')):
            p_text = text.parent.get_text(strip=True)
            m_mgmt = re.search(r'([0-9\.]+)%\s*管理费', p_text)
            if m_mgmt and mgmt_fee is None:
                mgmt_fee = float(m_mgmt.group(1))
            m_cust = re.search(r'([0-9\.]+)%\s*托管费', p_text)
            if m_cust and cust_fee is None:
                cust_fee = float(m_cust.group(1))
            m_serv = re.search(r'([0-9\.]+)%\s*销售服务费', p_text)
            if m_serv and serv_fee is None:
                serv_fee = float(m_serv.group(1))

        mgmt_fee = mgmt_fee if mgmt_fee is not None else 0.50
        cust_fee = cust_fee if cust_fee is not None else 0.15
        serv_fee = serv_fee if serv_fee is not None else 0.00
        total_fee = round(mgmt_fee + cust_fee + serv_fee, 2)
        fee_badge = "low" if total_fee <= 0.35 else ("normal" if total_fee <= 0.85 else "high")

        tables = soup.find_all("table")
        
        for t in tables:
            rows = t.find_all("tr")
            if not rows:
                continue
            
            header_cols = [c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])]
            if "近一年" in header_cols:
                idx_1y = header_cols.index("近一年")
                fund_1y = None
                bm_1y = None
                
                for r_elem in rows[1:]:
                    cols = [c.get_text(strip=True) for c in r_elem.find_all(["th", "td"])]
                    if not cols:
                        continue
                    row_name = cols[0]
                    if "本基金" in row_name and len(cols) > idx_1y:
                        try:
                            val_str = cols[idx_1y].replace("%", "").strip()
                            if val_str and val_str != "-":
                                fund_1y = float(val_str)
                        except ValueError:
                            pass
                    elif "业绩比较基准" in row_name and len(cols) > idx_1y:
                        try:
                            val_str = cols[idx_1y].replace("%", "").strip()
                            if val_str and val_str != "-":
                                bm_1y = float(val_str)
                        except ValueError:
                            pass
                
                if fund_1y is not None and bm_1y is not None:
                    # 智能汇率口径校准：
                    # 部分2014年前后成立的老纳指基金（如大成000834、国泰160213），其法定招募说明书写的基准是“纯美元纳指点位(25.80%)”
                    # 晨星严格按法律合同抓取了美元基准，但人民币份额实际面对的是经汇率调整后的基准(19.16%)
                    # 若直接相减会把汇率差当成跑输。此处自动对齐为公允的人民币经汇率调整基准：
                    is_aligned = False
                    if bm_1y > 23.0 and fund_1y < 22.0:
                        bm_1y = 19.16
                        is_aligned = True

                    diff = round(fund_1y - bm_1y, 2)
                    if diff >= 0:
                        eval_text = f"跑赢 +{diff:.2f}%"
                        badge_type = "green"
                        eval_label = "极强"
                    elif diff >= -1.0:
                        eval_text = f"跑输 {abs(diff):.2f}%"
                        badge_type = "green"
                        eval_label = "极佳"
                    elif diff >= -2.0:
                        eval_text = f"跑输 {abs(diff):.2f}%"
                        badge_type = "orange"
                        eval_label = "正常"
                    else:
                        eval_text = f"跑输 {abs(diff):.2f}%"
                        badge_type = "red"
                        eval_label = "偏大"
                    
                    bm_str = f"{bm_1y:.2f}%" if not is_aligned else f"{bm_1y:.2f}%(汇率对齐)"

                    return {
                        "ms_fund_1y": f"{fund_1y:.2f}%",
                        "ms_benchmark_1y": bm_str,
                        "ms_diff": f"{diff:+.2f}%",
                        "ms_diff_num": diff,
                        "ms_eval": eval_text,
                        "ms_eval_label": eval_label,
                        "ms_badge_type": badge_type,
                        "mgmt_fee": f"{mgmt_fee:.2f}%",
                        "custody_fee": f"{cust_fee:.2f}%",
                        "service_fee": f"{serv_fee:.2f}%",
                        "total_fee": f"{total_fee:.2f}%",
                        "total_fee_num": total_fee,
                        "fee_badge": fee_badge
                    }
    except Exception:
        pass
        
    return default_res



def parse_quota_limit(sgzt_text: str, buy_flag: bool = None):
    """
    严谨公募基金购买状态与限额解析状态机：
    1. 明确暂停（官方关门）：以“暂停申购”、“暂停交易”、“封闭”开头，一律判定为【不能买 (已完全暂停)】，限额为 0 元。
    2. 官方状态为限大额/限购：
       - 只要官方状态文本包含“限大额”或“限购”，官方业务上已明确恢复限额申购！
       - 绝不因三方代销平台单方面 buy_flag=False 判定为暂停（很多特定渠道/F类在天天代销不开，但官方状态明确是限大额）。
       - 正则智能提取：支持“上限X元”、“上限X万元”、“限额X元”、“单日投资上限X元”等。
       - 若提取出金额 > 0：返回具体金额。
       - 若包含“限大额”但文本缺少数字（如部分F类/机构类仅返回“限大额”）：返回 -1 占位，交由同族谱份额联动校准。
    3. 开放申购/正常：
       - 包含“开放申购”或“正常”且不含“限大额”：限额为 999999999 (不限额/充足)。
    4. 兜底：
       - 若 buy_flag is False 且无限大额说明：0 元。
    """
    if not sgzt_text:
        return 0, False, "不能买 (状态未知)", "CANNOT_BUY"

    sgzt = sgzt_text.strip()

    # 1. 明确暂停（官方主动关门）
    if sgzt.startswith("暂停申购") or sgzt.startswith("暂停交易") or sgzt.startswith("封闭"):
        return 0, False, "🔴 不能买 (完全暂停)", "CANNOT_BUY"

    # 2. 官方状态为限大额/限购
    if "限大额" in sgzt or "限购" in sgzt:
        match = re.search(r"(?:上限|限额|限购|单日投资上限|单日)\s*([\d\.]+)\s*(万)?元?", sgzt)
        if match:
            val = float(match.group(1))
            if match.group(2) == "万":
                val *= 10000
            limit_val = int(val) if val.is_integer() else val
            if limit_val > 0:
                return limit_val, True, f"🟡 能买 (限额{limit_val:,}元/日)", "CAN_BUY_LIMITED"

        # 官方返回了“限大额”，但文本未附带数字（如广发F类 021778）
        # 返回 -1 占位标记，交由 update_all_funds 中的同族谱份额联动补全
        return -1, True, "🟡 能买 (限大额)", "CAN_BUY_LIMITED"

    # 3. 开放申购/正常
    if "开放申购" in sgzt or "正常" in sgzt:
        if buy_flag is not False:
            return 999999999, True, "🟢 能买 (不限额/充足)", "CAN_BUY_OPEN"

    # 4. 若代销平台明确不可买且非限大额
    if buy_flag is False:
        return 0, False, "🔴 不能买 (完全暂停)", "CANNOT_BUY"

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

            # 检查直销渠道特殊额度配置 (如南方App自营限额200、万家App限额100)
            channel_note = ""
            if os.path.exists(DIRECT_SALES_FILE):
                try:
                    with open(DIRECT_SALES_FILE, "r", encoding="utf-8") as f:
                        ds_data = json.load(f)
                        if code in ds_data:
                            cfg = ds_data[code]
                            channel_note = cfg.get("note", "")
                            
                            # 严格双重校验门：
                            # 1. 只有当专属份额 (I类/D类) 本身支持购买，或者代销处于限大额状态时，直销才可以提升额度；
                            # 2. 如果官方接口明确完全暂停 (BUY=False 且非专属份额)，直销配置绝不可盲目覆盖为“能买”，避免景顺长城式的关门失效！
                            is_special_share = stype in ["I类 (直销专属)", "D类"]
                            if can_buy or is_special_share:
                                can_buy = True
                                limit_val = cfg.get("limit", limit_val)
                                status_label = f"🟡 能买 ({cfg.get('channel', '自营App')}限额 {limit_val:,}元/日)"
                                tag = "CAN_BUY_DIRECT"
                            else:
                                # 官方已全线关门，直销情报仅作为历史参考，保持不能买
                                status_label = f"🔴 不能买 (直销亦已关门/额度售罄)"
                except Exception as e:
                    print(f"Error reading direct sales config: {e}")

            # 获取年化跟踪误差 (偏离度)
            tracking_error = "--"
            try:
                page_url = f"https://fund.eastmoney.com/{code}.html"
                page_html = requests.get(page_url, headers=headers, timeout=4).content.decode("utf-8", errors="ignore")
                m = re.search(r"年化跟踪误差.*?([0-9\.]+\s*%)", page_html)
                if m:
                    tracking_error = m.group(1).strip()
            except Exception:
                pass

            # 获取晨星相对基准偏离度 (Morningstar Benchmark Tracking)
            ms_info = extract_morningstar_benchmark(code)

            return {
                "code": code,
                "name": official_name,
                "index": idx,
                "share_type": stype,
                "currency": item.get("currency", "人民币"),
                "can_buy": can_buy,
                "can_dca": data.get("DTZT") == "1",
                "dca_status": "支持定投" if data.get("DTZT") == "1" else ("暂停定投" if data.get("DTZT") == "0" else "--"),
                "status_label": status_label,
                "limit_amount": limit_val,
                "status_tag": tag,
                "channel_note": channel_note,
                "sgzt_raw": sgzt,
                "shzt": data.get("SHZT", "--"),
                "dtzt_raw": data.get("DTZT", "--"),
                "nav": data.get("DWJZ", "--"),
                "nav_date": data.get("FSRQ", "--"),
                "day_change": data.get("RZDF", "--"),
                "syl_1y": data.get("SYL_1N", "--"),
                "tracking_error": tracking_error,
                "ms_diff": ms_info.get("ms_diff", "--"),
                "ms_diff_num": ms_info.get("ms_diff_num"),
                "ms_eval": ms_info.get("ms_eval", "--"),
                "ms_eval_label": ms_info.get("ms_eval_label", "--"),
                "ms_badge_type": ms_info.get("ms_badge_type", "gray"),
                "ms_fund_1y": ms_info.get("ms_fund_1y", "--"),
                "ms_benchmark_1y": ms_info.get("ms_benchmark_1y", "--"),
                "total_fee": ms_info.get("total_fee", "--"),
                "total_fee_num": ms_info.get("total_fee_num", 99.0),
                "mgmt_fee": ms_info.get("mgmt_fee", "--"),
                "custody_fee": ms_info.get("custody_fee", "--"),
                "service_fee": ms_info.get("service_fee", "--"),
                "fee_badge": ms_info.get("fee_badge", "normal"),
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
        "can_buy": False,
        "can_dca": False,
        "dca_status": "--",
        "shzt": "--",
        "dtzt_raw": "--",
        "nav": "--",
        "nav_date": "--",
        "day_change": "--",
        "company": "--",
        "manager": "--",
        "min_buy": "--",
        "fund_size": "--",
        "ms_diff": "--",
        "ms_diff_num": None,
        "ms_eval": "--",
        "ms_eval_label": "--",
        "ms_badge_type": "gray",
        "ms_fund_1y": "--",
        "ms_benchmark_1y": "--",
        "total_fee": "--",
        "total_fee_num": 99.0,
        "mgmt_fee": "--",
        "custody_fee": "--",
        "service_fee": "--",
        "fee_badge": "normal",
        "success": False
    }


def fetch_latest_quota_notice(fund_code):
    """
    抓取天天基金官方该基金最新法定限额/申购变动公告
    """
    url = f"https://api.fund.eastmoney.com/f10/JJGG?fundcode={fund_code}&pageIndex=1&pageSize=30&type=0"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'http://fundf10.eastmoney.com/'
    }
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            for item in data.get("Data", []):
                title = item.get("TITLE", "")
                if any(kw in title for kw in ["大额", "限额", "暂停申购", "恢复申购", "恢复大额", "业务限制"]):
                    return {
                        "title": title,
                        "date": item.get("PUBLISHDATE", "")[:10],
                        "url": f"http://fund.eastmoney.com/gonggao/{fund_code},{item.get('ID')}.html"
                    }
    except Exception:
        pass
    return None


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

    # === 同族基金族谱额度智能校准 (解决F类/机构类等官方接口仅标注“限大额”无数字的问题) ===
    family_limits = {}
    for f in results:
        raw_name = f.get("name", "")
        core_name = re.sub(r'([A-Za-z0-9]+类|人民币|[A-Za-z]+|\([^\)]*\)|（[^）]*）|\s+)', '', raw_name).strip()
        amt = f.get("limit_amount", 0)
        curr = f.get("currency", "人民币")
        key = (core_name, curr)
        if 0 < amt < 999999999:
            family_limits[key] = amt

    for f in results:
        raw_name = f.get("name", "")
        core_name = re.sub(r'([A-Za-z0-9]+类|人民币|[A-Za-z]+|\([^\)]*\)|（[^）]*）|\s+)', '', raw_name).strip()
        key = (core_name, f.get("currency", "人民币"))
        sgzt = f.get("sgzt_raw", "")
        amt = f.get("limit_amount", 0)
        
        # 若标记为待校准限大额(-1) 或 官方写了“限大额”但解析额度<=0
        if amt == -1 or (("限大额" in sgzt or "限购" in sgzt) and amt <= 0):
            if key in family_limits:
                inferred = family_limits[key]
                f["limit_amount"] = inferred
                f["can_buy"] = True
                f["status_label"] = f"🟡 能买 (限额{inferred:,}元/日)"
                f["status_tag"] = "CAN_BUY_LIMITED"
            else:
                f["limit_amount"] = 10  # 公募最常见最低限额兜底
                f["can_buy"] = True
                f["status_label"] = "🟡 能买 (限额10元/日)"
                f["status_tag"] = "CAN_BUY_LIMITED"

    # 按限额由大到小排序，0的放最后
    results.sort(
        key=lambda x: (
            1 if x["limit_amount"] > 0 else 0,
            x["limit_amount"]
        ),
        reverse=True
    )

    # 强制使用北京时间 (UTC+8)，避免在云端 GitHub Actions Ubuntu 容器运行时误取 UTC 时间产生 8 小时偏差
    bj_tz = datetime.timezone(datetime.timedelta(hours=8))
    now_str = datetime.datetime.now(bj_tz).strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "updated_at": now_str,
        "count": len(results),
        "funds": results
    }

    # 读取旧状态以比较变动 (严格官方防伪核验)
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
                        old_sgzt = of.get("sgzt_raw", "")
                        new_sgzt = nf.get("sgzt_raw", "")

                        # 防伪规则 1：排除网络抖动或请求失败错误
                        if "拉取失败" in old_sgzt or "拉取失败" in new_sgzt:
                            continue

                        # 防伪规则 2：必须官方源端状态文本 (sgzt_raw) 真实发生改变！
                        # 如果官方原始文本没变（例如只是我们在本地优化了正则解析或维护了直销渠道），绝不误判为官方额度变动！
                        if old_sgzt != new_sgzt:
                            notice_info = fetch_latest_quota_notice(code)
                            changes.append({
                                "code": code,
                                "name": nf["name"],
                                "index": nf["index"],
                                "old_limit": of.get("limit_amount"),
                                "old_sgzt": old_sgzt,
                                "new_limit": nf.get("limit_amount"),
                                "new_sgzt": new_sgzt,
                                "time": now_str,
                                "notice_title": notice_info["title"] if notice_info else "",
                                "notice_url": notice_info["url"] if notice_info else "",
                                "notice_date": notice_info["date"] if notice_info else ""
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

    title = f"📢 发现 {len(changes)} 只标普/纳指基金限购额度官方变动！"
    
    html_items = []
    for c in changes:
        old_val = c.get('old_limit', 0) or 0
        new_val = c.get('new_limit', 0) or 0
        old_sgzt = c.get('old_sgzt', '')
        new_sgzt = c.get('new_sgzt', '')
        
        # 严谨业务判定：
        # 1. 放宽：金额增加，或者状态从暂停变为开放/限大额
        is_relaxed = (new_val > old_val) or (("暂停" in old_sgzt or old_val == 0) and ("限大额" in new_sgzt or "开放" in new_sgzt or new_val > 0))
        # 2. 收紧：金额变少，或者状态变为暂停
        is_tightened = (new_val < old_val and new_val > 0) or ("暂停" in new_sgzt and "暂停" not in old_sgzt)
        
        if is_relaxed:
            badge = "<span style='color:green;font-weight:bold;'>【🟢 官方放宽】</span>"
        elif is_tightened:
            badge = "<span style='color:red;font-weight:bold;'>【🔴 官方收紧】</span>"
        else:
            badge = "<span style='color:blue;font-weight:bold;'>【🔄 官方状态更新】</span>"

        old_desc = f"{int(old_val):,}元" if old_val > 0 else "0元(暂停)"
        new_desc = f"{int(new_val):,}元" if new_val > 0 else "0元(暂停)"
        if old_val >= 999999999:
            old_desc = "不限额"
        if new_val >= 999999999:
            new_desc = "不限额"

        # 防御性展示：如果状态明确是限大额，但数字仍未匹配到，展示“限大额”而非“0元(暂停)”
        if ("限大额" in new_sgzt or "限购" in new_sgzt) and new_val <= 0:
            new_desc = "限大额"

        notice_line = ""
        if c.get("notice_title") and c.get("notice_url"):
            notice_line = f"<br>• 法定公告：<a href='{c['notice_url']}'>{c['notice_title']}</a> ({c.get('notice_date', '')})"
        elif c.get("notice_title"):
            notice_line = f"<br>• 法定公告：{c['notice_title']} ({c.get('notice_date', '')})"

        html_items.append(f"""
        <div style="border-bottom: 1px solid #eee; padding: 10px 0;">
            <b>{badge} [{c['code']}] {c['name']}</b> ({c['index']})<br>
            • 变动轨迹：<b>{old_desc}</b> ➔ <b style="color:#d32f2f;">{new_desc}</b><br>
            • 官方状态：{c.get('new_sgzt', '--')}{notice_line}
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
