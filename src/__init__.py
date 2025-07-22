# -*- coding: utf-8 -*-

"""
加密货币价格告警系统包

此文件重导出所有主要模块，以简化导入语句
"""

# 从utils模块导出
from src.utils.config_loader import ConfigLoader, load_config
from src.utils.database import Database
from src.utils.logger import get_logger, setup_logger

# 从core模块导出
from src.core.alert_engine import AlertEngine
from src.core.data_fetcher import DataFetcher
from src.core.signal_evaluator import SignalEvaluator

# 从tasks模块导出
from src.tasks.backtest_task import run_backtest_task

# 从indicators模块导出
from src.indicators import load_indicators

# 从notifiers模块导出
from src.notifiers.feishu_notifier import FeishuNotifier

# 从analysis模块导出
from src.analysis.performance_analyzer import run_performance_analysis