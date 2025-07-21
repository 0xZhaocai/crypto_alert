from typing import List, Dict, Any
from indicators.base_indicator import BaseIndicator

class RSIIndicator(BaseIndicator):
    """RSI指标实现类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化RSI指标
        
        Args:
            config: 配置字典，包含指标参数
        """
        super().__init__(config)
        # 从配置中读取RSI周期，如果没有则使用默认值
        self.period = self.get_config_value('rsi_period', 14)
    
    @property
    def name(self) -> str:
        """返回指标名称
        
        Returns:
            指标名称
        """
        return "rsi"
    
    def calculate(self, klines: List[List[float]], **kwargs) -> Dict[str, Any]:
        """计算RSI指标
        
        Args:
            klines: K线数据列表
            **kwargs: 其他参数，可以包含:
                - period: RSI周期，覆盖默认值
                
        Returns:
            包含RSI指标计算结果的字典
        """
        if not self.validate_klines(klines, self.period + 1):
            return {"rsi": 50.0}  # 数据不足时返回中性值
        
        # 可以从kwargs中获取自定义周期
        period = kwargs.get('period', self.period)
        
        # 提取收盘价
        prices = self.extract_close_prices(klines)
        
        # 计算RSI
        rsi_value = self._calculate_rsi(prices, period)
        
        # 确定RSI区域
        zone = "neutral"
        if rsi_value >= 70:
            zone = "overbought"
        elif rsi_value <= 30:
            zone = "oversold"
        
        return {
            "rsi": rsi_value,
            "zone": zone
        }
    
    def _calculate_rsi(self, data: List[float], period: int = 14) -> float:
        """计算相对强弱指数 (RSI)
        
        Args:
            data: 价格数据列表
            period: RSI周期
            
        Returns:
            RSI值
        """
        if len(data) <= period:
            return 50.0  # 数据不足时返回中性值
            
        deltas = [data[i] - data[i - 1] for i in range(1, len(data))]
        gains = [x if x > 0 else 0 for x in deltas]
        losses = [-x if x < 0 else 0 for x in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))