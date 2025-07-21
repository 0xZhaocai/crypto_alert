import os
import sys
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_logger
from utils.config_loader import ConfigLoader
from utils.database import Database
from tasks.backtest_task import BacktestTask
from indicators import load_indicators

# 设置日志
log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'crypto_alert.log')
logger = get_logger(log_path)

def test_backtest():
    """测试回测功能"""
    # 加载配置
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
    config_loader = ConfigLoader(config_dir)
    config_loader.load_all_configs()
    
    alert_config = config_loader.get_alert_config()
    
    # 初始化数据库
    db = Database(alert_config['db_path'])
    
    # 加载指标插件
    load_indicators()
    
    # 创建回测任务
    backtest_task = BacktestTask(db)
    
    # 运行回测
    logger.info("开始运行回测...")
    backtest_task.run()
    logger.info("回测完成")

def test_backtest_specific_alert(alert_id):
    """测试特定告警的回测
    
    Args:
        alert_id: 告警ID
    """
    # 加载配置
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
    config_loader = ConfigLoader(config_dir)
    config_loader.load_all_configs()
    
    alert_config = config_loader.get_alert_config()
    
    # 初始化数据库
    db = Database(alert_config['db_path'])
    
    # 加载指标插件
    load_indicators()
    
    # 创建回测任务
    backtest_task = BacktestTask(db)
    
    # 获取特定告警
    alert = db.get_alert_by_id(alert_id)
    if not alert:
        logger.error(f"未找到ID为{alert_id}的告警")
        return
    
    # 运行特定告警的回测
    logger.info(f"开始对告警ID {alert_id} 进行回测...")
    backtest_task._process_alert(alert)
    logger.info(f"告警ID {alert_id} 的回测完成")

if __name__ == "__main__":
    # 如果提供了告警ID参数，则测试特定告警
    if len(sys.argv) > 1:
        try:
            alert_id = int(sys.argv[1])
            test_backtest_specific_alert(alert_id)
        except ValueError:
            logger.error("告警ID必须是整数")
    else:
        # 否则运行常规回测
        test_backtest()