import datetime
import time
from typing import Dict, Any, List, Optional

from core.data_fetcher import DataFetcher
from utils.database import Database
from utils.logger import get_logger

class BacktestTask:
    """回测任务，用于定期检查已发送的告警，并记录价格变化情况"""
    
    def __init__(self, db: Database):
        """初始化回测任务
        
        Args:
            db: 数据库实例
        """
        self.db = db
        self.data_fetcher = DataFetcher()
        self.logger = get_logger()
    
    def run(self) -> None:
        """运行回测任务，检查需要回测的告警"""
        self.logger.info(f"开始回测任务... 当前时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 获取最近24小时内的告警，且尚未完成24小时回测的
        alerts = self._get_alerts_to_backtest()
        
        if not alerts:
            self.logger.info("没有需要回测的告警")
            return
            
        self.logger.info(f"找到{len(alerts)}个需要回测的告警")
        
        for alert in alerts:
            self._process_alert(alert)
            
        self.logger.info("回测任务完成")
    
    def _get_alerts_to_backtest(self) -> List[Dict[str, Any]]:
        """获取需要回测的告警列表
        
        Returns:
            需要回测的告警列表
        """
        # 获取最近48小时内的所有告警
        recent_alerts = self.db.get_recent_alerts(limit=100)
        
        # 筛选出需要回测的告警
        alerts_to_backtest = []
        now = datetime.datetime.now()
        
        for alert in recent_alerts:
            # 解析告警时间
            alert_time = datetime.datetime.fromisoformat(alert['created_at'])
            
            # 计算告警发出后的时间间隔
            hours_since_alert = (now - alert_time).total_seconds() / 3600
            
            # 获取该告警的回测记录
            cursor = self.db.conn.cursor()
            cursor.execute("""
            SELECT price_1h, price_4h, price_24h 
            FROM alert_performance 
            WHERE alert_id = ?
            """, (alert['alert_id'],))
            
            performance = cursor.fetchone()
            
            # 根据时间间隔和已有回测记录决定需要进行哪种回测
            if 1 <= hours_since_alert < 4:
                # 需要进行1小时回测，检查是否已有1小时回测记录
                if not performance or performance[0] is None:
                    alert['backtest_type'] = '1h'
                    alerts_to_backtest.append(alert)
            elif 4 <= hours_since_alert < 24:
                # 需要进行4小时回测，检查是否已有4小时回测记录
                if not performance or performance[1] is None:
                    alert['backtest_type'] = '4h'
                    alerts_to_backtest.append(alert)
            elif 24 <= hours_since_alert < 48:
                # 需要进行24小时回测，检查是否已有24小时回测记录
                if not performance or performance[2] is None:
                    alert['backtest_type'] = '24h'
                    alerts_to_backtest.append(alert)
        
        return alerts_to_backtest
    
    def _process_alert(self, alert: Dict[str, Any]) -> None:
        """处理单个告警的回测
        
        Args:
            alert: 告警信息字典
        """
        symbol = alert['symbol_id']
        alert_id = alert['alert_id']
        direction = alert['direction']
        initial_price = alert['price']
        backtest_type = alert['backtest_type']
        
        try:
            # 获取当前价格
            self.logger.info(f"[{symbol}] 获取当前价格中...")
            current_price = self._get_current_price(symbol)
            
            if not current_price:
                self.logger.error(f"[{symbol}] 获取当前价格失败")
                return
            
            # 准备价格数据
            price_data = {
                'initial_price': initial_price,
                'direction': direction
            }
            
            # 根据回测类型设置不同时间点的价格
            if backtest_type == '1h':
                price_data['price_1h'] = current_price
            elif backtest_type == '4h':
                price_data['price_4h'] = current_price
            elif backtest_type == '24h':
                price_data['price_24h'] = current_price
            
            # 记录回测结果
            self.db.record_alert_performance(alert_id, price_data)
            
            # 计算价格变化百分比
            price_change = ((current_price / initial_price) - 1) * 100
            price_change_str = f"{price_change:.2f}%"
            
            # 计算如果跟随信号的收益率
            if direction == "多":
                profit = price_change
            else:  # 空
                profit = -price_change
            profit_str = f"{profit:.2f}%"
            
            self.logger.info(f"[{symbol}] {backtest_type}回测完成: 初始价格={initial_price:.4f}, 当前价格={current_price:.4f}, 变化={price_change_str}, 收益={profit_str}")
            
        except Exception as e:
            self.logger.error(f"[{symbol}] 回测处理失败: {e}")
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """获取当前价格
        
        Args:
            symbol: 交易对符号
            
        Returns:
            当前价格，如果获取失败则返回None
        """
        try:
            # 使用DataFetcher获取当前价格
            klines = self.data_fetcher.get_klines(symbol, "5m", limit=1)
            if klines and len(klines) > 0:
                return float(klines[0][4])  # 收盘价
            return None
        except Exception as e:
            self.logger.error(f"[{symbol}] 获取当前价格失败: {e}")
            return None


def run_backtest_task(db: Database) -> None:
    """运行回测任务的入口函数
    
    Args:
        db: 数据库实例
    """
    task = BacktestTask(db)
    task.run()


if __name__ == "__main__":
    # 用于直接运行此脚本进行测试
    from utils.database import Database
    db = Database(":memory:")
    run_backtest_task(db)