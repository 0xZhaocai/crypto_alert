import time
import requests
import datetime
import statistics
import random
import os
import json
import sqlite3

"""
加密货币价格监控与提醒工具

功能：
1. 监控多个加密货币的价格和技术指标。
2. 根据预设条件（分数、价格变化、RSI等）发送做多/做空信号提醒。
3. 支持通过飞书机器人发送格式化消息。
4. 包含请求重试、超时和全面的错误处理机制。
5. 具备状态记忆功能，避免对同一信号的重复提醒。
6. 内置信号冷静期：信号消失后进入观察期，防止因短期波动导致状态频繁切换。

使用方法：
- 核心配置位于同目录下的 `config.json` 文件。
- 状态记录于同目录下的 `alert_status.json` 文件。
- 建议使用任务计划（如 crontab）定时运行，例如每5分钟一次：
  */5 * * * * python3 /path/to/your/script/alert_15m.py
"""

# --- 全局配置加载 ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
STATUS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alert_status.json")
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "signals.db")

def load_config():
    """从JSON文件加载配置。"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"错误: 加载配置文件 {CONFIG_FILE} 失败: {e}")
        raise

CONFIG = load_config()
TOKEN_CONFIG = CONFIG["tokens"]
FEISHU_WEBHOOK = CONFIG["feishu_webhook"]
COOLDOWN_MINUTES = CONFIG["cooldown_minutes"]
SIGNAL_THRESHOLD = CONFIG["signal_threshold"]
RSI_RANGE = CONFIG["rsi_range"]
PRICE_EMA_GAP_RATIO = CONFIG["price_ema_gap_ratio"]
ATR_RATIO = CONFIG["atr_ratio"]
VOLUME_RATIO = CONFIG["volume_ratio"]
PRICE_CHANGE_THRESHOLD = CONFIG["price_change_threshold"]
SIGNAL_SCORE_CHANGE_THRESHOLD = CONFIG["signal_score_change_threshold"]
EMA_CONVERGENCE_THRESHOLD = CONFIG["ema_convergence_threshold"]
EMA_CONVERGENCE_SCORE = CONFIG["ema_convergence_score"]
RSI_CHANGE_THRESHOLD = CONFIG["rsi_change_threshold"]

BINANCE_API = "https://api.binance.com/api/v3/klines"

# --- 状态管理函数 ---
def load_status():
    """从JSON文件加载运行状态。"""
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r') as f:
                data = json.load(f)
                # 将ISO格式的字符串时间转换回datetime对象
                for symbol in data:
                    if data[symbol].get("signal_disappeared_time"):
                        data[symbol]["signal_disappeared_time"] = datetime.datetime.fromisoformat(data[symbol]["signal_disappeared_time"])
                return data
        except Exception as e:
            print(f"警告: 加载状态文件 {STATUS_FILE} 失败: {e}")
    return {}

def save_status(status):
    """将运行状态保存到JSON文件。"""
    try:
        data_to_save = status.copy()
        # 将datetime对象转换为ISO格式的字符串以便JSON序列化
        for symbol in data_to_save:
            if data_to_save[symbol].get("signal_disappeared_time"):
                data_to_save[symbol]["signal_disappeared_time"] = data_to_save[symbol]["signal_disappeared_time"].isoformat()
        
        with open(STATUS_FILE, 'w') as f:
            json.dump(data_to_save, f, indent=2)
    except Exception as e:
        print(f"错误: 保存状态文件 {STATUS_FILE} 失败: {e}")

# --- 数据库管理函数 ---
def init_database():
    """初始化SQLite数据库和表结构。"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signal_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                direction TEXT NOT NULL,
                score INTEGER NOT NULL,
                price REAL NOT NULL,
                price_above_ema21_15m INTEGER DEFAULT 0,
                price_above_ema21_1h INTEGER DEFAULT 0,
                price_below_ema21_15m INTEGER DEFAULT 0,
                price_below_ema21_1h INTEGER DEFAULT 0,
                rsi_in_range INTEGER DEFAULT 0,
                price_near_ema21 INTEGER DEFAULT 0,
                atr_amplified INTEGER DEFAULT 0,
                volume_amplified INTEGER DEFAULT 0,
                ema_convergence INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("数据库初始化成功")
    except Exception as e:
        print(f"数据库初始化失败: {e}")

