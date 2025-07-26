import time
import requests
import datetime
import statistics
import random
import os
import json
import sqlite3

"""
工具函数模块

包含以下功能：
- 配置管理：加载配置文件
- 状态管理：加载和保存运行状态
- 数据库操作：初始化数据库和保存信号记录
- 数据获取：从币安API获取K线数据
- 技术指标计算：EMA、RSI、ATR等指标
- 消息发送：发送飞书消息
"""

# --- 文件路径常量 ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
STATUS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alert_status.json")
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "signals.db")
BINANCE_API = "https://api.binance.com/api/v3/klines"


def load_config():
    """从JSON文件加载配置。"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"错误: 加载配置文件 {CONFIG_FILE} 失败: {e}")
        raise


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
            elif "贴近15mEMA21" in detail:
                conditions['price_near_ema21'] = 1
            elif "ATR放大" in detail:
                conditions['atr_amplified'] = 1
            elif "成交量放大" in detail:
                conditions['volume_amplified'] = 1
            elif "EMA靠近" in detail:
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


def send_feishu_msg(symbol, metrics, direction, score, details, feishu_webhook):
    """发送格式化的飞书消息。"""
    time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 选择最重要的6个条件显示
    key_conditions = details[:6]
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
        response = requests.post(feishu_webhook, json={"msg_type": "text", "content": {"text": body}}, timeout=10)
        response.raise_for_status()
        print(f"[{symbol}] 提醒发送成功")
    except Exception as e:
        print(f"[{symbol}] 发送提醒失败: {e}")