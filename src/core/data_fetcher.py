import time
import random
import requests
from typing import List, Dict, Any, Optional

from src.utils.logger import get_logger

class DataFetcher:
    """数据获取类，用于从交易所API获取K线数据"""
    
    def __init__(self, base_url: str = "https://api.binance.com/api/v3/klines"):
        """初始化数据获取器
        
        Args:
            base_url: 币安API的基础URL
        """
        self.base_url = base_url
        self.logger = get_logger()
    
    def get_klines(self, symbol: str, interval: str, limit: int = 50, max_retries: int = 3) -> List[List[Any]]:
        """从币安API获取K线数据，包含重试机制
        
        Args:
            symbol: 交易对符号
            interval: K线间隔，如1m, 5m, 15m, 1h等
            limit: 返回的K线数量
            max_retries: 最大重试次数
            
        Returns:
            K线数据列表
            
        Raises:
            Exception: 如果在最大重试次数后仍然失败
        """
        url = f"{self.base_url}?symbol={symbol.upper()}&interval={interval}&limit={limit}"
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = 1 + random.random()
                    self.logger.info(f"[{symbol}] 第{attempt+1}次尝试获取数据，等待{delay:.2f}秒...")
                    time.sleep(delay)
                
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                self.logger.error(f"[{symbol}] 请求异常 (第{attempt+1}次): {e}")
                if attempt == max_retries - 1:
                    raise
                    
            except ValueError as e:
                self.logger.error(f"[{symbol}] JSON解析错误 (第{attempt+1}次): {e}")
                if attempt == max_retries - 1:
                    raise
    
    def get_current_metrics(self, symbol: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """获取并计算一个代币的所有当前技术指标
        
        Args:
            symbol: 交易对符号
            config: 配置字典，包含指标参数
            
        Returns:
            包含各种技术指标的字典
            
        Raises:
            Exception: 如果获取或计算指标失败
        """
        from src.indicators import create_indicator, get_all_indicators
        
        try:
            # 获取K线数据
            klines_5m = self.get_klines(symbol, "5m")
            klines_15m = self.get_klines(symbol, "15m")
            klines_1h = self.get_klines(symbol, "1h")

            if len(klines_5m) < 21 or len(klines_15m) < 21 or len(klines_1h) < 21:
                raise Exception(f"K线数据不足")

            # 提取当前价格
            price = float(klines_5m[-1][4])
            
            # 初始化结果字典
            result = {"price": price}
            
            # 创建并计算EMA指标
            ema_indicator = create_indicator("ema", config)
            ema_5m_result = ema_indicator.calculate(klines_5m)
            ema_15m_result = ema_indicator.calculate(klines_15m)
            ema_1h_result = ema_indicator.calculate(klines_1h)
            result["ema21_5m"] = ema_5m_result["ema"]
            result["ema21_15m"] = ema_15m_result["ema"]
            result["ema21_1h"] = ema_1h_result["ema"]
            
            # 创建并计算RSI指标
            rsi_indicator = create_indicator("rsi", config)
            rsi_result = rsi_indicator.calculate(klines_5m)
            result["rsi_5m"] = rsi_result["rsi"]
            
            # 创建并计算ATR指标
            atr_indicator = create_indicator("atr", config)
            atr_result = atr_indicator.calculate(klines_5m)
            result["atr_ratio"] = atr_result["atr_ratio"]
            
            # 创建并计算成交量指标
            volume_indicator = create_indicator("volume", config)
            volume_result = volume_indicator.calculate(klines_5m)
            result["volume_ratio"] = volume_result["volume_ratio"]
            
            # 创建并计算价格与EMA偏离比例指标
            price_ema_gap_indicator = create_indicator("price_ema_gap", config)
            price_ema_gap_result = price_ema_gap_indicator.calculate(klines_15m)
            result["price_ema_gap_ratio"] = price_ema_gap_result["price_ema_gap_ratio"]
            
            # 创建并计算ZigZag指标
            zigzag_indicator = create_indicator("zigzag", config)
            zigzag_result = zigzag_indicator.calculate(klines_15m)
            result["zigzag"] = {
                "points": zigzag_result["zigzag_points"],
                "values": zigzag_result["zigzag_values"],
                "trend": zigzag_result["trend"],
                "pattern": zigzag_result["pattern"]
            }
            # 保持向后兼容
            result["zigzag_points"] = zigzag_result["zigzag_points"]
            result["zigzag_values"] = zigzag_result["zigzag_values"]
            
            return result
            
        except Exception as e:
            # 将原始异常包装后重新抛出，以便上层捕获
            self.logger.error(f"计算{symbol}指标失败: {e}")
            raise Exception(f"计算{symbol}指标失败: {e}") from e