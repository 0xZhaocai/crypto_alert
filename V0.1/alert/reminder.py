import time
import requests
import datetime
import statistics
import random
import platform
import os

"""
加密货币价格监控与提醒工具

功能：
1. 监控多个加密货币的价格和技术指标
2. 根据预设条件发送做多/做空信号提醒
3. 支持飞书消息通知和声音提醒
4. 自动重试和错误处理机制
5. 信号冷静期功能：当信号消失后，不会立即重置状态，而是等待15分钟的冷静期
   这样可以避免因短期波动导致的频繁提醒，提高信号质量

使用方法：
- 直接运行此脚本开始监控
- 可在配置区域修改监控的代币和检查间隔
- Windows系统需安装playsound库以支持声音提醒功能

"""

# 根据平台选择合适的声音播放方式
system_platform = platform.system()
if system_platform == "Darwin":  # macOS
    try:
        import subprocess
        def play_sound(sound_path):
            if os.path.exists(sound_path):
                try:
                    subprocess.call(["afplay", sound_path])
                    return True
                except Exception as e:
                    print(f"使用afplay播放声音失败: {e}")
                    return False
            else:
                print(f"声音文件不存在: {sound_path}")
                return False
    except Exception as e:
        print(f"初始化声音播放功能失败: {e}")
        def play_sound(sound_path):
            print("声音播放功能不可用")
            return False
else:  # Windows或其他系统
    try:
        from playsound import playsound
        def play_sound(sound_path):
            try:
                playsound(sound_path)
                return True
            except Exception as e:
                print(f"播放声音失败: {e}")
                return False
    except ImportError:
        print("playsound模块导入失败，声音提醒功能不可用")
        def play_sound(sound_path):
            print("声音播放功能不可用")
            return False

# ========== 配置区域 START ========== #
TOKEN_CONFIG = [
    {"symbol": "BTCUSDT", "name": "BTC"},
    {"symbol": "ETHUSDT", "name": "ETH"},
    {"symbol": "SOLUSDT", "name": "SOL"},
    {"symbol": "XRPUSDT", "name": "XRP"},
    {"symbol": "AVAXUSDT", "name": "AVAX"},
]

FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/891de003-fc6f-4991-8088-519d4816e23a"
# 检查间隔（分钟）
CHECK_INTERVAL_MINUTES = 5

# 使用绝对路径引用声音文件
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SOUND_PATH = os.path.join(SCRIPT_DIR, "yinxiao.mp3")
# ========== 配置区域 END ========== #

# 用于跟踪每个代币的提醒状态
ALERT_STATUS = {}

BINANCE_API = "https://api.binance.com/api/v3/klines"

def get_klines(symbol, interval, limit=50, max_retries=3):
    url = f"{BINANCE_API}?symbol={symbol}&interval={interval}&limit={limit}"
    
    for attempt in range(max_retries):
        try:
            # 添加随机延迟，避免同时请求
            if attempt > 0:
                delay = 1 + random.random()
                print(f"[{symbol}] 第{attempt+1}次尝试获取数据，等待{delay:.2f}秒...")
                time.sleep(delay)
                
            response = requests.get(url, timeout=10)  # 添加超时设置
            response.raise_for_status()  # 检查HTTP错误
            data = response.json()
            return data
            
        except requests.exceptions.SSLError as e:
            print(f"[{symbol}] SSL错误: {e}")
            if attempt == max_retries - 1:
                raise Exception(f"SSL连接错误，已重试{max_retries}次: {e}")
                
        except requests.exceptions.ConnectionError as e:
            print(f"[{symbol}] 连接错误: {e}")
            if attempt == max_retries - 1:
                raise Exception(f"连接错误，已重试{max_retries}次: {e}")
                
        except requests.exceptions.Timeout as e:
            print(f"[{symbol}] 请求超时: {e}")
            if attempt == max_retries - 1:
                raise Exception(f"请求超时，已重试{max_retries}次: {e}")
                
        except requests.exceptions.RequestException as e:
            print(f"[{symbol}] 请求异常: {e}")
            if attempt == max_retries - 1:
                raise Exception(f"请求异常，已重试{max_retries}次: {e}")
                
        except ValueError as e:
            # JSON解析错误
            print(f"[{symbol}] JSON解析错误: {e}")
            if attempt == max_retries - 1:
                raise Exception(f"JSON解析错误，已重试{max_retries}次: {e}")
    
    # 如果所有重试都失败
    raise Exception(f"获取{symbol}数据失败，已重试{max_retries}次")

