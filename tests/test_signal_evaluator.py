import os
import sys
import logging
import pandas as pd

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_logger
from utils.config_loader import ConfigLoader
from core.data_fetcher import DataFetcher
from core.signal_evaluator import SignalEvaluator
from indicators import load_indicators, create_indicator

# 设置日志
log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'crypto_alert.log')
logger = get_logger(log_path)

def test_signal_evaluator():
    """测试信号评估功能"""
    # 加载配置
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
    config_loader = ConfigLoader(config_dir)
    config_loader.load_all_configs()
    
    alert_config = config_loader.get_alert_config()
    
    # 创建数据获取器并加载指标插件
    data_fetcher = DataFetcher(alert_config)
    load_indicators()
    
    # 创建信号评估器
    signal_evaluator = SignalEvaluator(alert_config)
    
    # 测试交易对
    test_symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
    
    for symbol in test_symbols:
        try:
            logger.info(f"评估{symbol}的信号...")
            
            # 获取K线数据
            klines = data_fetcher.get_klines(symbol)
            
            # 转换为DataFrame
            df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            
            # 计算RSI
            rsi_indicator = create_indicator('rsi', alert_config)
            klines_data = [[row['timestamp'], row['open'], row['high'], row['low'], row['close'], row['volume']] for _, row in df.iterrows()]
            rsi_result = rsi_indicator.calculate(klines_data)
            current_rsi = rsi_result['rsi']
            
            # 获取当前价格和成交量
            current_price = data_fetcher.get_current_price(symbol)
            volume_24h = data_fetcher.get_24h_volume(symbol)
            
            # 评估信号
            signal_data = {
                'symbol': symbol,
                'price': current_price,
                'rsi': current_rsi,
                'volume': volume_24h
            }
            
            result = signal_evaluator.evaluate(signal_data)
            
            if result['should_alert']:
                logger.info(f"{symbol}触发告警信号: 方向={result['direction']}, 分数={result['signal_score']}")
            else:
                logger.info(f"{symbol}未触发告警信号")
                
        except Exception as e:
            logger.error(f"评估{symbol}信号时出错: {e}")

if __name__ == "__main__":
    test_signal_evaluator()