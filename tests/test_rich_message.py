import os
import sys
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_logger
from utils.config_loader import ConfigLoader
from notifiers.feishu_notifier import FeishuNotifier
from notifiers.message_formatter import MessageFormatter

# 设置日志
log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'crypto_alert.log')
logger = get_logger(log_path)

def test_rich_message():
    """测试富文本消息格式"""
    # 加载配置
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
    config_loader = ConfigLoader(config_dir)
    config_loader.load_all_configs()
    
    template_config = config_loader.get_template_config()
    alert_config = config_loader.get_alert_config()
    
    # 创建飞书通知器
    notifier = FeishuNotifier(alert_config.get('feishu_webhook'))
    
    # 测试数据
    test_data_list = [
        {
            'symbol': 'BTC/USDT',
            'price': 50000,
            'direction': 'LONG',
            'signal_score': 9,
            'rsi': 28,
            'volume': 1500000,
            'timestamp': '2023-01-01 12:00:00'
        },
        {
            'symbol': 'ETH/USDT',
            'price': 3000,
            'direction': 'SHORT',
            'signal_score': 7,
            'rsi': 72,
            'volume': 800000,
            'timestamp': '2023-01-01 12:05:00'
        },
        {
            'symbol': 'BNB/USDT',
            'price': 400,
            'direction': 'LONG',
            'signal_score': 8,
            'rsi': 30,
            'volume': 500000,
            'timestamp': '2023-01-01 12:10:00'
        }
    ]
    
    # 发送测试通知
    for test_data in test_data_list:
        logger.info(f"发送测试通知: {test_data}")
        success = notifier.send_alert(test_data)
        
        if success:
            logger.info(f"测试通知发送成功: {test_data['symbol']}")
        else:
            logger.error(f"测试通知发送失败: {test_data['symbol']}")

def test_alert_template_in_rich_text():
    """测试alert模板在富文本消息中的应用"""
    logger.info("开始测试alert模板在富文本消息中的应用...")
    
    # 创建消息格式化器
    formatter = MessageFormatter()
    
    # 测试参数
    symbol = 'btcusdt'
    name = 'BTC'
    direction = '多'
    score = 8
    price = 68000.0
    time = '2025-07-15 16:30'
    
    # 格式化富文本消息
    rich_message = formatter.format_alert_rich_text(
        symbol=symbol,
        name=name,
        direction=direction,
        score=score,
        price=price,
        time=time
    )
    
    # 打印结果
    logger.info(f"富文本消息标题: {rich_message['post']['zh_cn']['title']}")
    logger.info(f"富文本消息内容: {rich_message['post']['zh_cn']['content']}")
    
    # 注意：现在模板是在templates.py模块中定义的，无法在运行时修改
    # 这里只是为了演示，我们再次调用相同的方法
    
    # 再次格式化富文本消息
    rich_message = formatter.format_alert_rich_text(
        symbol=symbol,
        name=name,
        direction=direction,
        score=score,
        price=price,
        time=time
    )
    
    # 打印结果
    logger.info(f"再次调用后的富文本消息内容: {rich_message['post']['zh_cn']['content']}")
    
    return True

def test_newline_in_rich_text():
    """测试换行符在富文本消息中的处理"""
    logger.info("开始测试换行符在富文本消息中的处理...")
    
    # 创建消息格式化器
    formatter = MessageFormatter()
    
    # 测试参数
    symbol = 'btcusdt'
    name = 'BTC'
    direction = '多'
    score = 8
    price = 68000.0
    time = '2025-07-15 16:30'
    
    # 格式化富文本消息
    rich_message = formatter.format_alert_rich_text(
        symbol=symbol,
        name=name,
        direction=direction,
        score=score,
        price=price,
        time=time
    )
    
    # 打印结果
    logger.info(f"富文本消息标题: {rich_message['post']['zh_cn']['title']}")
    logger.info(f"富文本消息内容(应包含多行): {rich_message['post']['zh_cn']['content']}")
    
    # 检查内容是否包含多个元素（多行）
    content_length = len(rich_message['post']['zh_cn']['content'])
    logger.info(f"富文本消息内容行数: {content_length}")
    
    # 应该有5行内容（4个换行符分隔的文本行 + 1个链接）
    if content_length >= 5:
        logger.info("✅ 换行符处理正确，生成了多行内容")
    else:
        logger.error(f"❌ 换行符处理不正确，只生成了{content_length}行内容")
    
    return content_length >= 5

if __name__ == "__main__":
    try:
        logger.info("开始测试富文本消息格式...")
        # test_rich_message()
        test_alert_template_in_rich_text()
        test_newline_in_rich_text()
        logger.info("测试完成")
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        raise