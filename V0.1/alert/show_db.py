#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信号记录数据库查询工具

功能：
1. 查看所有信号记录
2. 按代币筛选记录
3. 按方向筛选记录
4. 统计分析
5. 查看最近记录

使用方法：
    python show_db.py --help
    python show_db.py --all
    python show_db.py --symbol BTCUSDT
    python show_db.py --direction 多
    python show_db.py --stats
    python show_db.py --recent 10
"""

import sqlite3
import argparse
import os
from datetime import datetime
import tabulate

# 数据库文件路径
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "signals.db")

def check_database():
    """检查数据库是否存在"""
    if not os.path.exists(DB_FILE):
        print(f"❌ 数据库文件不存在: {DB_FILE}")
        print("请先运行 alert_15m.py 生成信号记录")
        return False
    return True

def get_connection():
    """获取数据库连接"""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row  # 使结果可以按列名访问
        return conn
    except Exception as e:
        print(f"❌ 连接数据库失败: {e}")
        return None

def show_all_records(limit=None):
    """显示所有记录"""
    conn = get_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM signal_records ORDER BY timestamp DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        records = cursor.fetchall()
        
        if not records:
            print("📭 暂无信号记录")
            return
        
        # 准备表格数据
        headers = ['ID', '代币', '时间', '方向', '分数', '价格', '条件数']
        table_data = []
        
        for record in records:
            # 计算满足的条件数量
            conditions_count = sum([
                record['price_above_ema21_15m'],
                record['price_above_ema21_1h'],
                record['price_below_ema21_15m'],
                record['price_below_ema21_1h'],
                record['rsi_in_range'],
                record['price_near_ema21'],
                record['atr_amplified'],
                record['volume_amplified'],
                record['ema_convergence']
            ])
            
            table_data.append([
                record['id'],
                record['symbol'],
                record['timestamp'],
                record['direction'],
                record['score'],
                f"{record['price']:.4f}",
                conditions_count
            ])
        
        print(f"\n📊 信号记录 (共 {len(records)} 条)")
        print(tabulate.tabulate(table_data, headers=headers, tablefmt='grid'))
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
    finally:
        conn.close()

def show_by_symbol(symbol):
    """按代币筛选记录"""
    conn = get_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM signal_records WHERE symbol = ? ORDER BY timestamp DESC",
            (symbol,)
        )
        records = cursor.fetchall()
        
        if not records:
            print(f"📭 {symbol} 暂无信号记录")
            return
        
        print(f"\n📊 {symbol} 信号记录 (共 {len(records)} 条)")
        show_detailed_records(records)
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
    finally:
        conn.close()

def show_by_direction(direction):
    """按方向筛选记录"""
    conn = get_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM signal_records WHERE direction = ? ORDER BY timestamp DESC",
            (direction,)
        )
        records = cursor.fetchall()
        
        if not records:
            print(f"📭 {direction}头信号暂无记录")
            return
        
        print(f"\n📊 {direction}头信号记录 (共 {len(records)} 条)")
        show_detailed_records(records)
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
    finally:
        conn.close()

def show_detailed_records(records):
    """显示详细记录"""
    for i, record in enumerate(records, 1):
        print(f"\n--- 记录 {i} ---")
        print(f"ID: {record['id']}")
        print(f"代币: {record['symbol']}")
        print(f"时间: {record['timestamp']}")
        print(f"方向: {record['direction']}")
        print(f"分数: {record['score']}")
        print(f"价格: {record['price']:.4f}")
        
        # 显示满足的条件
        conditions = []
        if record['price_above_ema21_15m']:
            conditions.append("价格 > EMA21(15m)")
        if record['price_above_ema21_1h']:
            conditions.append("价格 > EMA21(1h)")
        if record['price_below_ema21_15m']:
            conditions.append("价格 < EMA21(15m)")
        if record['price_below_ema21_1h']:
            conditions.append("价格 < EMA21(1h)")
        if record['rsi_in_range']:
            conditions.append("RSI在区间内")
        if record['price_near_ema21']:
            conditions.append("贴近15mEMA21")
        if record['atr_amplified']:
            conditions.append("ATR放大")
        if record['volume_amplified']:
            conditions.append("成交量放大")
        if record['ema_convergence']:
            conditions.append("EMA靠近")
        
        print(f"满足条件: {', '.join(conditions)}")

def show_statistics():
    """显示统计信息"""
    conn = get_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # 总体统计
        cursor.execute("SELECT COUNT(*) as total FROM signal_records")
        total = cursor.fetchone()['total']
        
        if total == 0:
            print("📭 暂无信号记录")
            return
        
        print(f"\n📈 信号统计分析")
        print(f"总记录数: {total}")
        
        # 按方向统计
        cursor.execute("""
            SELECT direction, COUNT(*) as count, AVG(score) as avg_score 
            FROM signal_records 
            GROUP BY direction
        """)
        direction_stats = cursor.fetchall()
        
        print("\n📊 按方向统计:")
        for stat in direction_stats:
            print(f"  {stat['direction']}头: {stat['count']} 次, 平均分数: {stat['avg_score']:.1f}")
        
        # 按代币统计
        cursor.execute("""
            SELECT symbol, COUNT(*) as count, AVG(score) as avg_score 
            FROM signal_records 
            GROUP BY symbol 
            ORDER BY count DESC
        """)
        symbol_stats = cursor.fetchall()
        
        print("\n🪙 按代币统计:")
        for stat in symbol_stats:
            print(f"  {stat['symbol']}: {stat['count']} 次, 平均分数: {stat['avg_score']:.1f}")
        
        # 条件统计
        cursor.execute("""
            SELECT 
                SUM(price_above_ema21_15m) as price_above_ema21_15m,
                SUM(price_above_ema21_1h) as price_above_ema21_1h,
                SUM(price_below_ema21_15m) as price_below_ema21_15m,
                SUM(price_below_ema21_1h) as price_below_ema21_1h,
                SUM(rsi_in_range) as rsi_in_range,
                SUM(price_near_ema21) as price_near_ema21,
                SUM(atr_amplified) as atr_amplified,
                SUM(volume_amplified) as volume_amplified,
                SUM(ema_convergence) as ema_convergence
            FROM signal_records
        """)
        condition_stats = cursor.fetchone()
        
        print("\n🎯 条件出现频率:")
        conditions = [
            ("价格 > EMA21(15m)", condition_stats['price_above_ema21_15m']),
            ("价格 > EMA21(1h)", condition_stats['price_above_ema21_1h']),
            ("价格 < EMA21(15m)", condition_stats['price_below_ema21_15m']),
            ("价格 < EMA21(1h)", condition_stats['price_below_ema21_1h']),
            ("RSI在区间内", condition_stats['rsi_in_range']),
            ("贴近15mEMA21", condition_stats['price_near_ema21']),
            ("ATR放大", condition_stats['atr_amplified']),
            ("成交量放大", condition_stats['volume_amplified']),
            ("EMA靠近", condition_stats['ema_convergence'])
        ]
        
        for condition, count in conditions:
            percentage = (count / total) * 100
            print(f"  {condition}: {count} 次 ({percentage:.1f}%)")
        
        # 分数分布
        cursor.execute("""
            SELECT score, COUNT(*) as count 
            FROM signal_records 
            GROUP BY score 
            ORDER BY score
        """)
        score_stats = cursor.fetchall()
        
        print("\n🎯 分数分布:")
        for stat in score_stats:
            print(f"  {stat['score']}分: {stat['count']} 次")
        
    except Exception as e:
        print(f"❌ 统计失败: {e}")
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(
        description='信号记录数据库查询工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python show_db.py --all                 # 显示所有记录
  python show_db.py --recent 10           # 显示最近10条记录
  python show_db.py --symbol BTCUSDT      # 显示BTCUSDT的记录
  python show_db.py --direction 多        # 显示多头信号记录
  python show_db.py --stats               # 显示统计信息
        """
    )
    
    parser.add_argument('--all', action='store_true', help='显示所有记录')
    parser.add_argument('--recent', type=int, metavar='N', help='显示最近N条记录')
    parser.add_argument('--symbol', type=str, help='按代币筛选 (如: BTCUSDT)')
    parser.add_argument('--direction', type=str, choices=['多', '空'], help='按方向筛选')
    parser.add_argument('--stats', action='store_true', help='显示统计信息')
    
    args = parser.parse_args()
    
    # 检查数据库
    if not check_database():
        return
    
    # 如果没有参数，显示帮助
    if not any([args.all, args.recent, args.symbol, args.direction, args.stats]):
        parser.print_help()
        return
    
    print(f"🔍 信号记录数据库查询工具")
    print(f"数据库: {DB_FILE}")
    
    # 执行相应的查询
    if args.all:
        show_all_records()
    elif args.recent:
        show_all_records(args.recent)
    elif args.symbol:
        show_by_symbol(args.symbol.upper())
    elif args.direction:
        show_by_direction(args.direction)
    elif args.stats:
        show_statistics()

if __name__ == "__main__":
    try:
        # 检查是否安装了tabulate
        import tabulate
    except ImportError:
        print("❌ 缺少依赖包 tabulate")
        print("请运行: pip install tabulate")
        exit(1)
    
    main()