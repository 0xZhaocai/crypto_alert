from typing import List, Dict, Any
from indicators.base_indicator import BaseIndicator

class ATRIndicator(BaseIndicator):
    """ATR指标实现类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化ATR指标
        
        Args:
            config: 配置字典，包含指标参数
        """
        super().__init__(config)
        # 从配置中读取ATR周期，如果没有则使用默认值
        self.period = self.get_config_value('atr_period', 14)
        # 从配置中读取ATR历史周期，如果没有则使用默认值
        self.history_period = self.get_config_value('atr_history_period', 100)
    
    @property
    def name(self) -> str:
        """返回指标名称
        
        Returns:
            指标名称
        """
        return "atr"
    
    def calculate(self, klines: List[List[float]], **kwargs) -> Dict[str, Any]:
        """计算ATR指标
        
        Args:
            klines: K线数据列表
            **kwargs: 其他参数，可以包含:
                - period: ATR周期，覆盖默认值
                - history_period: ATR历史周期，覆盖默认值
                
        Returns:
            包含ATR指标计算结果的字典
        """
        # 确保有足够的数据计算ATR和历史ATR
        min_required = max(self.period, self.history_period) + 1
        if not self.validate_klines(klines, min_required):
            return {"atr": 0.0, "atr_ratio": 1.0}  # 数据不足时返回默认值
        
        # 可以从kwargs中获取自定义周期
        period = kwargs.get('period', self.period)
        history_period = kwargs.get('history_period', self.history_period)
        
        # 计算ATR
        atr_value = self._calculate_atr(klines, period)
        
        # 计算历史ATR
        if len(klines) > history_period + period:
            historical_klines = klines[-(history_period + period):-period]
            historical_atr = self._calculate_atr(historical_klines, period)
            atr_ratio = atr_value / historical_atr if historical_atr > 0 else 1.0
        else:
            atr_ratio = 1.0
        
        # 确定波动性区域
        volatility = "normal"
        if atr_ratio >= 1.5:
            volatility = "high"
        elif atr_ratio <= 0.5:
            volatility = "low"
        
        return {
            "atr": atr_value,
            "atr_ratio": atr_ratio,
            "volatility": volatility
        }
    
    def _calculate_atr(self, klines: List[List[float]], period: int = 14) -> float:
        """计算平均真实波幅 (ATR)
        
        Args:
            klines: K线数据列表
            period: ATR周期
            
        Returns:
            ATR值
        """
        if len(klines) <= period:
            return 0.0  # 数据不足时返回0
        
        tr_values = []
        
        for i in range(1, len(klines)):
            high = float(klines[i][2])  # 当前K线的最高价
            low = float(klines[i][3])   # 当前K线的最低价
            prev_close = float(klines[i-1][4])  # 前一K线的收盘价
            
            # 计算真实波幅 (True Range)
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            tr_values.append(tr)
        
        # 计算ATR (使用简单移动平均)
        if len(tr_values) < period:
            return sum(tr_values) / len(tr_values) if tr_values else 0.0
        
        return sum(tr_values[-period:]) / period