def ema(data, period=21):
    ema_values = []
    k = 2 / (period + 1)
    for i in range(len(data)):
        if i < period - 1:
            ema_values.append(None)
        elif i == period - 1:
            sma = sum(data[i + 1 - period:i + 1]) / period
            ema_values.append(sma)
        else:
            ema_values.append(data[i] * k + ema_values[-1] * (1 - k))
    return ema_values[-1]

def rsi(data, period=14):
    deltas = [data[i] - data[i - 1] for i in range(1, len(data))]
    gains = [x if x > 0 else 0 for x in deltas]
    losses = [-x if x < 0 else 0 for x in deltas]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def atr(data, period=14):
    trs = []
    for i in range(1, len(data)):
        high = float(data[i][2])
        low = float(data[i][3])
        close_prev = float(data[i - 1][4])
        tr = max(high - low, abs(high - close_prev), abs(low - close_prev))
        trs.append(tr)
    return statistics.mean(trs[-period:])

def get_current_metrics(symbol, max_retries=3):
    print(f"获取 {symbol} 指标中...")
    try:
        klines_5m = get_klines(symbol, "5m", max_retries=max_retries)
        klines_15m = get_klines(symbol, "15m", max_retries=max_retries)
        klines_1h = get_klines(symbol, "1h", max_retries=max_retries)

        # 检查数据是否足够
        if len(klines_5m) < 21 or len(klines_15m) < 21 or len(klines_1h) < 21:
            raise Exception(f"获取的K线数据不足: 5m={len(klines_5m)}, 15m={len(klines_15m)}, 1h={len(klines_1h)}")

        closes_5m = [float(x[4]) for x in klines_5m]
        closes_15m = [float(x[4]) for x in klines_15m]
        closes_1h = [float(x[4]) for x in klines_1h]
        volumes_5m = [float(x[5]) for x in klines_5m]

        price = closes_5m[-1]
        ema21_5m = ema(closes_5m, 21)
        ema21_15m = ema(closes_15m, 21)
        ema21_1h = ema(closes_1h, 21)
        rsi_5m = rsi(closes_5m, 14)
        atr_5m = atr(klines_5m, 14)
        atr_5m_sma = statistics.mean([atr(klines_5m[-15 - i:-i], 14) for i in range(1, 6)])
        volume_5m_sma = statistics.mean(volumes_5m[-21:])
        volume_5m = volumes_5m[-1]

        return {
            "price": price,
            "ema21_5m": ema21_5m,
            "ema21_15m": ema21_15m,
            "ema21_1h": ema21_1h,
            "rsi_5m": rsi_5m,
            "atr_ratio": atr_5m / atr_5m_sma,
            "volume_ratio": volume_5m / volume_5m_sma,
            "price_ema_gap_ratio": abs(price - ema21_5m) / ema21_5m,
        }
    except Exception as e:
        # 重新抛出异常，添加更多上下文信息
        raise Exception(f"计算{symbol}指标失败: {e}")

