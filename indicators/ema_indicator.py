from typing import List, Dict, Any
from indicators.base_indicator import BaseIndicator

class EMAIndicator(BaseIndicator):
    """EMA指标实现类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化EMA指标
        
        Args:
            config: 配置字典，包含指标参数
        """
        super().__init__(config)
        # 从配置中读取EMA周期，如果没有则使用默认值
        self.period = self.get_config_value('ema_period', 21)
    
    @property
    def name(self) -> str:
        """返回指标名称
        
        Returns:
            指标名称
        """
        return "ema"
    
    def calculate(self, klines: List[List[float]], **kwargs) -> Dict[str, Any]:
        """计算EMA指标
        
        Args:
            klines: K线数据列表
            **kwargs: 其他参数，可以包含:
                - period: EMA周期，覆盖默认值
                
        Returns:
            包含EMA指标计算结果的字典
        """
        if not self.validate_klines(klines, self.period):
            return {"ema": 0.0}  # 数据不足时返回0
        
        # 可以从kwargs中获取自定义周期
        period = kwargs.get('period', self.period)
        
        # 提取收盘价
        prices = self.extract_close_prices(klines)
        
        # 计算EMA
        ema_value = self._calculate_ema(prices, period)
        
        # 计算价格与EMA的关系
        current_price = prices[-1] if prices else 0
        price_position = "above" if current_price > ema_value else "below" if current_price < ema_value else "at"
        
        # 计算价格与EMA的偏离比例
        gap_ratio = abs(current_price - ema_value) / ema_value if ema_value > 0 else 0.0
        
        return {
            "ema": ema_value,
            "price_position": price_position,
            "price_ema_gap_ratio": gap_ratio
        }
    
    def _calculate_ema(self, data: List[float], period: int = 21) -> float:
        """计算指数移动平均线 (EMA)
        
        Args:
            data: 价格数据列表
            period: EMA周期
            
        Returns:
            EMA值
        """
        if len(data) < period:
            return 0.0  # 数据不足时返回0
            
        ema_values = []
        k = 2 / (period + 1)
        
        for i, price in enumerate(data):
            if len(ema_values) == 0:
                # 使用简单移动平均作为第一个EMA值
                sma = sum(data[:period]) / period
                ema_values.append(sma)
            else:
                ema_values.append(price * k + ema_values[-1] * (1 - k))
        
        return ema_values[-1]