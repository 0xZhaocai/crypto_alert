import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

class Logger:
    """日志工具类，用于统一的日志记录"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式，确保只有一个Logger实例"""
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, log_path: str, log_level: str = 'INFO'):
        """初始化日志工具
        
        Args:
            log_path: 日志文件路径
            log_level: 日志级别，默认为INFO
        """
        if self._initialized:
            return
            
        self._initialized = True
        self.log_path = log_path
        self.log_level = self._get_log_level(log_level)
        
        # 确保日志目录存在
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        # 配置日志记录器
        self.logger = logging.getLogger('crypto_alert')
        self.logger.setLevel(self.log_level)
        
        # 清除已有的处理器
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # 添加文件处理器
        file_handler = RotatingFileHandler(
            self.log_path, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
        file_handler.setLevel(self.log_level)
        file_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
    
    def _get_log_level(self, level_str: str) -> int:
        """将字符串日志级别转换为logging模块的级别常量
        
        Args:
            level_str: 日志级别字符串
            
        Returns:
            logging模块的日志级别常量
        """
        levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return levels.get(level_str.upper(), logging.INFO)
    
    def get_logger(self) -> logging.Logger:
        """获取日志记录器
        
        Returns:
            配置好的日志记录器
        """
        return self.logger

# 便捷函数，用于获取已配置的日志记录器
def get_logger(log_path: Optional[str] = None, log_level: Optional[str] = None) -> logging.Logger:
    """获取已配置的日志记录器
    
    Args:
        log_path: 日志文件路径，如果为None则使用已配置的路径
        log_level: 日志级别，如果为None则使用已配置的级别
        
    Returns:
        配置好的日志记录器
    """
    if Logger._instance is None and log_path is None:
        raise ValueError("首次调用必须提供log_path参数")
        
    if log_path is not None:
        logger_instance = Logger(log_path, log_level or 'INFO')
    else:
        logger_instance = Logger._instance
        
    return logger_instance.get_logger()

# 便捷函数，用于设置默认的日志记录器
def setup_logger(log_path: Optional[str] = None, log_level: str = 'INFO') -> logging.Logger:
    """设置默认的日志记录器
    
    Args:
        log_path: 日志文件路径，如果为None则使用默认路径
        log_level: 日志级别，默认为INFO
        
    Returns:
        配置好的日志记录器
    """
    if log_path is None:
        # 使用默认日志路径
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_dir = os.path.join(base_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, 'crypto_alert.log')
    
    return get_logger(log_path, log_level)