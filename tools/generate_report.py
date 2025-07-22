import argparse
import sys
import traceback
import os
import datetime

# 确保能够导入src包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.database import Database
from src.utils.logger import get_logger
from src.utils.config_loader import ConfigLoader
from src.analysis.performance_analyzer import run_performance_analysis
from src.indicators import load_indicators

# 设置日志
log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'logs', 'crypto_alert.log')
logger = get_logger(log_path)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='生成告警性能分析报告')
    parser.add_argument('--days', type=int, default=30, help='分析最近多少天的数据，默认30天')
    parser.add_argument('--output', type=str, default='', help='输出报告的路径，默认为项目目录下的reports目录')
    args = parser.parse_args()
    
    try:
        # 加载配置
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'config')
        config_loader = ConfigLoader(config_dir)
        config_loader.load_all_configs()
        alert_config = config_loader.get_alert_config()
        
        # 确保数据目录存在
        data_dir = os.path.dirname(alert_config['db_path'])
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            logger.info(f"创建数据目录: {data_dir}")
        
        # 检查数据库文件是否存在
        if not os.path.exists(alert_config['db_path']):
            logger.warning(f"数据库文件不存在: {alert_config['db_path']}")
            logger.info("将创建新的数据库文件")
        
        # 初始化数据库
        db = Database(alert_config['db_path'])
        
        # 加载指标插件
        load_indicators()
        
        # 创建reports目录（如果不存在）
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'reports')
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
            logger.info(f"创建报告目录: {reports_dir}")
        
        # 设置默认输出路径在reports目录下
        if not args.output:
            current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            args.output = os.path.join(reports_dir, f'performance_report_{current_time}.html')
        else:
            # 确保输出目录存在
            output_dir = os.path.dirname(os.path.abspath(args.output))
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                logger.info(f"创建输出目录: {output_dir}")
        
        # 运行性能分析
        logger.info(f"开始生成最近{args.days}天的性能分析报告...")
        run_performance_analysis(db, args.days, args.output)
        logger.info(f"性能分析报告已生成: {args.output}")
        print(f"\n性能分析报告已生成: {args.output}")
        
    except Exception as e:
        logger.error(f"生成性能分析报告失败: {e}\n{traceback.format_exc()}")
        print(f"\n错误: 生成性能分析报告失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()