import sqlite3
import os
import sys

# 确保能够导入src包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 数据库路径
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'data', 'crypto_alert.db')

# 检查数据库文件是否存在
if not os.path.exists(db_path):
    print(f"数据库文件不存在: {db_path}")
    exit(1)

# 连接数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 获取所有表名
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("数据库中的表:")
for table in tables:
    print(f"- {table[0]}")
    
    # 获取表结构
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    
    print("  列结构:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # 获取表中的记录数
    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
    count = cursor.fetchone()[0]
    print(f"  记录数: {count}")
    
    # 如果是alerts表，显示最近的几条记录
    if table[0] == 'alerts' and count > 0:
        print("\n  最近的告警记录:")
        cursor.execute("SELECT alert_id, symbol_id, direction, score, price, created_at FROM alerts ORDER BY created_at DESC LIMIT 5")
        recent_alerts = cursor.fetchall()
        for alert in recent_alerts:
            print(f"  - ID: {alert[0]}, 交易对: {alert[1]}, 方向: {alert[2]}, 分数: {alert[3]}, 价格: {alert[4]}, 时间: {alert[5]}")
    
    # 如果是alert_performance表，显示最近的几条记录
    if table[0] == 'alert_performance' and count > 0:
        print("\n  最近的性能记录:")
        cursor.execute("""
        SELECT ap.performance_id, s.display_name, a.direction, a.price, ap.price_1h, ap.price_4h, ap.price_24h, ap.profit_if_follow
        FROM alert_performance ap
        JOIN alerts a ON ap.alert_id = a.alert_id
        JOIN symbols s ON a.symbol_id = s.symbol_id
        ORDER BY ap.performance_id DESC LIMIT 5
        """)
        recent_performances = cursor.fetchall()
        for perf in recent_performances:
            print(f"  - ID: {perf[0]}, 交易对: {perf[1]}, 方向: {perf[2]}, 初始价格: {perf[3]}, 1h价格: {perf[4]}, 4h价格: {perf[5]}, 24h价格: {perf[6]}, 收益: {perf[7]}%")
    
    print("\n")

# 关闭连接
conn.close()