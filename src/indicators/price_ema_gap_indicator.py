from typing import List, Dict, Any
from src.indicators.base_indicator import BaseIndicator
from src.indicators.ema_indicator import EMAIndicator

class PriceEmaGapIndicator(BaseIndicator):
    """价格与EMA偏离比例指标实现类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化价格与EMA偏离比例指标
        
        Args:
            config: 配置字典，包含指标参数
        """
        super().__init__(config)
        # 从配置中读取EMA周期，如果没有则使用默认值
        self.ema_period = self.get_config_value('ema_period', 21)
        # 创建EMA指标实例用于计算
        self.ema_indicator = EMAIndicator(config)
    
    @property
    def name(self) -> str:
        """返回指标名称
        
        Returns:
            指标名称
        """
        return "price_ema_gap"
    
    def calculate(self, klines: List[List[float]], **kwargs) -> Dict[str, Any]:
        """计算价格与EMA偏离比例指标
        
        Args:
            klines: K线数据列表
            **kwargs: 其他参数，可以包含:
                - ema_period: EMA周期，覆盖默认值
                
        Returns:
            包含价格与EMA偏离比例指标计算结果的字典
        """
        if not self.validate_klines(klines, self.ema_period):
            return {"price_ema_gap_ratio": 0.0}  # 数据不足时返回默认值
        
        # 可以从kwargs中获取自定义周期
        ema_period = kwargs.get('ema_period', self.ema_period)
        
        # 使用EMA指标计算EMA值
        ema_result = self.ema_indicator.calculate(klines, period=ema_period)
        
        # 提取收盘价
        prices = self.extract_close_prices(klines)
        current_price = prices[-1] if prices else 0.0
        
        # 获取EMA值
        ema_value = ema_result.get("ema", 0.0)
        
        # 计算价格与EMA的偏离比例
        gap_ratio = abs(current_price - ema_value) / ema_value if ema_value > 0 else 0.0
        
        # 确定偏离区域
        deviation = "normal"
        if gap_ratio >= 0.05:  # 5%以上偏离
            deviation = "high"
        elif gap_ratio <= 0.01:  # 1%以下偏离
            deviation = "low"
        
        # 确定价格相对于EMA的位置
        position = "at"
        if current_price > ema_value:
            position = "above"
        elif current_price < ema_value:
            position = "below"
        
        return {
            "price_ema_gap_ratio": gap_ratio,
            "deviation": deviation,
            "position": position
        }