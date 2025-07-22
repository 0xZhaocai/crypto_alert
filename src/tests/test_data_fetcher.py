import os
import sys
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_logger
from utils.config_loader import ConfigLoader
from core.data_fetcher import DataFetcher
from indicators import load_indicators

# 设置日志
log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'crypto_alert.log')
logger = get_logger(log_path)

def test_data_fetcher():
    """测试数据获取功能"""
    # 加载配置
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
    config_loader = ConfigLoader(config_dir)
    config_loader.load_all_configs()
    
    alert_config = config_loader.get_alert_config()
    
    # 加载指标插件
    load_indicators()
    
    # 创建数据获取器
    data_fetcher = DataFetcher()
    
    # 测试交易对
    test_symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
    
    for symbol in test_symbols:
        try:
            logger.info(f"获取{symbol}的K线数据...")
            klines = data_fetcher.get_klines(symbol)
            logger.info(f"成功获取{symbol}的K线数据，共{len(klines)}条记录")
            
            logger.info(f"获取{symbol}的当前价格...")
            price = data_fetcher.get_current_price(symbol)
            logger.info(f"{symbol}的当前价格: {price}")
            
            logger.info(f"获取{symbol}的24小时成交量...")
            volume = data_fetcher.get_24h_volume(symbol)
            logger.info(f"{symbol}的24小时成交量: {volume}")
            
        except Exception as e:
            logger.error(f"测试{symbol}数据获取时出错: {e}")

if __name__ == "__main__":
    test_data_fetcher()