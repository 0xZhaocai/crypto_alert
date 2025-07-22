#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
导入示例

此文件展示了如何使用重导出的模块来简化导入语句
"""

import os
import sys

# 确保能够导入src包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 方法1：使用src包直接导入所有重导出的模块
from src import ConfigLoader, Database, get_logger, AlertEngine, run_backtest_task, load_indicators

# 方法2：导入整个src包，然后使用点号访问
import src
config_loader = src.ConfigLoader("path/to/config")
db = src.Database("path/to/db")
# 首次调用get_logger需要提供log_path参数
log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'logs', 'crypto_alert.log')
logger = src.get_logger(log_path)

# 方法3：使用src.utils包导入工具模块
from src.utils import ConfigLoader, Database, get_logger

# 对比：原始导入方式
# from src.utils.config_loader import ConfigLoader
# from src.utils.database import Database
# from src.utils.logger import get_logger
# from src.core.alert_engine import AlertEngine
# from src.tasks.backtest_task import run_backtest_task
# from src.indicators import load_indicators

def main():
    """示例主函数"""
    # 使用导入的模块
    # 首次调用get_logger需要提供log_path参数
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'logs', 'crypto_alert.log')
    logger = get_logger(log_path)
    logger.info("示例程序启动")
    
    # 打印导入的模块信息，展示不同导入方式
    logger.info("导入方式示例：")
    logger.info("1. 直接从src包导入: ConfigLoader, Database, get_logger等")
    logger.info("2. 导入整个src包，然后使用点号访问: src.ConfigLoader, src.Database等")
    logger.info("3. 从src.utils包导入: ConfigLoader, Database, get_logger等")
    
    config_loader = ConfigLoader("path/to/config")
    db = Database("path/to/db")
    
    # 其他代码...

if __name__ == "__main__":
    main()