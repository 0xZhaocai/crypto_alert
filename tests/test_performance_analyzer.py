import os
import sys
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_logger
from utils.config_loader import ConfigLoader
from utils.database import Database
from analysis.performance_analyzer import run_performance_analysis
from indicators import load_indicators

# 设置日志
log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'crypto_alert.log')
logger = get_logger(log_path)

def test_performance_analyzer():
    """测试性能分析功能"""
    # 加载配置
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
    config_loader = ConfigLoader(config_dir)
    config_loader.load_all_configs()
    
    alert_config = config_loader.get_alert_config()
    
    # 初始化数据库
    db = Database(alert_config['db_path'])
    
    # 加载指标插件
    load_indicators()
    
    # 设置输出路径
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests', 'output')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'test_performance_report.html')
    
    # 运行性能分析
    days = 30  # 默认分析最近30天的数据
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            logger.error("天数必须是整数")
    
    logger.info(f"开始分析最近{days}天的告警性能...")
    run_performance_analysis(db, days, output_path)
    logger.info(f"性能分析报告已生成: {output_path}")

if __name__ == "__main__":
    test_performance_analyzer()