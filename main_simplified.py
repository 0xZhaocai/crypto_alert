#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
加密货币价格告警系统入口点（简化导入版本）

此文件展示了如何使用重导出的模块来简化main.py中的导入语句
"""

import os
import sys
import traceback
import argparse

# 确保当前目录在系统路径中，以便能够导入src包
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 使用重导出的模块简化导入
from src import (
    ConfigLoader, Database, get_logger,
    AlertEngine, run_backtest_task, load_indicators,
    FeishuNotifier
)

def setup_basic_logging():
    """设置基本的日志记录，在配置加载前使用"""
    try:
        # 确保日志目录存在
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # 设置基本日志文件
        basic_log_path = os.path.join(log_dir, 'crypto_alert.log')
        return get_logger(basic_log_path)
    except Exception as e:
        print(f"设置基本日志失败: {e}")
        return None

def main():
    """主函数，加载配置并启动告警引擎，可选执行回测任务"""
    
    # 设置基本日志记录
    logger = setup_basic_logging()
    if logger:
        logger.info("程序启动")
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='加密货币价格告警系统')
    parser.add_argument('--backtest', action='store_true', help='执行回测任务')
    args = parser.parse_args()
    try:
        # 获取配置目录路径
        config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'config')
        
        # 加载配置
        config_loader = ConfigLoader(config_dir)
        config_loader.load_all_configs()
        
        # 获取配置
        alert_config = config_loader.get_alert_config()
        symbols = config_loader.get_symbols_list()
        
        # 确保日志目录存在
        os.makedirs(os.path.dirname(alert_config['log_path']), exist_ok=True)
        
        # 初始化日志
        logger = get_logger(alert_config['log_path'], alert_config['log_level'])
        logger.info("加载配置成功")
        
        # 初始化数据库
        db = Database(alert_config['db_path'])
        logger.info(f"数据库初始化成功: {alert_config['db_path']}")
        
        # 加载指标插件
        load_indicators()
        logger.info("指标插件加载成功")
        
        # 根据参数决定执行告警检查还是回测任务
        if args.backtest:
            logger.info("开始执行回测任务...")
            run_backtest_task(db)
            logger.info("回测任务完成")
        else:
            # 创建并运行告警引擎
            engine = AlertEngine(alert_config, config_loader.symbols, db)
            engine.run()
            
            logger.info("告警检查完成")
        
    except Exception as e:
        # 获取异常的详细信息
        error_msg = f"程序异常退出: {e}\n{traceback.format_exc()}"
        
        # 尝试记录到日志
        try:
            # 如果已经有日志记录器，直接使用
            if 'logger' in locals() and logger:
                logger.critical(error_msg)
            else:
                # 尝试获取或创建日志记录器
                try:
                    logger = setup_basic_logging()
                    if logger:
                        logger.critical(error_msg)
                    else:
                        # 如果无法创建基本日志记录器，尝试使用全局日志记录器
                        logger = get_logger()
                        logger.critical(error_msg)
                except Exception as basic_log_error:
                    print(f"创建基本日志记录器失败: {basic_log_error}")
                    try:
                        # 最后尝试使用全局日志记录器
                        logger = get_logger()
                        logger.critical(error_msg)
                    except Exception as global_log_error:
                        print(f"使用全局日志记录器失败: {global_log_error}")
                        print(error_msg)
        except Exception as log_error:
            print(f"记录日志失败: {log_error}")
            print(error_msg)
        
        # 尝试发送崩溃通知
        try:
            # 获取当前时间戳
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 准备详细的错误信息
            crash_info = f"{str(e)}\n\n详细错误信息:\n{traceback.format_exc()}"
            
            # 初始化变量
            webhook_url = None
            
            # 如果配置加载成功，使用配置中的webhook
            try:
                # 检查是否已经有配置加载
                if 'alert_config' in locals() and alert_config:
                    webhook_url = alert_config.get('feishu_webhook')
                else:
                    # 配置加载失败，尝试直接从配置文件读取webhook
                    config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'config')
                    config_loader = ConfigLoader(config_dir)
                    config_loader.load_alert_config()
                    
                    alert_config = config_loader.get_alert_config()
                    webhook_url = alert_config.get('feishu_webhook')
            except Exception as config_error:
                print(f"获取飞书配置失败: {config_error}")
                # 即使配置加载失败，也继续尝试发送通知
            
            # 创建飞书通知器并发送崩溃通知
            notifier = FeishuNotifier(webhook_url)
            send_result = notifier.send_crash(crash_info, timestamp=timestamp)
            
            if send_result:
                print("已发送崩溃通知")
            elif webhook_url:
                print("发送崩溃通知失败，可能是模板配置错误或网络问题")
            else:
                print("未配置飞书webhook，无法发送崩溃通知")
                
        except Exception as notify_error:
            print(f"发送崩溃通知失败: {notify_error}")
        
        # 返回非零退出码
        sys.exit(1)

if __name__ == "__main__":
    main()