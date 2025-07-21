from typing import Dict, Type, Any, List
import importlib
import inspect
import os
import sys
from pathlib import Path
from indicators.base_indicator import BaseIndicator

# 指标注册表
_INDICATORS: Dict[str, Type[BaseIndicator]] = {}

def register_indicator(indicator_class: Type[BaseIndicator]) -> Type[BaseIndicator]:
    """注册指标类
    
    Args:
        indicator_class: 要注册的指标类
        
    Returns:
        注册的指标类
    """
    # 创建临时实例以获取指标名称
    temp_instance = indicator_class({})
    indicator_name = temp_instance.name
    
    # 注册指标
    _INDICATORS[indicator_name] = indicator_class
    return indicator_class

def get_indicator_class(indicator_name: str) -> Type[BaseIndicator]:
    """获取指标类
    
    Args:
        indicator_name: 指标名称
        
    Returns:
        指标类
    """
    return _INDICATORS.get(indicator_name)

def get_all_indicators() -> Dict[str, Type[BaseIndicator]]:
    """获取所有注册的指标
    
    Returns:
        指标名称到指标类的映射字典
    """
    return _INDICATORS.copy()

def create_indicator(indicator_name: str, config: Dict[str, Any] = None) -> BaseIndicator:
    """创建指标实例
    
    Args:
        indicator_name: 指标名称
        config: 配置字典
        
    Returns:
        指标实例
    """
    indicator_class = get_indicator_class(indicator_name)
    if indicator_class is None:
        raise ValueError(f"未找到指标: {indicator_name}")
    
    return indicator_class(config)

def load_indicators() -> None:
    """加载所有指标模块"""
    # 获取当前目录
    current_dir = Path(__file__).parent
    
    # 遍历目录中的所有Python文件
    for file_path in current_dir.glob("*.py"):
        if file_path.name == "__init__.py" or file_path.name == "base_indicator.py":
            continue
        
        # 导入模块
        module_name = f"indicators.{file_path.stem}"
        try:
            module = importlib.import_module(module_name)
            
            # 查找模块中的指标类
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseIndicator) and 
                    obj != BaseIndicator):
                    # 注册指标类
                    register_indicator(obj)
        except Exception as e:
            print(f"加载指标模块 {module_name} 失败: {e}")

# 自动加载所有指标
load_indicators()