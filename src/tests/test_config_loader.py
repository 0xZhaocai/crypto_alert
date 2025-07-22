import os
import sys
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_logger
from utils.config_loader import ConfigLoader

# 设置日志
log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'crypto_alert.log')
logger = get_logger(log_path)

def test_config_loader():
    """测试配置加载功能"""
    # 获取配置目录路径
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
    
    try:
        # 创建配置加载器
        logger.info("创建配置加载器...")
        config_loader = ConfigLoader(config_dir)
        
        # 加载所有配置
        logger.info("加载所有配置...")
        config_loader.load_all_configs()
        
        # 获取告警配置
        logger.info("获取告警配置...")
        alert_config = config_loader.get_alert_config()
        logger.info(f"告警配置: {alert_config}")
        
        # 获取模板配置
        logger.info("获取模板配置...")
        template_config = config_loader.get_template_config()
        logger.info(f"模板配置: {template_config}")
        
        # 获取交易对配置
        logger.info("获取交易对配置...")
        symbols = config_loader.get_symbols()
        logger.info(f"交易对列表 (前5个): {symbols[:5]}")
        
        logger.info("配置加载测试完成")
        
    except Exception as e:
        logger.error(f"测试配置加载时出错: {e}")

if __name__ == "__main__":
    test_config_loader()