def evaluate_signals(metrics):
    long_score = 0
    short_score = 0

    if metrics["price"] > metrics["ema21_15m"]:
        long_score += 2
    if metrics["price"] > metrics["ema21_1h"]:
        long_score += 2
    if 40 <= metrics["rsi_5m"] <= 60:
        long_score += 1
    if metrics["price_ema_gap_ratio"] < 0.003:
        long_score += 1
    if metrics["atr_ratio"] >= 1.1:
        long_score += 2
    if metrics["volume_ratio"] >= 1.3:
        long_score += 2

    if metrics["price"] < metrics["ema21_15m"]:
        short_score += 2
    if metrics["price"] < metrics["ema21_1h"]:
        short_score += 2
    if 40 <= metrics["rsi_5m"] <= 60:
        short_score += 1
    if metrics["price_ema_gap_ratio"] < 0.003:
        short_score += 1
    if metrics["atr_ratio"] >= 1.1:
        short_score += 2
    if metrics["volume_ratio"] >= 1.3:
        short_score += 2

    return long_score, short_score

def send_feishu_msg(symbol, metrics, direction, score):
    time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    is_long = direction == "多"  # 修改这里，从"做多"改为"多"
    direction_icon = "📈" if is_long else "📉"
    cond_15m = metrics["price"] > metrics["ema21_15m"] if is_long else metrics["price"] < metrics["ema21_15m"]
    cond_1h = metrics["price"] > metrics["ema21_1h"] if is_long else metrics["price"] < metrics["ema21_1h"]
    cond_rsi = 40 <= metrics["rsi_5m"] <= 60
    cond_gap = metrics["price_ema_gap_ratio"] < 0.003
    cond_atr = metrics["atr_ratio"] >= 1.1
    cond_vol = metrics["volume_ratio"] >= 1.3

    body = f"""
    {symbol} 触发盯盘
    🕒 时间：{time_str} 
    {direction_icon} 趋势：{direction} 
    💰 价格：{metrics['price']:.2f} 
    🎯 信号条件：{score}/10
    {'✅' if cond_15m else '- '}价格 {'>' if is_long else '<'} EMA21（15m） 
    {'✅' if cond_1h else '- '}价格 {'>' if is_long else '<'} EMA21（1H）
    {'✅' if cond_rsi else '- '}RSI 区间（{metrics['rsi_5m']:.2f}）
    {'✅' if cond_gap else '- '}贴近5m均线（{metrics['ema21_5m']:.2f}）
    {'✅' if cond_atr else '- '}ATR 放大（{metrics['atr_ratio']:.2f}x）
    {'✅' if cond_vol else '- '}成交量放大（{metrics['volume_ratio']:.2f}x）
        """
    print(f"[{symbol}] 发送提醒：【{direction}】分数: {score}")
    
    # 添加错误处理，确保消息发送的可靠性
    try:
        response = requests.post(FEISHU_WEBHOOK, json={"msg_type": "text", "content": {"text": body}}, timeout=10)
        response.raise_for_status()
        print(f"[{symbol}] 提醒发送成功")
    except Exception as e:
        print(f"[{symbol}] 发送提醒失败: {e}")

    # if score >= 8:
    #     try:
    #         play_sound(SOUND_PATH)
    #     except Exception as e:
    #         print(f"播放声音失败: {e}")

