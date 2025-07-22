import logging
from typing import Dict, Any, Optional

# 导入模板函数
from src.notifiers import templates

class MessageFormatter:
    """消息格式化器，用于处理飞书消息格式"""
    
    def __init__(self, templates_dict: Optional[Dict[str, str]] = None):
        """初始化消息格式化器
        
        Args:
            templates_dict: 消息模板字典，用于向后兼容
        """
        self.templates_dict = templates_dict or {}
        self.logger = logging.getLogger(__name__)
    
    def format_alert_text(self, symbol: str, name: str, direction: str, score: int, price: float, time: str, pattern: str = "") -> str:
        """格式化普通文本提醒消息
        
        Args:
            symbol: 交易对符号
            name: 显示名称
            direction: 信号方向 (多/空)
            score: 信号分数
            price: 当前价格
            time: 当前时间
            pattern: 形态识别结果，可选
            
        Returns:
            格式化后的文本消息
        """
        # 使用templates模块中的函数
        return templates.format_alert_text(
            symbol=symbol,
            name=name,
            direction=direction,
            score=score,
            price=price,
            time=time,
            pattern=pattern
        )
    
    def format_alert_rich_text(self, symbol: str, name: str, direction: str, score: int, price: float, time: str, pattern: str = "") -> Dict[str, Any]:
        """格式化富文本提醒消息
        
        Args:
            symbol: 交易对符号
            name: 显示名称
            direction: 信号方向 (多/空)
            score: 信号分数
            price: 当前价格
            time: 当前时间
            pattern: 形态识别结果，可选
            
        Returns:
            格式化后的富文本消息字典
        """
        # 使用templates模块中的函数
        return templates.format_alert_rich_text(
            symbol=symbol,
            name=name,
            direction=direction,
            score=score,
            price=price,
            time=time,
            pattern=pattern
        )
    
    def format_error_text(self, symbol: str, error_count: int, error_message: str) -> str:
        """格式化错误消息
        
        Args:
            symbol: 交易对符号
            error_count: 连续错误次数
            error_message: 错误信息
            
        Returns:
            格式化后的错误消息
        """
        # 使用templates模块中的函数
        return templates.format_error_text(
            symbol=symbol,
            error_count=error_count,
            error_message=error_message
        )
    
    def format_crash_text(self, error_message: str, timestamp: str = None) -> str:
        """格式化崩溃消息
        
        Args:
            error_message: 错误信息
            timestamp: 崩溃时间戳，如果为None则使用当前时间
            
        Returns:
            格式化后的崩溃消息
        """
        # 使用templates模块中的函数
        return templates.format_crash_text(
            error_message=error_message,
            timestamp=timestamp
        )
        
    def format_crash_rich_text(self, error_message: str, timestamp: str = None) -> Dict[str, Any]:
        """格式化富文本崩溃消息
        
        Args:
            error_message: 错误信息
            timestamp: 崩溃时间戳，如果为None则使用当前时间
            
        Returns:
            格式化后的富文本崩溃消息字典
        """
        # 使用templates模块中的函数
        return templates.format_crash_rich_text(
            error_message=error_message,
            timestamp=timestamp
        )