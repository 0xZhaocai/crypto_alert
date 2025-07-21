import os
import sys
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_logger
from utils.config_loader import ConfigLoader
from notifiers.feishu_notifier import FeishuNotifier

# 设置日志
log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'crypto_alert.log')
logger = get_logger(log_path)

def test_feishu_notifier():
    """测试飞书通知器"""
    # 加载配置
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
    config_loader = ConfigLoader(config_dir)
    config_loader.load_all_configs()
    
    template_config = config_loader.get_template_config()
    alert_config = config_loader.get_alert_config()
    
    # 创建飞书通知器
    notifier = FeishuNotifier(alert_config.get('feishu_webhook'))
    
    # 测试数据
    test_data = {
        'symbol': 'BTC/USDT',
        'price': 50000,
        'direction': 'LONG',
        'signal_score': 8,
        'rsi': 28,
        'volume': 1000000,
        'timestamp': '2023-01-01 12:00:00'
    }
    
    # 发送测试通知
    logger.info(f"发送测试通知: {test_data}")
    success = notifier.send_alert(test_data)
    
    if success:
        logger.info("测试通知发送成功")
    else:
        logger.error("测试通知发送失败")

if __name__ == "__main__":
    test_feishu_notifier()