def main_loop():
    # 初始化提醒状态，增加 signal_disappeared_time 字段用于冷静期计时
    for token in TOKEN_CONFIG:
        ALERT_STATUS[token["symbol"]] = {
            "long": False,  # 是否已经发送过做多提醒
            "short": False,  # 是否已经发送过做空提醒
            "last_long_score": 0,  # 上次做多得分
            "last_short_score": 0,  # 上次做空得分
            "error_count": 0,  # 连续错误计数
            "signal_disappeared_time": None,  # 新增：记录信号消失的时间戳
        }
    
    print(f"开始监控，将在每隔{CHECK_INTERVAL_MINUTES}分钟进行检查")
    print(f"监控代币: {', '.join([token['symbol'] for token in TOKEN_CONFIG])}")
    
    try:
        while True:
            # 获取当前时间
            now = datetime.datetime.now()
            
            # 计算下一个检查点
            # 计算当前分钟数在一小时内的位置
            minutes_in_hour = now.minute
            # 计算下一个检查点（向上取整到下一个间隔点）
            next_check_minute = ((minutes_in_hour // CHECK_INTERVAL_MINUTES) + 1) * CHECK_INTERVAL_MINUTES
            # 如果下一个检查点超过了59分，则调整为下一个小时的0分
            if next_check_minute >= 60:
                next_check_minute = 0
            
            # 计算需要等待的秒数
            if next_check_minute > minutes_in_hour:
                # 在同一小时内
                wait_seconds = (next_check_minute - minutes_in_hour) * 60 - now.second
            else:
                # 需要等到下一个小时
                wait_seconds = (60 - minutes_in_hour + next_check_minute) * 60 - now.second
            
            # 如果当前时间正好是检查点，则立即执行检查
            if minutes_in_hour % CHECK_INTERVAL_MINUTES == 0 and now.second < 10:  # 给10秒的误差范围
                print(f"\n开始检查... 当前时间: {now.strftime('%H:%M:%S')}")
                
                for token in TOKEN_CONFIG:
                    symbol = token["symbol"]
                    try:
                        # 如果之前有连续错误，显示恢复尝试信息
                        if ALERT_STATUS[symbol]["error_count"] > 0:
                            print(f"[{symbol}] 尝试恢复，之前连续失败次数: {ALERT_STATUS[symbol]['error_count']}")
                        
                        metrics = get_current_metrics(token["symbol"])
                        long_score, short_score = evaluate_signals(metrics)
                        print(f"[{symbol}] 做多得分: {long_score}, 做空得分: {short_score}")
                        
                        # 重置错误计数
                        ALERT_STATUS[symbol]["error_count"] = 0
                        
                        # --- 主要逻辑修改区域 START --- 

                        # 1. 处理做多信号 
                        if long_score >= 6: 
                            # 核心判断：首次触发 或 分数增强，则发送提醒 
                            if not ALERT_STATUS[symbol]["long"] or long_score > ALERT_STATUS[symbol]["last_long_score"]: 
                                send_feishu_msg(token["name"], metrics, "多", long_score)  # 修改这里，从"做多"改为"多"
                                ALERT_STATUS[symbol]["long"] = True 
                                ALERT_STATUS[symbol]["short"] = False  # 对立信号重置 
                            
                            # 只要信号存在，就更新分数并清除"消失"计时器 
                            ALERT_STATUS[symbol]["last_long_score"] = long_score 
                            ALERT_STATUS[symbol]["signal_disappeared_time"] = None 

                        # 2. 处理做空信号 
                        elif short_score >= 6: 
                            # 核心判断：首次触发 或 分数增强，则发送提醒 
                            if not ALERT_STATUS[symbol]["short"] or short_score > ALERT_STATUS[symbol]["last_short_score"]: 
                                send_feishu_msg(token["name"], metrics, "空", short_score)  # 修改这里，从"做空"改为"空"
                                ALERT_STATUS[symbol]["short"] = True 
                                ALERT_STATUS[symbol]["long"] = False # 对立信号重置 
                            
                            # 只要信号存在，就更新分数并清除"消失"计时器 
                            ALERT_STATUS[symbol]["last_short_score"] = short_score 
                            ALERT_STATUS[symbol]["signal_disappeared_time"] = None 
                            
                        # 3. 处理信号消失（冷静期逻辑） 
                        else: 
                            cooldown_period = datetime.timedelta(minutes=15) # 定义15分钟冷静期 
                            
                            # 检查做多信号是否需要重置 
                            if ALERT_STATUS[symbol]["long"]: 
                                if ALERT_STATUS[symbol]["signal_disappeared_time"] is None: 
                                    # 首次检测到信号消失，记录当前时间 
                                    ALERT_STATUS[symbol]["signal_disappeared_time"] = now 
                                    print(f"[{symbol}] 做多信号消失，进入{cooldown_period.seconds // 60}分钟观察期...") 
                                elif now - ALERT_STATUS[symbol]["signal_disappeared_time"] > cooldown_period: 
                                    # 信号消失已超过冷静期，正式重置状态 
                                    ALERT_STATUS[symbol]["long"] = False 
                                    ALERT_STATUS[symbol]["signal_disappeared_time"] = None 
                                    ALERT_STATUS[symbol]["last_long_score"] = 0 
                                    print(f"[{symbol}] 做多信号消失超过{cooldown_period.seconds // 60}分钟，已重置状态。") 

                            # 检查做空信号是否需要重置 
                            if ALERT_STATUS[symbol]["short"]: 
                                if ALERT_STATUS[symbol]["signal_disappeared_time"] is None: 
                                    ALERT_STATUS[symbol]["signal_disappeared_time"] = now 
                                    print(f"[{symbol}] 做空信号消失，进入{cooldown_period.seconds // 60}分钟观察期...") 
                                elif now - ALERT_STATUS[symbol]["signal_disappeared_time"] > cooldown_period: 
                                    ALERT_STATUS[symbol]["short"] = False 
                                    ALERT_STATUS[symbol]["signal_disappeared_time"] = None 
                                    ALERT_STATUS[symbol]["last_short_score"] = 0 
                                    print(f"[{symbol}] 做空信号消失超过{cooldown_period.seconds // 60}分钟，已重置状态。") 
                        
                        # --- 主要逻辑修改区域 END --- 

                    except Exception as e:
                        # 增加错误计数
                        ALERT_STATUS[symbol]["error_count"] += 1
                        print(f"[{symbol}] 获取数据失败 (连续第{ALERT_STATUS[symbol]['error_count']}次): {e}")
                        
                        # 如果连续错误超过阈值，发送警告
                        if ALERT_STATUS[symbol]["error_count"] == 3:
                            try:
                                error_msg = f"⚠️ 警告: {symbol}连续3次获取数据失败，请检查网络或API状态\n最后错误: {e}"
                                requests.post(FEISHU_WEBHOOK, json={"msg_type": "text", "content": {"text": error_msg}}, timeout=10)
                            except Exception as notify_err:
                                print(f"发送错误通知失败: {notify_err}")
                
                # 重新计算下一个检查点（因为检查过程可能花费了一些时间）
                now = datetime.datetime.now()
                minutes_in_hour = now.minute
                next_check_minute = ((minutes_in_hour // CHECK_INTERVAL_MINUTES) + 1) * CHECK_INTERVAL_MINUTES
                if next_check_minute >= 60:
                    next_check_minute = 0
                
                if next_check_minute > minutes_in_hour:
                    wait_seconds = (next_check_minute - minutes_in_hour) * 60 - now.second
                else:
                    wait_seconds = (60 - minutes_in_hour + next_check_minute) * 60 - now.second
            
            # 显示等待信息
            next_check_time = (now + datetime.timedelta(seconds=wait_seconds)).strftime("%H:%M:%S")
            print(f"等待下一次检查... 下次检查时间: {next_check_time} (等待{wait_seconds}秒)")
            
            # 分段等待，每30秒检查一次是否到达检查点，提高响应性
            wait_interval = 30  # 30秒检查一次
            for _ in range(wait_seconds // wait_interval + 1):
                if wait_seconds <= 0:
                    break
                sleep_time = min(wait_interval, wait_seconds)
                time.sleep(sleep_time)
                wait_seconds -= sleep_time
                
                # 检查是否到达新的检查点
                now = datetime.datetime.now()
                if now.minute % CHECK_INTERVAL_MINUTES == 0 and now.second < 10:
                    break
    except KeyboardInterrupt:
        print("\n程序被用户中断，正在退出...")
    except Exception as e:
        print(f"\n发生严重错误: {e}")
        # 尝试发送严重错误通知
        try:
            error_msg = f"🚨 严重错误: 监控程序异常退出\n错误信息: {e}"
            requests.post(FEISHU_WEBHOOK, json={"msg_type": "text", "content": {"text": error_msg}}, timeout=10)
        except:
            pass
        raise  # 重新抛出异常以便查看完整堆栈


if __name__ == "__main__":
    main_loop()
