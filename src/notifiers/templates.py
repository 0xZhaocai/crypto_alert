import logging
from typing import Dict, Any

# 日志记录器
logger = logging.getLogger(__name__)


def format_alert_text(symbol: str, name: str, direction: str, score: int, price: float, time: str, pattern: str = "", max_possible_score: int = 12) -> str:
    """格式化普通文本提醒消息
    
    Args:
        symbol: 交易对符号
        name: 显示名称
        direction: 信号方向 (多/空)
        score: 信号分数
        price: 当前价格
        time: 当前时间
        pattern: 形态识别结果，可选
        max_possible_score: 信号评分的最大可能分数，默认为12
        
    Returns:
        格式化后的文本消息
    """
    # 确保形态和趋势方向一致
    # 如果形态是M顶，趋势必须是空；如果形态是W底，趋势必须是多
    display_direction = direction
    if pattern == "M顶" and direction == "多":
        logger.warning(f"检测到形态与趋势不一致：形态为M顶但趋势为多，已自动调整为空")
        display_direction = "空"
    elif pattern == "W底" and direction == "空":
        logger.warning(f"检测到形态与趋势不一致：形态为W底但趋势为空，已自动调整为多")
        display_direction = "多"
    
    # 总是显示形态信息，即使是"未知"
    pattern_text = f"\n🔍 形态：{pattern}"
#    formatted_text = f"📊 趋势：{display_direction}\n🎯 信号：{score}/{max_possible_score}{pattern_text}\n💰 价格：{price:.4f}\n🕒 时间：{time}\nhttps://binance.com/zh-CN/futures/{symbol}USDT"
    formatted_text = f"📊 趋势：{display_direction}\n🎯 信号：{score}/{max_possible_score}{pattern_text}\n💰 价格：{price:.4f}\n🕒 时间：{time}"
    
    logger.debug(f"格式化文本消息: {formatted_text}")
    return formatted_text


def format_alert_rich_text(symbol: str, name: str, direction: str, score: int, price: float, time: str, pattern: str = "", max_possible_score: int = 12) -> Dict[str, Any]:
    """格式化富文本提醒消息
    
    Args:
        symbol: 交易对符号
        name: 显示名称
        direction: 信号方向 (多/空)
        score: 信号分数
        price: 当前价格
        time: 当前时间
        pattern: 形态识别结果，可选
        max_possible_score: 信号评分的最大可能分数，默认为12
        
    Returns:
        格式化后的富文本消息字典
    """
    # 确保形态和趋势方向一致
    # 如果形态是M顶，趋势必须是空；如果形态是W底，趋势必须是多
    display_direction = direction
    if pattern == "M顶" and direction == "多":
        display_direction = "空"
    elif pattern == "W底" and direction == "空":
        display_direction = "多"
    
    # 构建富文本内容
    content = [
        [{"tag": "text", "text": f"📊 趋势：{display_direction}"}],
        [{"tag": "text", "text": f"🎯 信号：{score}/{max_possible_score}"}]
    ]
    
    # 总是显示形态信息，即使是"未知"
    content.append([{"tag": "text", "text": f"🔍 形态：{pattern}"}])
    
    # 添加其他信息
    content.extend([
        [{"tag": "text", "text": f"💰 价格：{price:.4f}"}],
        [{"tag": "text", "text": f"🕒 时间：{time}"}],
        #[{"tag": "a", "text": f"查看{symbol.upper()}走势", "href": f"https://binance.com/zh-CN/futures/{symbol}USDT"}]
    ])
    
    # 构建标题
    title = f"🔔 {name} 盯盘提醒"
    
    logger.debug(f"格式化富文本消息: {title}")
    
    return {
        "post": {
            "zh_cn": {
                "title": title,
                "content": content
            }
        }
    }


def format_error_text(symbol: str, error_count: int, error_message: str) -> str:
    """格式化错误消息
    
    Args:
        symbol: 交易对符号
        error_count: 连续错误次数
        error_message: 错误信息
        
    Returns:
        格式化后的错误消息
    """
    formatted_text = f"⚠️ 警告: {symbol}连续{error_count}次处理失败，请检查。最后错误: {error_message}"
    
    logger.debug(f"格式化错误消息: {formatted_text}")
    return formatted_text


def format_crash_text(error_message: str, timestamp: str = None) -> str:
    """格式化崩溃消息
    
    Args:
        error_message: 错误信息
        timestamp: 崩溃时间戳，如果为None则使用当前时间
        
    Returns:
        格式化后的崩溃消息
    """
    # 如果没有提供时间戳，使用当前时间
    if timestamp is None:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    formatted_text = f"🚨 严重错误: 监控程序异常退出\n时间: {timestamp}\n错误信息: \n{error_message}"
    
    logger.debug(f"格式化崩溃消息: {formatted_text}")
    return formatted_text


def format_crash_rich_text(error_message: str, timestamp: str = None) -> Dict[str, Any]:
    """格式化富文本崩溃消息
    
    Args:
        error_message: 错误信息
        timestamp: 崩溃时间戳，如果为None则使用当前时间
        
    Returns:
        格式化后的富文本崩溃消息字典
    """
    # 如果没有提供时间戳，使用当前时间
    if timestamp is None:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 将错误信息按行分割，每行作为单独的文本块
    error_lines = error_message.split('\n')
    error_blocks = []
    
    # 添加错误信息标题
    error_blocks.append([
        {
            "tag": "text",
            "text": "错误信息:\n"
        }
    ])
    
    # 为每行错误信息创建单独的文本块，以保持格式
    for line in error_lines:
        if line.strip():
            error_blocks.append([
                {
                    "tag": "text",
                    "text": line
                }
            ])
    
    rich_content = {
        "post": {
            "zh_cn": {
                "title": "🚨 监控程序异常退出",
                "content": [
                    # 时间戳块
                    [
                        {
                            "tag": "text",
                            "text": "时间: "
                        },
                        {
                            "tag": "text",
                            "text": timestamp
                        }
                    ],
                ] + error_blocks  # 添加所有错误信息块
            }
        }
    }
    
    logger.debug(f"格式化富文本崩溃消息")
    return rich_content