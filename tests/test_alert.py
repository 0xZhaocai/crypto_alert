import os
import sys
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_logger
from utils.config_loader import ConfigLoader
from utils.database import Database
from core.alert_engine import AlertEngine
from indicators import load_indicators

# 设置日志
log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'crypto_alert.log')
logger = get_logger(log_path)

def test_alert():
    """测试告警功能"""
    # 加载配置
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
    config_loader = ConfigLoader(config_dir)
    config_loader.load_all_configs()
    
    template_config = config_loader.get_template_config()
    alert_config = config_loader.get_alert_config()
    
    # 初始化数据库
    db = Database(alert_config['db_path'])
    
    # 加载指标插件
    load_indicators()
    
    # 创建告警引擎
    alert_engine = AlertEngine(alert_config, config_loader.symbols, template_config, db)
    
    # 测试特定交易对
    test_symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
    
    logger.info(f"开始测试告警功能，测试交易对: {test_symbols}")
    
    # 运行告警检查
    try:
        logger.info("运行告警引擎检查...")
        alert_engine.run()
    except Exception as e:
        logger.error(f"运行告警引擎时出错: {e}")
    
    logger.info("告警测试完成")

if __name__ == "__main__":
    test_alert()