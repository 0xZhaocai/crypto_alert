from typing import List, Dict, Any
from indicators.base_indicator import BaseIndicator

class VolumeIndicator(BaseIndicator):
    """成交量指标实现类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化成交量指标
        
        Args:
            config: 配置字典，包含指标参数
        """
        super().__init__(config)
        # 从配置中读取成交量历史周期，如果没有则使用默认值
        self.history_period = self.get_config_value('volume_history_period', 20)
    
    @property
    def name(self) -> str:
        """返回指标名称
        
        Returns:
            指标名称
        """
        return "volume"
    
    def calculate(self, klines: List[List[float]], **kwargs) -> Dict[str, Any]:
        """计算成交量指标
        
        Args:
            klines: K线数据列表
            **kwargs: 其他参数，可以包含:
                - history_period: 成交量历史周期，覆盖默认值
                
        Returns:
            包含成交量指标计算结果的字典
        """
        if not self.validate_klines(klines, self.history_period + 1):
            return {"volume": 0.0, "volume_ratio": 1.0}  # 数据不足时返回默认值
        
        # 可以从kwargs中获取自定义周期
        history_period = kwargs.get('history_period', self.history_period)
        
        # 提取成交量数据
        volumes = self.extract_volumes(klines)
        
        # 获取当前成交量
        current_volume = volumes[-1] if volumes else 0.0
        
        # 计算历史平均成交量
        if len(volumes) > history_period:
            historical_volumes = volumes[-history_period-1:-1]
            avg_historical_volume = sum(historical_volumes) / len(historical_volumes) if historical_volumes else 0.0
            volume_ratio = current_volume / avg_historical_volume if avg_historical_volume > 0 else 1.0
        else:
            volume_ratio = 1.0
        
        # 确定成交量区域
        volume_zone = "normal"
        if volume_ratio >= 2.0:
            volume_zone = "high"
        elif volume_ratio <= 0.5:
            volume_zone = "low"
        
        return {
            "volume": current_volume,
            "volume_ratio": volume_ratio,
            "volume_zone": volume_zone
        }
    
    def _calculate_volume_ratio(self, volumes: List[float], history_period: int = 20) -> float:
        """计算成交量比率
        
        Args:
            volumes: 成交量数据列表
            history_period: 历史周期
            
        Returns:
            成交量比率
        """
        if len(volumes) <= history_period:
            return 1.0  # 数据不足时返回1.0
        
        current_volume = volumes[-1]
        historical_volumes = volumes[-history_period-1:-1]
        avg_historical_volume = sum(historical_volumes) / len(historical_volumes) if historical_volumes else 0.0
        
        return current_volume / avg_historical_volume if avg_historical_volume > 0 else 1.0