import time
import datetime
import schedule
import sys
import traceback

from utils.database import Database
from utils.logger import get_logger, setup_logger
from tasks.backtest_task import run_backtest_task
from notifiers.feishu_notifier import FeishuNotifier
from utils.config_loader import load_config
from indicators import load_indicators

# 设置日志
setup_logger()
logger = get_logger()

# 加载配置
config = load_config()

# 初始化数据库
db = Database(config['database_path'])

# 加载指标插件
load_indicators()

# 加载消息模板
templates = {}
with open(config['templates_path'], 'r', encoding='utf-8') as f:
    current_template = None
    current_content = []
    
    for line in f:
        if line.startswith('---'):
            if current_template and current_content:
                templates[current_template] = ''.join(current_content).strip()
                current_content = []
            current_template = line.strip('-').strip()
        elif current_template:
            current_content.append(line)
    
    if current_template and current_content:
        templates[current_template] = ''.join(current_content).strip()

# 初始化飞书通知器
notifier = FeishuNotifier(config['feishu_webhook'], templates)

def job():
    """定时任务"""
    try:
        logger.info(f"开始执行回测任务，当前时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        run_backtest_task(db)
        logger.info("回测任务执行完成")
    except Exception as e:
        error_msg = f"回测任务执行失败: {e}\n{traceback.format_exc()}"
        logger.error(error_msg)
        notifier.send_crash(error_msg)

def main():
    """主函数"""
    logger.info("回测服务启动")
    
    # 设置定时任务，每小时运行一次
    schedule.every().hour.do(job)
    
    # 立即运行一次
    job()
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次是否有待运行的任务
    except KeyboardInterrupt:
        logger.info("回测服务被手动停止")
    except Exception as e:
        error_msg = f"回测服务异常退出: {e}\n{traceback.format_exc()}"
        logger.error(error_msg)
        notifier.send_crash(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()