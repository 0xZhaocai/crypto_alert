import datetime
import requests
from typing import Dict, Any, Optional

from src.utils.logger import get_logger
from src.notifiers.message_formatter import MessageFormatter

class FeishuNotifier:
    """飞书通知器，用于发送飞书消息"""
    
    def __init__(self, webhook_url: str = None, templates: Dict[str, str] = None, logger=None):
        """初始化飞书通知器
        
        Args:
            webhook_url: 飞书机器人webhook地址，如果为None或空字符串则无法发送消息
            templates: 消息模板字典，已废弃，保留参数仅为向后兼容
            logger: 日志记录器，如果为None则使用全局日志记录器
        """
        self.webhook_url = webhook_url
        self.formatter = MessageFormatter()
        self.logger = logger if logger else get_logger()
        
        # 检查webhook_url是否有效
        if not self.webhook_url:
            self.logger.warning("飞书webhook未配置，无法发送通知")
    
    def send_alert(self, symbol: str, name: str, metrics: Dict[str, Any], direction: str, score: int) -> str:
        """发送提醒消息
        
        Args:
            symbol: 交易对符号
            name: 显示名称
            metrics: 包含各种技术指标的字典
            direction: 信号方向 (多/空)
            score: 信号分数
            
        Returns:
            发送的消息内容，如果发送失败则返回空字符串
        """
        # 检查webhook_url是否配置
        if not self.webhook_url:
            self.logger.warning(f"[{symbol}] 飞书webhook未配置，无法发送提醒")
            return ""
            
        time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 获取形态信息，默认为"未知"
        pattern = "未知"
        if 'zigzag' in metrics and 'pattern' in metrics['zigzag']:
            pattern = metrics['zigzag']['pattern']
        
        try:
            # 使用格式化器创建富文本消息
            rich_content = self.formatter.format_alert_rich_text(
                symbol=symbol,
                name=name,
                direction=direction,
                score=score,
                price=metrics['price'],
                time=time_str,
                pattern=pattern
            )
            
            # 构建简洁的文本消息内容，用于存储到数据库
            text_content = self.formatter.format_alert_text(
                symbol=symbol,
                name=name,
                direction=direction,
                score=score,
                price=metrics['price'],
                time=time_str,
                pattern=pattern
            )
            
            # 构建简洁的日志内容
            log_content = f"{name} | 🎯 信号：{direction} {score}/10 | 💰 价格：{metrics['price']:.4f} | 🕒 时间：{time_str} | https://binance.com/zh-CN/futures/{symbol}"
            
            self.logger.info(f"[{symbol}] 发送提醒：【{direction}】分数: {score}")
            # 使用debug级别记录消息内容，避免重复打印
            self.logger.debug(f"[{symbol}] 发送内容: {log_content}")
            
            # 使用富文本格式发送消息
            response = requests.post(
                self.webhook_url, 
                json={"msg_type": "post", "content": rich_content}, 
                timeout=10
            )
            response.raise_for_status()
            self.logger.info(f"[{symbol}] 提醒发送成功")
            return text_content
                
        except Exception as e:
            self.logger.error(f"[{symbol}] 发送提醒失败: {e}")
            return ""
    
    def send_error(self, symbol: str, error_count: int, error_message: str) -> bool:
        """发送错误消息
        
        Args:
            symbol: 交易对符号
            error_count: 连续错误次数
            error_message: 错误信息
            
        Returns:
            是否发送成功
        """
        # 检查webhook_url是否配置
        if not self.webhook_url:
            self.logger.warning(f"[{symbol}] 飞书webhook未配置，无法发送错误提醒")
            return False
            
        try:
            # 使用格式化器创建错误消息
            body = self.formatter.format_error_text(
                symbol=symbol,
                error_count=error_count,
                error_message=error_message
            )
            
            response = requests.post(
                self.webhook_url, 
                json={"msg_type": "text", "content": {"text": body}}, 
                timeout=10
            )
            response.raise_for_status()
            self.logger.info(f"[{symbol}] 错误提醒发送成功")
            return True
                
        except Exception as e:
            self.logger.error(f"发送错误提醒失败: {e}")
            return False
    
    def send_crash(self, error_message: str, timestamp: str = None) -> bool:
        """发送程序崩溃消息
        
        Args:
            error_message: 错误信息
            timestamp: 崩溃时间戳，如果为None则使用当前时间
            
        Returns:
            是否发送成功
        """
        # 检查webhook_url是否配置
        if not self.webhook_url:
            self.logger.warning("飞书webhook未配置，无法发送崩溃提醒")
            return False
        
        try:
            # 使用格式化器创建崩溃消息
            rich_content = self.formatter.format_crash_rich_text(error_message=error_message, timestamp=timestamp)
            body = None  # 不需要普通文本内容，因为我们使用富文本
        except Exception as format_error:
            self.logger.error(f"格式化崩溃消息失败: {format_error}")
            # 使用简单格式作为备选
            body = f"🚨 严重错误: 监控程序异常退出\n时间: {timestamp or datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n错误信息: {error_message}"
            rich_content = None
            self.logger.info("使用简单格式作为备选")
        
        
        try:
            # 如果有富文本内容，使用富文本格式发送
            if rich_content:
                response = requests.post(
                    self.webhook_url, 
                    json={"msg_type": "post", "content": rich_content}, 
                    timeout=10
                )
                response.raise_for_status()
                self.logger.info("崩溃提醒发送成功 (富文本格式)")
                return True
            # 否则使用普通文本格式发送
            elif body:
                response = requests.post(
                    self.webhook_url, 
                    json={"msg_type": "text", "content": {"text": body}}, 
                    timeout=10
                )
                response.raise_for_status()
                self.logger.info("崩溃提醒发送成功 (普通文本格式)")
                return True
            else:
                self.logger.error("没有可用的消息内容，无法发送崩溃提醒")
                return False
            
        except Exception as e:
            self.logger.error(f"发送崩溃提醒失败: {e}")
            # 如果之前尝试使用富文本格式失败，尝试使用普通文本格式
            if rich_content and body is None:
                try:
                    # 创建一个简单的文本消息作为备选
                    fallback_body = f"🚨 严重错误: 监控程序异常退出\n时间: {timestamp}\n错误信息: {error_message}"
                    response = requests.post(
                        self.webhook_url, 
                        json={"msg_type": "text", "content": {"text": fallback_body}}, 
                        timeout=10
                    )
                    response.raise_for_status()
                    self.logger.info("崩溃提醒发送成功 (普通文本格式作为备选)")
                    return True
                except Exception as fallback_error:
                    self.logger.error(f"使用普通文本格式发送崩溃提醒也失败: {fallback_error}")
                    return False
            return False