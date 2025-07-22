from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseIndicator(ABC):
    """指标基类，所有技术指标都应继承此类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化指标
        
        Args:
            config: 配置字典，包含指标参数
        """
        self.config = config or {}
    
    @property
    @abstractmethod
    def name(self) -> str:
        """返回指标名称
        
        Returns:
            指标名称
        """
        pass
    
    @abstractmethod
    def calculate(self, klines: List[List[float]], **kwargs) -> Dict[str, Any]:
        """计算指标值
        
        Args:
            klines: K线数据列表
            **kwargs: 其他参数
            
        Returns:
            包含指标计算结果的字典
        """
        pass
    
    def get_config_value(self, key: str, default_value: Any) -> Any:
        """从配置中获取值，如果不存在则返回默认值
        
        Args:
            key: 配置键
            default_value: 默认值
            
        Returns:
            配置值或默认值
        """
        return self.config.get(key, default_value)
    
    def validate_klines(self, klines: List[List[float]], min_length: int = 1) -> bool:
        """验证K线数据是否有效
        
        Args:
            klines: K线数据列表
            min_length: 最小所需长度
            
        Returns:
            K线数据是否有效
        """
        return isinstance(klines, list) and len(klines) >= min_length
    
    def extract_close_prices(self, klines: List[List[float]]) -> List[float]:
        """从K线数据中提取收盘价
        
        Args:
            klines: K线数据列表
            
        Returns:
            收盘价列表
        """
        return [float(x[4]) for x in klines] if self.validate_klines(klines) else []
    
    def extract_volumes(self, klines: List[List[float]]) -> List[float]:
        """从K线数据中提取成交量
        
        Args:
            klines: K线数据列表
            
        Returns:
            成交量列表
        """
        return [float(x[5]) for x in klines] if self.validate_klines(klines) else []