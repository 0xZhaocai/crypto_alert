import os
import sys
import logging
import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_logger
from utils.config_loader import ConfigLoader
from utils.database import Database

# 设置日志
log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'crypto_alert.log')
logger = get_logger(log_path)

def test_database():
    """测试数据库操作功能"""
    # 创建临时数据库文件
    test_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests', 'test_db.sqlite')
    
    # 如果测试数据库已存在，先删除
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    # 创建数据库实例
    db = Database(test_db_path)
    
    try:
        # 测试初始化表
        logger.info("测试初始化数据库表...")
        db.init_tables()
        logger.info("数据库表初始化成功")
        
        # 测试添加交易对
        logger.info("测试添加交易对...")
        test_symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
        db.init_symbols(test_symbols)
        
        # 测试获取活跃交易对
        active_symbols = db.get_active_symbols()
        logger.info(f"活跃交易对: {active_symbols}")
        
        # 测试更新交易对状态
        logger.info("测试更新交易对状态...")
        db.update_symbol_status('BTC/USDT', False)
        
        # 再次获取活跃交易对
        active_symbols = db.get_active_symbols()
        logger.info(f"更新后的活跃交易对: {active_symbols}")
        
        # 测试记录告警
        logger.info("测试记录告警...")
        alert_data = {
            'symbol': 'ETH/USDT',
            'price': 3000.0,
            'direction': 'LONG',
            'signal_score': 8,
            'rsi': 28,
            'volume': 1000000.0,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        alert_id = db.record_alert(alert_data)
        logger.info(f"记录告警成功，ID: {alert_id}")
        
        # 测试获取最近告警
        recent_alerts = db.get_recent_alerts(1)
        logger.info(f"最近告警: {recent_alerts}")
        
        # 测试记录告警性能
        logger.info("测试记录告警性能...")
        performance_data = {
            'alert_id': alert_id,
            'price_1h': 3050.0,
            'price_4h': 3100.0,
            'price_24h': 3200.0,
            'price_change_1h': 1.67,
            'price_change_4h': 3.33,
            'price_change_24h': 6.67,
            'profit_if_follow': 1.67  # 假设是多头信号
        }
        db.record_alert_performance(performance_data)
        logger.info("记录告警性能成功")
        
        # 测试获取性能摘要
        performance_summary = db.get_performance_summary(30)
        logger.info(f"性能摘要: {performance_summary}")
        
    except Exception as e:
        logger.error(f"测试数据库操作时出错: {e}")
    finally:
        # 关闭数据库连接
        db.close()
        logger.info("数据库连接已关闭")

if __name__ == "__main__":
    test_database()