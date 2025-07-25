import os
import sys
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_logger
from notifiers.message_formatter import MessageFormatter

# 设置日志
log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'test_notifier.log')
logger = get_logger(log_path)

def test_text_message_newlines():
    """测试文本消息中的换行符处理"""
    logger.info("开始测试文本消息中的换行符处理...")
    
    # 创建包含各种换行符表示的测试模板
    templates = {
        'alert': '📊 趋势{direction}\n🎯 信号：{score}/{max_possible_score}\n💰 价格：{price:.4f}\n🕒 时间：{time}\n`https://binance.com/zh-CN/futures/{symbol}USDT`',
        'error': '⚠️ 警告: {symbol}连续{error_count}次处理失败\n请检查。\n最后错误: {error_message}',
        'crash': '🚨 严重错误: 监控程序异常退出\n时间: {timestamp}\n错误信息: \n{error_message}'
    }
    
    # 创建消息格式化器
    formatter = MessageFormatter(templates)
    
    # 测试alert文本消息
    logger.info("测试alert文本消息...")
    alert_text = formatter.format_alert_text(
        symbol='btcusdt',
        name='BTC',
        direction='多',
        score=8,
        price=68000.0,
        time='2025-07-15 16:30'
    )
    logger.info(f"格式化后的alert文本消息:\n{alert_text}")
    
    # 测试error文本消息
    logger.info("测试error文本消息...")
    error_text = formatter.format_error_text(
        symbol='btcusdt',
        error_count=3,
        error_message='连接超时'
    )
    logger.info(f"格式化后的error文本消息:\n{error_text}")
    
    # 测试crash文本消息
    logger.info("测试crash文本消息...")
    crash_text = formatter.format_crash_text(
        error_message='程序异常退出\n详细错误: 内存溢出',
        timestamp='2025-07-15 16:30:00'
    )
    logger.info(f"格式化后的crash文本消息:\n{crash_text}")
    
    # 测试模板中使用单引号包围的换行符
    logger.info("测试单引号包围的换行符...")
    templates['alert'] = '📊 趋势{direction} \'\\n\' 🎯 信号：{score}/{max_possible_score} \'\\n\' 💰 价格：{price:.4f}'
    formatter = MessageFormatter(templates)
    alert_text = formatter.format_alert_text(
        symbol='btcusdt',
        name='BTC',
        direction='多',
        score=8,
        price=68000.0,
        time='2025-07-15 16:30'
    )
    logger.info(f"使用单引号包围换行符的alert文本消息:\n{alert_text}")
    
    return True

if __name__ == "__main__":
    try:
        logger.info("开始测试文本消息格式...")
        test_text_message_newlines()
        logger.info("测试完成")
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        raise