def save_signal_record(symbol, direction, score, metrics, details):
    """保存信号记录到数据库。"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 解析details中的条件
        conditions = {
            'price_above_ema21_15m': 0,
            'price_above_ema21_1h': 0,
            'price_below_ema21_15m': 0,
            'price_below_ema21_1h': 0,
            'rsi_in_range': 0,
            'price_near_ema21': 0,
            'atr_amplified': 0,
            'volume_amplified': 0,
            'ema_convergence': 0
        }
        
        for detail in details:
            if "价格 > EMA21(15m)" in detail:
                conditions['price_above_ema21_15m'] = 1
            elif "价格 > EMA21(1h)" in detail:
                conditions['price_above_ema21_1h'] = 1
            elif "价格 < EMA21(15m)" in detail:
                conditions['price_below_ema21_15m'] = 1
            elif "价格 < EMA21(1h)" in detail:
                conditions['price_below_ema21_1h'] = 1
            elif "RSI在区间内" in detail:
                conditions['rsi_in_range'] = 1
            elif "价格贴近15mEMA21" in detail:
                conditions['price_near_ema21'] = 1
            elif "ATR放大" in detail:
                conditions['atr_amplified'] = 1
            elif "成交量放大" in detail:
                conditions['volume_amplified'] = 1
            elif "EMA9/21靠近" in detail:
                conditions['ema_convergence'] = 1
        
        cursor.execute('''
            INSERT INTO signal_records (
                symbol, timestamp, direction, score, price,
                price_above_ema21_15m, price_above_ema21_1h,
                price_below_ema21_15m, price_below_ema21_1h,
                rsi_in_range, price_near_ema21, atr_amplified,
                volume_amplified, ema_convergence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            symbol,
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            direction,
            score,
            metrics['price'],
            conditions['price_above_ema21_15m'],
            conditions['price_above_ema21_1h'],
            conditions['price_below_ema21_15m'],
            conditions['price_below_ema21_1h'],
            conditions['rsi_in_range'],
            conditions['price_near_ema21'],
            conditions['atr_amplified'],
            conditions['volume_amplified'],
            conditions['ema_convergence']
        ))
        
        conn.commit()
        conn.close()
        print(f"[{symbol}] 信号记录已保存到数据库")
    except Exception as e:
        print(f"[{symbol}] 保存信号记录失败: {e}")

# --- 数据获取与技术指标计算 ---
def get_klines(symbol, interval, limit=50, max_retries=3):
    """从币安API获取K线数据，包含重试机制。"""
    url = f"{BINANCE_API}?symbol={symbol}&interval={interval}&limit={limit}"
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                delay = 1 + random.random()
                print(f"[{symbol}] 第{attempt+1}次尝试获取数据，等待{delay:.2f}秒...")
                time.sleep(delay)
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[{symbol}] 请求异常 (第{attempt+1}次): {e}")
            if attempt == max_retries - 1:
                raise
        except ValueError as e:
            print(f"[{symbol}] JSON解析错误 (第{attempt+1}次): {e}")
            if attempt == max_retries - 1:
                raise

def ema(data, period=21):
    """计算指数移动平均线 (EMA)。"""
    ema_values = []
    k = 2 / (period + 1)
    for i, price in enumerate(data):
        if len(ema_values) == 0:
            # 使用简单移动平均作为第一个EMA值
            sma = sum(data[:period]) / period
            ema_values.append(sma)
        else:
            ema_values.append(price * k + ema_values[-1] * (1 - k))
    return ema_values[-1]

def rsi(data, period=14):
    """计算相对强弱指数 (RSI)。"""
    deltas = [data[i] - data[i - 1] for i in range(1, len(data))]
    gains = [x if x > 0 else 0 for x in deltas]
    losses = [-x if x < 0 else 0 for x in deltas]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def atr(data, period=14):
    """计算平均真实波幅 (ATR)。"""
    trs = []
    for i in range(1, len(data)):
        high = float(data[i][2])
        low = float(data[i][3])
        close_prev = float(data[i - 1][4])
        tr = max(high - low, abs(high - close_prev), abs(low - close_prev))
        trs.append(tr)
    return statistics.mean(trs[-period:]) if trs else 0

def get_current_metrics(symbol):
    """获取并计算一个代币的所有当前技术指标。"""
    try:
        klines_5m = get_klines(symbol, "5m")
        klines_15m = get_klines(symbol, "15m")
        klines_1h = get_klines(symbol, "1h")

        if len(klines_5m) < 21 or len(klines_15m) < 21 or len(klines_1h) < 21:
            raise Exception(f"K线数据不足")

        closes_5m = [float(x[4]) for x in klines_5m]
        closes_15m = [float(x[4]) for x in klines_15m]
        closes_1h = [float(x[4]) for x in klines_1h]
        volumes_5m = [float(x[5]) for x in klines_5m]

        price = closes_5m[-1]
        atr_5m_val = atr(klines_5m, 14)
        
        # 计算各周期的EMA9和EMA21
        ema9_5m = ema(closes_5m, 9)
        ema21_5m = ema(closes_5m, 21)
        ema9_15m = ema(closes_15m, 9)
        ema21_15m = ema(closes_15m, 21)
        ema9_1h = ema(closes_1h, 9)
        ema21_1h = ema(closes_1h, 21)
        
        # 计算各周期EMA9与EMA21的靠近度
        ema_convergence_5m = abs(ema9_5m - ema21_5m) / ema21_5m
        ema_convergence_15m = abs(ema9_15m - ema21_15m) / ema21_15m
        ema_convergence_1h = abs(ema9_1h - ema21_1h) / ema21_1h
        
        return {
            "price": price,
            "ema9_5m": ema9_5m,
            "ema21_5m": ema21_5m,
            "ema9_15m": ema9_15m,
            "ema21_15m": ema21_15m,
            "ema9_1h": ema9_1h,
            "ema21_1h": ema21_1h,
            "rsi_5m": rsi(closes_5m, 14),
            "atr_ratio": atr_5m_val / statistics.mean([atr(klines_5m[-15 - i:-i], 14) for i in range(1, 6)]),
            "volume_ratio": volumes_5m[-1] / statistics.mean(volumes_5m[-21:]),
            "price_ema_gap_ratio": abs(price - ema21_15m) / ema21_15m,
            "ema_convergence_5m": ema_convergence_5m,
            "ema_convergence_15m": ema_convergence_15m,
            "ema_convergence_1h": ema_convergence_1h,
        }
    except Exception as e:
        # 将原始异常包装后重新抛出，以便上层捕获
        raise Exception(f"计算{symbol}指标失败: {e}") from e

def evaluate_signals(metrics):
    """根据各项指标为多空方向评分。"""
    long_score, short_score = 0, 0
    long_details, short_details = [], []

    # 做多信号评分
    if metrics["price"] > metrics["ema21_15m"]:
        long_score += 2; long_details.append("价格 > EMA21(15m): +2")
    if metrics["price"] > metrics["ema21_1h"]:
        long_score += 2; long_details.append("价格 > EMA21(1h): +2")
    if RSI_RANGE["min"] <= metrics["rsi_5m"] <= RSI_RANGE["max"]:
        long_score += 1; long_details.append(f"RSI在区间内({metrics['rsi_5m']:.2f}): +1")
    if metrics["price_ema_gap_ratio"] < PRICE_EMA_GAP_RATIO:
        long_score += 1; long_details.append(f"价格贴近15mEMA21({metrics['price_ema_gap_ratio']:.3%}): +1")
    if metrics["atr_ratio"] >= ATR_RATIO:
        long_score += 2; long_details.append(f"ATR放大({metrics['atr_ratio']:.2f}x): +2")
    if metrics["volume_ratio"] >= VOLUME_RATIO:
        long_score += 2; long_details.append(f"成交量放大({metrics['volume_ratio']:.2f}x): +2")
    
    # EMA靠近度评分（任一周期EMA9与EMA21靠近都给分）
    ema_convergence_count = 0
    if metrics["ema_convergence_5m"] < EMA_CONVERGENCE_THRESHOLD:
        ema_convergence_count += 1
    if metrics["ema_convergence_15m"] < EMA_CONVERGENCE_THRESHOLD:
        ema_convergence_count += 1
    if metrics["ema_convergence_1h"] < EMA_CONVERGENCE_THRESHOLD:
        ema_convergence_count += 1
    
    if ema_convergence_count > 0:
        long_score += EMA_CONVERGENCE_SCORE
        long_details.append(f"EMA9/21靠近: +{EMA_CONVERGENCE_SCORE}")

    # 做空信号评分
    if metrics["price"] < metrics["ema21_15m"]:
        short_score += 2; short_details.append("价格 < EMA21(15m): +2")
    if metrics["price"] < metrics["ema21_1h"]:
        short_score += 2; short_details.append("价格 < EMA21(1h): +2")
    if RSI_RANGE["min"] <= metrics["rsi_5m"] <= RSI_RANGE["max"]:
        short_score += 1; short_details.append(f"RSI在区间内({metrics['rsi_5m']:.2f}): +1")
    if metrics["price_ema_gap_ratio"] < PRICE_EMA_GAP_RATIO:
        short_score += 1; short_details.append(f"价格贴近15mEMA21({metrics['price_ema_gap_ratio']:.3%}): +1")
    if metrics["atr_ratio"] >= ATR_RATIO:
        short_score += 2; short_details.append(f"ATR放大({metrics['atr_ratio']:.2f}x): +2")
    if metrics["volume_ratio"] >= VOLUME_RATIO:
        short_score += 2; short_details.append(f"成交量放大({metrics['volume_ratio']:.2f}x): +2")
    
    # EMA靠近度评分（任一周期EMA9与EMA21靠近都给分）
    if ema_convergence_count > 0:
        short_score += EMA_CONVERGENCE_SCORE
        short_details.append(f"EMA9/21靠近: +{EMA_CONVERGENCE_SCORE}")

    return long_score, short_score, long_details, short_details

def should_send_alert(symbol, metrics, direction, score, alert_status):
    """
    判断是否应该发送提醒。
    核心思想：任何一次提醒，都必须与上一次提醒的价格有显著变化。
    """
    # 1. 首要条件：检查价格自上次提醒后，是否有足够的变化。
    #    只要 alert_status 中有上次提醒的价格 (last_price > 0)，此条必须满足，否则一票否决。
    if alert_status["last_price"] > 0:
        price_change = abs(metrics["price"] - alert_status["last_price"]) / alert_status["last_price"]
        if price_change < PRICE_CHANGE_THRESHOLD:
            print(f"[{symbol}] 价格自上次提醒({alert_status['last_price']:.4f})后变化不足({price_change:.2%})，不发送新提醒")
            return False

    # 2. 基础条件：检查其他必要指标是否达标。
    #    只有在价格变化达标（或首次运行时）后，才检查这些。
    if not (RSI_RANGE["min"] <= metrics["rsi_5m"] <= RSI_RANGE["max"]):
        print(f"[{symbol}] RSI({metrics['rsi_5m']:.2f})不在区间内({RSI_RANGE['min']}-{RSI_RANGE['max']})，信号质量不高，不发送")
        return False
        
    if metrics["price_ema_gap_ratio"] >= PRICE_EMA_GAP_RATIO:
        print(f"[{symbol}] 价格偏离EMA({metrics['price_ema_gap_ratio']:.3%})超过阈值({PRICE_EMA_GAP_RATIO:.3%})，信号质量不高，不发送")
        return False
        
    # 如果通过了以上所有关卡，说明这是一个值得发送的、状态有实际变化的信号
    signal_is_active = alert_status.get('long', False) or alert_status.get('short', False)
    if not signal_is_active:
         print(f"[{symbol}] 首次触发信号，且所有条件满足，准备发送提醒。")
    else:
         print(f"[{symbol}] 价格变化显著，且信号条件依然满足，准备发送更新提醒。")

    return True

def send_feishu_msg(symbol, metrics, direction, score, details):
    """发送格式化的飞书消息。"""
    time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 选择最重要的4个条件显示
    key_conditions = details[:6]  # 取前4个条件
    conditions_text = "\n".join([f"✅ {detail.split(': +')[0]}" for detail in key_conditions])
    
    body = f"""{symbol}
