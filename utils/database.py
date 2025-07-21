import os
import sqlite3
import datetime
from typing import Dict, Any, List, Optional, Tuple

class Database:
    """数据库工具类，用于管理SQLite数据库连接和操作"""
    
    def __init__(self, db_path: str):
        """初始化数据库连接
        
        Args:
            db_path: SQLite数据库文件路径
        """
        self.db_path = db_path
        
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 初始化数据库
        self.conn = None
        self.connect()
        self.create_tables()
    
    def connect(self) -> None:
        """连接到SQLite数据库"""
        self.conn = sqlite3.connect(self.db_path)
        # 启用外键约束
        self.conn.execute("PRAGMA foreign_keys = ON")
        # 配置连接以返回字典形式的结果
        self.conn.row_factory = sqlite3.Row
    
    def close(self) -> None:
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def create_tables(self) -> None:
        """创建必要的数据库表"""
        cursor = self.conn.cursor()
        
        # 创建symbols表，存储交易对信息
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS symbols (
            symbol_id TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        
        # 创建symbol_status表，存储交易对状态
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS symbol_status (
            symbol_id TEXT PRIMARY KEY,
            is_long INTEGER NOT NULL DEFAULT 0,
            is_short INTEGER NOT NULL DEFAULT 0,
            last_long_score INTEGER NOT NULL DEFAULT 0,
            last_short_score INTEGER NOT NULL DEFAULT 0,
            error_count INTEGER NOT NULL DEFAULT 0,
            signal_disappeared_time TEXT,
            last_price REAL NOT NULL DEFAULT 0,
            last_rsi REAL NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (symbol_id) REFERENCES symbols(symbol_id)
        )
        """)
        
        # 创建alerts表，存储发送的提醒记录
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol_id TEXT NOT NULL,
            direction TEXT NOT NULL,
            score INTEGER NOT NULL,
            price REAL NOT NULL,
            rsi REAL NOT NULL,
            ema21_15m REAL,
            ema21_1h REAL,
            price_ema_gap_ratio REAL,
            atr_ratio REAL,
            volume_ratio REAL,
            message_content TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (symbol_id) REFERENCES symbols(symbol_id)
        )
        """)
        
        # 创建alert_performance表，存储告警后的价格变化情况
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS alert_performance (
            performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id INTEGER NOT NULL,
            price_1h REAL,
            price_4h REAL,
            price_24h REAL,
            price_change_1h REAL,
            price_change_4h REAL,
            price_change_24h REAL,
            profit_if_follow REAL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (alert_id) REFERENCES alerts(alert_id)
        )
        """)
        
        self.conn.commit()
    
    def init_symbols(self, symbols: Dict[str, str]) -> None:
        """初始化交易对信息
        
        Args:
            symbols: 包含交易对符号和显示名称的字典
        """
        cursor = self.conn.cursor()
        now = datetime.datetime.now().isoformat()
        
        # 获取现有的交易对
        cursor.execute("SELECT symbol_id FROM symbols")
        existing_symbols = {row['symbol_id'] for row in cursor.fetchall()}
        
        # 添加新的交易对
        for symbol_id, display_name in symbols.items():
            if symbol_id not in existing_symbols:
                cursor.execute(
                    "INSERT INTO symbols (symbol_id, display_name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (symbol_id, display_name, now, now)
                )
            else:
                cursor.execute(
                    "UPDATE symbols SET display_name = ?, is_active = 1, updated_at = ? WHERE symbol_id = ?",
                    (display_name, now, symbol_id)
                )
        
        # 将不在配置中的交易对标记为非活动
        placeholders = ', '.join(['?'] * len(symbols))
        if symbols:
            cursor.execute(
                f"UPDATE symbols SET is_active = 0, updated_at = ? WHERE symbol_id NOT IN ({placeholders})",
                [now] + list(symbols.keys())
            )
        
        self.conn.commit()
        
        # 初始化交易对状态
        for symbol_id in symbols.keys():
            self.init_symbol_status(symbol_id)
    
    def init_symbol_status(self, symbol_id: str) -> None:
        """初始化交易对状态
        
        Args:
            symbol_id: 交易对符号
        """
        cursor = self.conn.cursor()
        now = datetime.datetime.now().isoformat()
        
        # 检查状态是否已存在
        cursor.execute("SELECT 1 FROM symbol_status WHERE symbol_id = ?", (symbol_id,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO symbol_status (symbol_id, updated_at) VALUES (?, ?)",
                (symbol_id, now)
            )
            self.conn.commit()
    
    def get_active_symbols(self) -> List[Dict[str, str]]:
        """获取活动的交易对列表
        
        Returns:
            包含交易对信息的列表，每个元素是包含symbol和name的字典
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT symbol_id, display_name FROM symbols WHERE is_active = 1"
        )
        return [{'symbol': row['symbol_id'], 'name': row['display_name']} for row in cursor.fetchall()]
    
    def get_symbol_status(self, symbol_id: str) -> Dict[str, Any]:
        """获取交易对状态
        
        Args:
            symbol_id: 交易对符号
            
        Returns:
            包含交易对状态的字典
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM symbol_status WHERE symbol_id = ?",
            (symbol_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            return {}
        
        result = dict(row)
        
        # 将is_long和is_short转换为布尔值
        result['long'] = bool(result.pop('is_long'))
        result['short'] = bool(result.pop('is_short'))
        
        # 将signal_disappeared_time转换为datetime对象
        if result['signal_disappeared_time']:
            result['signal_disappeared_time'] = datetime.datetime.fromisoformat(result['signal_disappeared_time'])
        
        return result
    
    def update_symbol_status(self, symbol_id: str, status: Dict[str, Any]) -> None:
        """更新交易对状态
        
        Args:
            symbol_id: 交易对符号
            status: 包含交易对状态的字典
        """
        cursor = self.conn.cursor()
        now = datetime.datetime.now().isoformat()
        
        # 准备更新数据
        update_data = {}
        
        if 'long' in status:
            update_data['is_long'] = 1 if status['long'] else 0
        if 'short' in status:
            update_data['is_short'] = 1 if status['short'] else 0
        if 'last_long_score' in status:
            update_data['last_long_score'] = status['last_long_score']
        if 'last_short_score' in status:
            update_data['last_short_score'] = status['last_short_score']
        if 'error_count' in status:
            update_data['error_count'] = status['error_count']
        if 'signal_disappeared_time' in status:
            if status['signal_disappeared_time'] is None:
                update_data['signal_disappeared_time'] = None
            else:
                update_data['signal_disappeared_time'] = status['signal_disappeared_time'].isoformat()
        if 'last_price' in status:
            update_data['last_price'] = status['last_price']
        if 'last_rsi' in status:
            update_data['last_rsi'] = status['last_rsi']
        
        update_data['updated_at'] = now
        
        # 构建SQL更新语句
        if update_data:
            fields = ', '.join([f"{k} = ?" for k in update_data.keys()])
            values = list(update_data.values())
            
            cursor.execute(
                f"UPDATE symbol_status SET {fields} WHERE symbol_id = ?",
                values + [symbol_id]
            )
            self.conn.commit()
    
    def record_alert(self, symbol_id: str, direction: str, score: int, price: float, rsi: float, 
                     metrics: dict = None, message_content: str = None) -> int:
        """记录发送的提醒
        
        Args:
            symbol_id: 交易对符号
            direction: 信号方向 (多/空)
            score: 信号分数
            price: 当前价格
            rsi: 当前RSI值
            metrics: 其他技术指标数据
            message_content: 发送的消息内容
            
        Returns:
            新插入记录的ID
        """
        cursor = self.conn.cursor()
        now = datetime.datetime.now().isoformat()
        
        # 提取指标数据，如果没有提供则使用None
        ema21_15m = metrics.get('ema21_15m') if metrics else None
        ema21_1h = metrics.get('ema21_1h') if metrics else None
        price_ema_gap_ratio = metrics.get('price_ema_gap_ratio') if metrics else None
        atr_ratio = metrics.get('atr_ratio') if metrics else None
        volume_ratio = metrics.get('volume_ratio') if metrics else None
        
        cursor.execute(
            "INSERT INTO alerts (symbol_id, direction, score, price, rsi, "
            "ema21_15m, ema21_1h, price_ema_gap_ratio, atr_ratio, volume_ratio, "
            "message_content, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (symbol_id, direction, score, price, rsi, 
             ema21_15m, ema21_1h, price_ema_gap_ratio, atr_ratio, volume_ratio, 
             message_content, now)
        )
        
        # 获取新插入记录的ID
        alert_id = cursor.lastrowid
        
        self.conn.commit()
        return alert_id
    
    def get_recent_alerts(self, symbol_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的提醒记录
        
        Args:
            symbol_id: 交易对符号，如果为None则获取所有交易对的提醒
            limit: 返回的记录数量限制
            
        Returns:
            包含提醒记录的列表
        """
        cursor = self.conn.cursor()
        
        if symbol_id:
            cursor.execute(
                """SELECT a.*, s.display_name 
                   FROM alerts a 
                   JOIN symbols s ON a.symbol_id = s.symbol_id 
                   WHERE a.symbol_id = ? 
                   ORDER BY a.created_at DESC LIMIT ?""",
                (symbol_id, limit)
            )
        else:
            cursor.execute(
                """SELECT a.*, s.display_name 
                   FROM alerts a 
                   JOIN symbols s ON a.symbol_id = s.symbol_id 
                   ORDER BY a.created_at DESC LIMIT ?""",
                (limit,)
            )
        
        return [dict(row) for row in cursor.fetchall()]
        
    def record_alert_performance(self, alert_id: int, price_data: Dict[str, float]) -> None:
        """记录告警后的价格变化情况
        
        Args:
            alert_id: 告警ID
            price_data: 价格数据字典，包含以下键：
                - price_1h: 1小时后的价格
                - price_4h: 4小时后的价格
                - price_24h: 24小时后的价格
                - initial_price: 初始价格
                - direction: 信号方向 ('long' 或 'short')
        """
        cursor = self.conn.cursor()
        now = datetime.datetime.now().isoformat()
        
        # 获取初始价格和方向
        initial_price = price_data.get('initial_price')
        direction = price_data.get('direction')
        
        # 计算价格变化百分比
        price_1h = price_data.get('price_1h')
        price_4h = price_data.get('price_4h')
        price_24h = price_data.get('price_24h')
        
        price_change_1h = ((price_1h / initial_price) - 1) * 100 if price_1h and initial_price else None
        price_change_4h = ((price_4h / initial_price) - 1) * 100 if price_4h and initial_price else None
        price_change_24h = ((price_24h / initial_price) - 1) * 100 if price_24h and initial_price else None
        
        # 计算如果跟随信号的收益率
        # 做多时，收益率 = 价格变化率
        # 做空时，收益率 = -价格变化率
        profit_if_follow = None
        if direction == 'long' and price_change_24h is not None:
            profit_if_follow = price_change_24h
        elif direction == 'short' and price_change_24h is not None:
            profit_if_follow = -price_change_24h
        
        cursor.execute("""
        INSERT INTO alert_performance 
        (alert_id, price_1h, price_4h, price_24h, price_change_1h, price_change_4h, price_change_24h, profit_if_follow, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (alert_id, price_1h, price_4h, price_24h, price_change_1h, price_change_4h, price_change_24h, profit_if_follow, now))
        
        self.conn.commit()
        
    def get_alert_performance(self, alert_id: Optional[int] = None, days: int = 30) -> List[Dict[str, Any]]:
        """获取告警性能数据
        
        Args:
            alert_id: 可选，告警ID，如果提供则只返回该告警的性能数据
            days: 返回最近多少天的数据，默认30天
            
        Returns:
            告警性能数据列表
        """
        cursor = self.conn.cursor()
        
        # 计算days天前的日期
        days_ago = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
        
        if alert_id:
            cursor.execute("""
            SELECT p.performance_id, p.alert_id, a.symbol_id, s.display_name, a.direction, a.score,
                   a.price, p.price_1h, p.price_4h, p.price_24h, 
                   p.price_change_1h, p.price_change_4h, p.price_change_24h, 
                   p.profit_if_follow, a.created_at, p.updated_at
            FROM alert_performance p
            JOIN alerts a ON p.alert_id = a.alert_id
            JOIN symbols s ON a.symbol_id = s.symbol_id
            WHERE p.alert_id = ?
            ORDER BY a.created_at DESC
            """, (alert_id,))
        else:
            cursor.execute("""
            SELECT p.performance_id, p.alert_id, a.symbol_id, s.display_name, a.direction, a.score,
                   a.price, p.price_1h, p.price_4h, p.price_24h, 
                   p.price_change_1h, p.price_change_4h, p.price_change_24h, 
                   p.profit_if_follow, a.created_at, p.updated_at
            FROM alert_performance p
            JOIN alerts a ON p.alert_id = a.alert_id
            JOIN symbols s ON a.symbol_id = s.symbol_id
            WHERE a.created_at > ?
            ORDER BY a.created_at DESC
            """, (days_ago,))
            
        performances = []
        for row in cursor.fetchall():
            performances.append({
                'performance_id': row[0],
                'alert_id': row[1],
                'symbol_id': row[2],
                'display_name': row[3],
                'direction': row[4],
                'score': row[5],
                'initial_price': row[6],
                'price_1h': row[7],
                'price_4h': row[8],
                'price_24h': row[9],
                'price_change_1h': row[10],
                'price_change_4h': row[11],
                'price_change_24h': row[12],
                'profit_if_follow': row[13],
                'alert_time': row[14],
                'updated_at': row[15]
            })
            
        return performances
        
    def get_performance_summary(self, days: int = 30) -> Dict[str, Any]:
        """获取告警性能统计摘要
        
        Args:
            days: 统计最近多少天的数据，默认30天
            
        Returns:
            性能统计摘要字典
        """
        cursor = self.conn.cursor()
        
        # 计算days天前的日期
        days_ago = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
        
        # 获取总体统计数据
        cursor.execute("""
        SELECT 
            COUNT(*) as total_alerts,
            SUM(CASE WHEN profit_if_follow > 0 THEN 1 ELSE 0 END) as profitable_alerts,
            AVG(profit_if_follow) as avg_profit,
            MAX(profit_if_follow) as max_profit,
            MIN(profit_if_follow) as max_loss
        FROM alert_performance p
        JOIN alerts a ON p.alert_id = a.alert_id
        WHERE a.created_at > ?
        """, (days_ago,))
        
        row = cursor.fetchone()
        total_alerts = row[0] if row[0] else 0
        profitable_alerts = row[1] if row[1] else 0
        avg_profit = row[2] if row[2] else 0
        max_profit = row[3] if row[3] else 0
        max_loss = row[4] if row[4] else 0
        
        # 计算胜率
        win_rate = (profitable_alerts / total_alerts * 100) if total_alerts > 0 else 0
        
        # 按方向统计
        cursor.execute("""
        SELECT 
            a.direction,
            COUNT(*) as total,
            SUM(CASE WHEN profit_if_follow > 0 THEN 1 ELSE 0 END) as profitable,
            AVG(profit_if_follow) as avg_profit
        FROM alert_performance p
        JOIN alerts a ON p.alert_id = a.alert_id
        WHERE a.created_at > ?
        GROUP BY a.direction
        """, (days_ago,))
        
        direction_stats = {}
        for row in cursor.fetchall():
            direction = row[0]
            total = row[1] if row[1] else 0
            profitable = row[2] if row[2] else 0
            avg_profit = row[3] if row[3] else 0
            win_rate_dir = (profitable / total * 100) if total > 0 else 0
            
            direction_stats[direction] = {
                'total': total,
                'profitable': profitable,
                'win_rate': win_rate_dir,
                'avg_profit': avg_profit
            }
        
        return {
            'total_alerts': total_alerts,
            'profitable_alerts': profitable_alerts,
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'by_direction': direction_stats
        }