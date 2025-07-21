import datetime
from typing import Dict, Any, List, Optional

from core.data_fetcher import DataFetcher
from core.signal_evaluator import SignalEvaluator
from notifiers.feishu_notifier import FeishuNotifier
from utils.database import Database
from utils.logger import get_logger
from indicators import load_indicators

class AlertEngine:
    """告警引擎，集成数据获取、信号评估和通知发送等功能"""
    
    def __init__(self, config: Dict[str, Any], symbols: Dict[str, str], db: Database):
        """初始化告警引擎
        
        Args:
            config: 配置字典
            symbols: 交易对符号和显示名称的字典
            db: 数据库实例
        """
        self.config = config
        self.symbols = symbols
        self.db = db
        self.logger = get_logger()
        
        # 初始化组件
        self.data_fetcher = DataFetcher()
        self.signal_evaluator = SignalEvaluator(config)
        self.notifier = FeishuNotifier(config['feishu_webhook'])
        
        # 初始化数据库中的交易对
        self.db.init_symbols(symbols)
    
    def run(self) -> None:
        """运行告警引擎，处理所有活动的交易对"""
        self.logger.info(f"开始检查... 当前时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 获取活动的交易对列表
        symbols_list = self.db.get_active_symbols()
        self.logger.info(f"监控代币: {', '.join([token['symbol'] for token in symbols_list])}")
        
        for token in symbols_list:
            symbol = token["symbol"]
            name = token["name"]
            
            try:
                # 获取交易对状态
                status = self.db.get_symbol_status(symbol)
                
                if status.get("error_count", 0) > 0:
                    self.logger.info(f"[{symbol}] 尝试恢复，之前连续失败次数: {status['error_count']}")
                
                # 获取指标
                self.logger.info(f"获取 {symbol} 指标中...")
                metrics = self.data_fetcher.get_current_metrics(symbol, self.config)
                
                # 评估信号
                long_score, short_score, long_details, short_details = self.signal_evaluator.evaluate_signals(metrics)
                
                self.logger.info(f"[{symbol}] 当前价格: {metrics['price']:.4f}")
                self.logger.info(f"[{symbol}] 做多得分: {long_score}/10")
                for detail in long_details: 
                    self.logger.info(f"[{symbol}] 做多 - {detail}")
                self.logger.info(f"[{symbol}] 做空得分: {short_score}/10")
                for detail in short_details: 
                    self.logger.info(f"[{symbol}] 做空 - {detail}")
                
                # 重置错误计数
                if status.get("error_count", 0) > 0:
                    status["error_count"] = 0
                    self.db.update_symbol_status(symbol, status)
                
                # 处理做多信号
                if long_score >= self.config['signal_threshold']:
                    should_send, failed_reasons = self.signal_evaluator.should_send_alert(symbol, metrics, "long", long_score, status)
                    if should_send:
                        # 发送告警通知
                        message_content = self.notifier.send_alert(symbol, name, metrics, "多", long_score)
                        
                        # 更新交易对状态
                        status.update({
                            "long": True, 
                            "short": False, 
                            "signal_disappeared_time": datetime.datetime.now(),
                            "last_price": metrics["price"], 
                            "last_rsi": metrics["rsi_5m"]
                        })
                        self.db.update_symbol_status(symbol, status)
                        
                        # 记录告警信息，包含完整的指标数据和消息内容
                        alert_id = self.db.record_alert(symbol, "多", long_score, metrics["price"], metrics["rsi_5m"], 
                                                      metrics, message_content)
                        
                        self.logger.info(f"[{symbol}] 做多信号触发，进入{self.config['cooldown_minutes']}分钟观察期...，告警ID: {alert_id}")
                    else:
                        if status.get("signal_disappeared_time"):
                            end_time = status["signal_disappeared_time"] + datetime.timedelta(minutes=self.config['cooldown_minutes'])
                            self.logger.info(f"[{symbol}] 做多得分: {long_score}，但信号条件不满足，不发送（观察期结束: {end_time.strftime('%H:%M:%S')}）")
                        else:
                            self.logger.info(f"[{symbol}] 做多得分: {long_score}，但信号条件不满足，不发送")
                            
                        # 详细列出所有不满足的条件
                        if failed_reasons:
                            self.logger.info(f"[{symbol}] 不满足条件列表:")
                            for i, reason in enumerate(failed_reasons, 1):
                                self.logger.info(f"[{symbol}] {i}. {reason}")
                        else:
                            self.logger.info(f"[{symbol}] 不满足条件: 未知原因")
                    
                    status["last_long_score"] = long_score
                    self.db.update_symbol_status(symbol, status)
                
                # 处理做空信号
                elif short_score >= self.config['signal_threshold']:
                    should_send, failed_reasons = self.signal_evaluator.should_send_alert(symbol, metrics, "short", short_score, status)
                    if should_send:
                        # 发送告警通知
                        message_content = self.notifier.send_alert(symbol, name, metrics, "空", short_score)
                        
                        # 更新交易对状态
                        status.update({
                            "short": True, 
                            "long": False, 
                            "signal_disappeared_time": datetime.datetime.now(),
                            "last_price": metrics["price"], 
                            "last_rsi": metrics["rsi_5m"]
                        })
                        self.db.update_symbol_status(symbol, status)
                        
                        # 记录告警信息，包含完整的指标数据和消息内容
                        alert_id = self.db.record_alert(symbol, "空", short_score, metrics["price"], metrics["rsi_5m"], 
                                                      metrics, message_content)
                        
                        self.logger.info(f"[{symbol}] 做空信号触发，进入{self.config['cooldown_minutes']}分钟观察期...，告警ID: {alert_id}")
                    else:
                        if status.get("signal_disappeared_time"):
                            end_time = status["signal_disappeared_time"] + datetime.timedelta(minutes=self.config['cooldown_minutes'])
                            self.logger.info(f"[{symbol}] 做空得分: {short_score}，但信号条件不满足，不发送（观察期结束: {end_time.strftime('%H:%M:%S')}）")
                        else:
                            self.logger.info(f"[{symbol}] 做空得分: {short_score}，但信号条件不满足，不发送")
                            
                        # 详细列出所有不满足的条件
                        if failed_reasons:
                            self.logger.info(f"[{symbol}] 不满足条件列表:")
                            for i, reason in enumerate(failed_reasons, 1):
                                self.logger.info(f"[{symbol}] {i}. {reason}")
                        else:
                            self.logger.info(f"[{symbol}] 不满足条件: 未知原因")
                    
                    status["last_short_score"] = short_score
                    self.db.update_symbol_status(symbol, status)
                
                # 当前分数不满足任何阈值，检查是否需要重置旧信号
                else:
                    cooldown_period = datetime.timedelta(minutes=self.config['cooldown_minutes'])
                    now = datetime.datetime.now()
                    
                    # 检查并重置已过期的做多信号
                    if status.get("long", False) and status.get("signal_disappeared_time"):
                        if now - status["signal_disappeared_time"] > cooldown_period:
                            status.update({"long": False, "signal_disappeared_time": None, "last_long_score": 0})
                            self.db.update_symbol_status(symbol, status)
                            self.logger.info(f"[{symbol}] 做多信号观察期结束，已重置状态。")

                    # 检查并重置已过期的做空信号
                    if status.get("short", False) and status.get("signal_disappeared_time"):
                        if now - status["signal_disappeared_time"] > cooldown_period:
                            status.update({"short": False, "signal_disappeared_time": None, "last_short_score": 0})
                            self.db.update_symbol_status(symbol, status)
                            self.logger.info(f"[{symbol}] 做空信号观察期结束，已重置状态。")
                
                self.logger.info("") # 分隔不同代币的日志
                
            except Exception as e:
                # 更新错误计数
                status = self.db.get_symbol_status(symbol) or {}
                error_count = status.get("error_count", 0) + 1
                status["error_count"] = error_count
                self.db.update_symbol_status(symbol, status)
                
                self.logger.error(f"[{symbol}] 处理失败 (连续第{error_count}次): {e}")
                self.logger.info("")
                
                # 连续失败3次后发送警告
                if error_count == 3:
                    try:
                        self.notifier.send_error(symbol, error_count, str(e))
                    except Exception as notify_err:
                        self.logger.error(f"发送错误通知失败: {notify_err}")