🎯 信号：{score}
💰 价格：{metrics['price']:.4f} 
🕒 时间：{time_str}

{conditions_text}"""

    print(f"[{symbol}] 发送提醒：【{direction}】分数: {score}")
    
    # 保存信号记录到数据库
    save_signal_record(symbol, direction, score, metrics, details)
    
    try:
        response = requests.post(FEISHU_WEBHOOK, json={"msg_type": "text", "content": {"text": body}}, timeout=10)
        response.raise_for_status()
        print(f"[{symbol}] 提醒发送成功")
    except Exception as e:
        print(f"[{symbol}] 发送提醒失败: {e}")

def main():
    """主执行函数。"""
    print(f"开始检查... 当前时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"监控代币: {', '.join([token['symbol'] for token in TOKEN_CONFIG])}")
    
    # 初始化数据库
    init_database()
    
    ALERT_STATUS = load_status()
    
    # 初始化新代币的状态
    for token in TOKEN_CONFIG:
        if token["symbol"] not in ALERT_STATUS:
            ALERT_STATUS[token["symbol"]] = {
                "long": False, "short": False, "last_long_score": 0, "last_short_score": 0,
                "error_count": 0, "signal_disappeared_time": None, "last_price": 0, "last_rsi": 0,
            }
    
    for token in TOKEN_CONFIG:
        symbol = token["symbol"]
        try:
            if ALERT_STATUS[symbol]["error_count"] > 0:
                print(f"[{symbol}] 尝试恢复，之前连续失败次数: {ALERT_STATUS[symbol]['error_count']}")
            
            print(f"获取 {symbol} 指标中...")
            metrics = get_current_metrics(symbol)
            long_score, short_score, long_details, short_details = evaluate_signals(metrics)

            print(f"[{symbol}] 当前价格: {metrics['price']:.4f}")
            print(f"[{symbol}] 做多得分: {long_score}")
            for detail in long_details: print(f"[{symbol}] 做多 - {detail}")
            print(f"[{symbol}] 做空得分: {short_score}")
            for detail in short_details: print(f"[{symbol}] 做空 - {detail}")
            
            ALERT_STATUS[symbol]["error_count"] = 0 # 成功获取数据后，重置错误计数
            
            if long_score >= SIGNAL_THRESHOLD:
                if should_send_alert(symbol, metrics, "long", long_score, ALERT_STATUS[symbol]):
                    send_feishu_msg(token["name"], metrics, "多", long_score, long_details)
                    ALERT_STATUS[symbol].update({
                        "long": True, "short": False, "signal_disappeared_time": datetime.datetime.now(),
                        "last_price": metrics["price"], "last_rsi": metrics["rsi_5m"]
                    })
                    print(f"[{symbol}] 做多信号触发，进入{COOLDOWN_MINUTES}分钟观察期...")
                else:
                    if ALERT_STATUS[symbol]["signal_disappeared_time"]:
                        end_time = ALERT_STATUS[symbol]["signal_disappeared_time"] + datetime.timedelta(minutes=COOLDOWN_MINUTES)
                        print(f"[{symbol}] 做多得分: {long_score}，但信号条件不满足，不发送（观察期结束: {end_time.strftime('%H:%M:%S')}）")
                    else:
                        print(f"[{symbol}] 做多得分: {long_score}，但信号条件不满足，不发送")
                ALERT_STATUS[symbol]["last_long_score"] = long_score

            elif short_score >= SIGNAL_THRESHOLD:
                if should_send_alert(symbol, metrics, "short", short_score, ALERT_STATUS[symbol]):
                    send_feishu_msg(token["name"], metrics, "空", short_score, short_details)
                    ALERT_STATUS[symbol].update({
                        "short": True, "long": False, "signal_disappeared_time": datetime.datetime.now(),
                        "last_price": metrics["price"], "last_rsi": metrics["rsi_5m"]
                    })
                    print(f"[{symbol}] 做空信号触发，进入{COOLDOWN_MINUTES}分钟观察期...")
                else:
                    if ALERT_STATUS[symbol]["signal_disappeared_time"]:
                        end_time = ALERT_STATUS[symbol]["signal_disappeared_time"] + datetime.timedelta(minutes=COOLDOWN_MINUTES)
                        print(f"[{symbol}] 做空得分: {short_score}，但信号条件不满足，不发送（观察期结束: {end_time.strftime('%H:%M:%S')}）")
                    else:
                        print(f"[{symbol}] 做空得分: {short_score}，但信号条件不满足，不发送")
                ALERT_STATUS[symbol]["last_short_score"] = short_score
                
            else: # 当前分数不满足任何阈值，检查是否需要重置旧信号
                cooldown_period = datetime.timedelta(minutes=COOLDOWN_MINUTES)
                now = datetime.datetime.now()
                
                # 检查并重置已过期的做多信号
                if ALERT_STATUS[symbol]["long"] and ALERT_STATUS[symbol]["signal_disappeared_time"]:
                    if now - ALERT_STATUS[symbol]["signal_disappeared_time"] > cooldown_period:
                        ALERT_STATUS[symbol].update({"long": False, "signal_disappeared_time": None, "last_long_score": 0})
                        print(f"[{symbol}] 做多信号观察期结束，已重置状态。")

                # 检查并重置已过期的做空信号
                if ALERT_STATUS[symbol]["short"] and ALERT_STATUS[symbol]["signal_disappeared_time"]:
                    if now - ALERT_STATUS[symbol]["signal_disappeared_time"] > cooldown_period:
                        ALERT_STATUS[symbol].update({"short": False, "signal_disappeared_time": None, "last_short_score": 0})
                        print(f"[{symbol}] 做空信号观察期结束，已重置状态。")
            
            print() # 分隔不同代币的日志
            
        except Exception as e:
            ALERT_STATUS[symbol]["error_count"] += 1
            print(f"[{symbol}] 处理失败 (连续第{ALERT_STATUS[symbol]['error_count']}次): {e}")
            print()
            
            # 连续失败3次后发送警告
            if ALERT_STATUS[symbol]["error_count"] == 3:
                try:
                    error_msg = f"⚠️ 警告: {symbol}连续3次处理失败，请检查。\n最后错误: {e}"
                    requests.post(FEISHU_WEBHOOK, json={"msg_type": "text", "content": {"text": error_msg}}, timeout=10)
                except Exception as notify_err:
                    print(f"发送错误通知失败: {notify_err}")
    
    save_status(ALERT_STATUS)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n发生严重错误，程序异常退出: {e}")
        try:
            error_msg = f"🚨 严重错误: 监控程序异常退出。\n错误信息: {e}"
            requests.post(FEISHU_WEBHOOK, json={"msg_type": "text", "content": {"text": error_msg}}, timeout=10)
        except:
            pass
        raise