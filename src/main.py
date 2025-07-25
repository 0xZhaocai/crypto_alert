#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import traceback
import argparse

from src.utils.config_loader import ConfigLoader
from src.utils.database import Database
from src.utils.logger import get_logger
from src.core.alert_engine import AlertEngine
from src.tasks.backtest_task import run_backtest_task
from src.indicators import load_indicators

def setup_basic_logging():
    """设置基本的日志记录，在配置加载前使用"""
    try:
        # 确保日志目录存在
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'logs')
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
    parser.add_argument('--show-metrics', type=str, help='显示指定代币的详细指标参数，例如：--show-metrics BTCUSDT')
    parser.add_argument('--help-metrics', action='store_true', help='显示指标参数说明')
    args = parser.parse_args()
    try:
        # 确保ConfigLoader已正确导入
        from src.utils.config_loader import ConfigLoader
        
        # 获取配置目录路径
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'config')
        
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
        
        # 根据参数决定执行告警检查、回测任务、显示指标详情或显示帮助信息
        if args.help_metrics:
            logger.info("显示指标参数说明...")
            print("\n===== 指标参数说明 =====")
            print("\n--- EMA指标 ---")
            print("EMA21: 21周期指数移动平均线，用于判断价格趋势")
            print("价格与EMA偏离比例: 价格与EMA的距离占EMA的百分比，越小表示价格越贴近EMA")
            
            print("\n--- RSI指标 ---")
            print("RSI: 相对强弱指数，用于判断市场是否超买或超卖")
            print("RSI值范围: 0-100，通常认为低于30为超卖，高于70为超买")
            
            print("\n--- ATR指标 ---")
            print("ATR: 平均真实波幅，用于衡量市场波动性")
            print("ATR比率: 当前ATR与前N周期ATR的比值，大于1表示波动性增加")
            
            print("\n--- 成交量指标 ---")
            print("成交量比率: 当前成交量与前N周期平均成交量的比值，大于1表示成交量放大")
            
            print("\n--- ZigZag指标 ---")
            print("ZigZag: 通过连接重要的价格转折点来过滤市场噪音，帮助识别关键的支撑和阻力位")
            print("趋势: up(上升)、down(下降)或neutral(中性)")
            print("形态: W底、M顶、整理或未知")
            print("偏差百分比: 价格变动百分比阈值，用于确定转折点")
            print("极轴腿数量: 用于控制识别的转折点数量")
            
            print("\n--- 信号评估 ---")
            print("做多/做空得分: 根据各项指标计算的综合得分")
            print("得分阈值: 当得分达到阈值时，系统会发出交易信号")
            print("\n使用示例: python run.py --show-metrics BTCUSDT")
            logger.info("指标参数说明显示完成")
            return
        elif args.show_metrics:
            logger.info(f"显示代币 {args.show_metrics} 的详细指标参数...")
            from src.core.data_fetcher import DataFetcher
            
            # 创建数据获取器
            data_fetcher = DataFetcher()
            
            try:
                # 获取指标数据
                metrics = data_fetcher.get_current_metrics(args.show_metrics, alert_config)
                
                # 打印指标详情
                print(f"\n===== {args.show_metrics} 指标详情 =====")
                print(f"当前价格: {metrics['price']:.4f} USDT")
                
                print(f"\n--- EMA指标 ---")
                print(f"EMA21(5分钟): {metrics['ema21_5m']:.4f}")
                print(f"EMA21(15分钟): {metrics['ema21_15m']:.4f}")
                print(f"EMA21(1小时): {metrics['ema21_1h']:.4f}")
                print(f"价格与EMA偏离比例: {metrics['price_ema_gap_ratio']:.4%}")
                print(f"价格位于EMA之上/之下: {metrics['price'] > metrics['ema21_15m'] and '上方' or '下方'} (15分钟)")
                print(f"价格位于EMA之上/之下: {metrics['price'] > metrics['ema21_1h'] and '上方' or '下方'} (1小时)")
                
                print(f"\n--- RSI指标 ---")
                if 'rsi_5m' in metrics:
                    print(f"RSI(5分钟): {metrics['rsi_5m']:.2f}")
                else:
                    print("RSI数据不可用")
                
                print(f"\n--- ATR指标 ---")
                print(f"ATR比率: {metrics['atr_ratio']:.2f}x")
                
                print(f"\n--- 成交量指标 ---")
                print(f"成交量比率: {metrics['volume_ratio']:.2f}x")
                
                print(f"\n--- ZigZag指标 ---")
                print(f"趋势: {metrics['zigzag']['trend']}")
                print(f"形态: {metrics['zigzag']['pattern']}")
                print(f"偏差百分比: {metrics['zigzag_deviation']}%")
                print(f"极轴腿数量: {metrics['zigzag_depth']}")
                
                # 打印指标原始数据点
                print(f"\n--- 指标原始数据点 ---")
                print(f"ZigZag点位索引: {metrics['zigzag_points']}")
                print(f"ZigZag点位价格: {[float('{:.4f}'.format(v)) for v in metrics['zigzag_values']]}")
                
                # 打印信号评估结果
                print(f"\n--- 信号评估 ---")
                from src.core.signal_evaluator import SignalEvaluator
                evaluator = SignalEvaluator(alert_config)
                long_score, short_score, long_details, short_details = evaluator.evaluate_signals(metrics)
                print(f"做多得分: {long_score}/{evaluator.max_possible_score} ({long_score/evaluator.max_possible_score*100:.1f}%)")
                print(f"做空得分: {short_score}/{evaluator.max_possible_score} ({short_score/evaluator.max_possible_score*100:.1f}%)")
                
                print(f"\n做多详情:")
                for detail in long_details:
                    print(f"  - {detail}")
                
                print(f"\n做空详情:")
                for detail in short_details:
                    print(f"  - {detail}")
                
                logger.info(f"显示代币 {args.show_metrics} 的详细指标参数完成")
            except Exception as e:
                logger.error(f"获取代币 {args.show_metrics} 的指标数据失败: {e}")
                print(f"错误: 获取代币 {args.show_metrics} 的指标数据失败: {e}")
        elif args.backtest:
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
            # 确保即使在配置加载失败的情况下也能发送崩溃通知
            from src.notifiers.feishu_notifier import FeishuNotifier
            from datetime import datetime
            
            # 获取当前时间戳
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
                    # 确保ConfigLoader已定义
                    if 'ConfigLoader' not in locals() and 'ConfigLoader' not in globals():
                        from src.utils.config_loader import ConfigLoader
                    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'config')
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