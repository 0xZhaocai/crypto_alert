import datetime
import requests
from utils import (
    load_config, load_status, save_status,
    init_database, get_current_metrics,
    send_feishu_msg
)

"""
加密货币价格监控与提醒工具 - 核心业务逻辑

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
  */5 * * * * python3 /path/to/your/script/alert.py
"""

# --- 全局配置加载 ---
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
        long_score += 1; long_details.append(f"贴近15mEMA21({metrics['price_ema_gap_ratio']:.2%}): +1")
    if metrics["atr_ratio"] >= ATR_RATIO:
        long_score += 2; long_details.append(f"ATR放大({metrics['atr_ratio']:.2f}x): +2")
    if metrics["volume_ratio"] >= VOLUME_RATIO:
        long_score += 2; long_details.append(f"成交量放大({metrics['volume_ratio']:.2f}x): +2")
    
    # EMA靠近度评分（任一周期EMA9与EMA21靠近都给分）
    ema_convergence_periods = []
    if metrics["ema_convergence_5m"] < EMA_CONVERGENCE_THRESHOLD:
        ema_convergence_periods.append("5m")
    if metrics["ema_convergence_15m"] < EMA_CONVERGENCE_THRESHOLD:
        ema_convergence_periods.append("15m")
    if metrics["ema_convergence_1h"] < EMA_CONVERGENCE_THRESHOLD:
        ema_convergence_periods.append("1h")
    
    if ema_convergence_periods:
        long_score += EMA_CONVERGENCE_SCORE
        periods_str = "/".join(ema_convergence_periods)
        long_details.append(f"EMA靠近({periods_str}): +{EMA_CONVERGENCE_SCORE}")

    # 做空信号评分
    if metrics["price"] < metrics["ema21_15m"]:
        short_score += 2; short_details.append("价格 < EMA21(15m): +2")
    if metrics["price"] < metrics["ema21_1h"]:
        short_score += 2; short_details.append("价格 < EMA21(1h): +2")
    if RSI_RANGE["min"] <= metrics["rsi_5m"] <= RSI_RANGE["max"]:
        short_score += 1; short_details.append(f"RSI在区间内({metrics['rsi_5m']:.2f}): +1")
    if metrics["price_ema_gap_ratio"] < PRICE_EMA_GAP_RATIO:
        short_score += 1; short_details.append(f"贴近15mEMA21({metrics['price_ema_gap_ratio']:.2%}): +1")
    if metrics["atr_ratio"] >= ATR_RATIO:
        short_score += 2; short_details.append(f"ATR放大({metrics['atr_ratio']:.2f}x): +2")
    if metrics["volume_ratio"] >= VOLUME_RATIO:
        short_score += 2; short_details.append(f"成交量放大({metrics['volume_ratio']:.2f}x): +2")
    
    # EMA靠近度评分（任一周期EMA9与EMA21靠近都给分）
    if ema_convergence_periods:
        short_score += EMA_CONVERGENCE_SCORE
        periods_str = "/".join(ema_convergence_periods)
        short_details.append(f"EMA靠近({periods_str}): +{EMA_CONVERGENCE_SCORE}")

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
                    send_feishu_msg(token["name"], metrics, "多", long_score, long_details, FEISHU_WEBHOOK)
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
                    send_feishu_msg(token["name"], metrics, "空", short_score, short_details, FEISHU_WEBHOOK)
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