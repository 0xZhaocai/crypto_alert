import os
import configparser
from typing import Dict, Any, List, Tuple

class ConfigLoader:
    """配置加载器，用于读取INI格式的配置文件"""
    
    def __init__(self, config_dir: str):
        """初始化配置加载器
        
        Args:
            config_dir: 配置文件目录路径
        """
        self.config_dir = config_dir
        self.alert_config = {}
        self.symbols = {}
        self.templates = {}
        
    def load_all_configs(self) -> None:
        """加载所有配置文件"""
        self.load_alert_config()
        self.load_symbols()
        self.load_templates()
        
    def load_alert_config(self) -> Dict[str, Any]:
        """加载告警配置
        
        Returns:
            包含告警配置的字典
        """
        config = configparser.ConfigParser()
        config_path = os.path.join(self.config_dir, 'alert_config.ini')
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
            
        config.read(config_path, encoding='utf-8')
        
        # 加载常规配置
        self.alert_config['feishu_webhook'] = config.get('general', 'feishu_webhook')
        self.alert_config['cooldown_minutes'] = config.getint('general', 'cooldown_minutes')
        self.alert_config['signal_threshold'] = config.getint('general', 'signal_threshold')
        
        # 加载条件控制配置
        if 'conditions' in config:
            self.alert_config['conditions'] = {
                'enable_rsi_check': config.getboolean('conditions', 'enable_rsi_check', fallback=True),
                'enable_price_ema_check': config.getboolean('conditions', 'enable_price_ema_check', fallback=True),
                'enable_atr_check': config.getboolean('conditions', 'enable_atr_check', fallback=True),
                'enable_volume_check': config.getboolean('conditions', 'enable_volume_check', fallback=True),
                'enable_zigzag_check': config.getboolean('conditions', 'enable_zigzag_check', fallback=False),
                'enable_price_change_check': config.getboolean('conditions', 'enable_price_change_check', fallback=True),
                'enable_signal_score_change_check': config.getboolean('conditions', 'enable_signal_score_change_check', fallback=True),
                'enable_rsi_change_check': config.getboolean('conditions', 'enable_rsi_change_check', fallback=True)
            }
        else:
            # 如果没有条件控制部分，默认全部启用
            self.alert_config['conditions'] = {
                'enable_rsi_check': True,
                'enable_price_ema_check': True,
                'enable_atr_check': True,
                'enable_volume_check': True,
                'enable_zigzag_check': False,
                'enable_price_change_check': True,
                'enable_signal_score_change_check': True,
                'enable_rsi_change_check': True
            }
        
        # 加载指标配置
        self.alert_config['indicators'] = {}
        self.alert_config['indicators']['rsi_min'] = config.getint('indicators', 'rsi_min')
        self.alert_config['indicators']['rsi_max'] = config.getint('indicators', 'rsi_max')
        self.alert_config['indicators']['price_ema_gap_ratio'] = config.getfloat('indicators', 'price_ema_gap_ratio')
        self.alert_config['indicators']['atr_ratio'] = config.getfloat('indicators', 'atr_ratio')
        self.alert_config['indicators']['volume_ratio'] = config.getfloat('indicators', 'volume_ratio')
        
        # 加载ZigZag指标配置
        self.alert_config['indicators']['zigzag_deviation'] = config.getfloat('indicators', 'zigzag_deviation', fallback=5.0)
        self.alert_config['indicators']['zigzag_depth'] = config.getint('indicators', 'zigzag_depth', fallback=10)
        
        # 为了向后兼容，保留原来的配置结构
        self.alert_config['rsi_range'] = {
            'min': self.alert_config['indicators']['rsi_min'],
            'max': self.alert_config['indicators']['rsi_max']
        }
        self.alert_config['price_ema_gap_ratio'] = self.alert_config['indicators']['price_ema_gap_ratio']
        self.alert_config['atr_ratio'] = self.alert_config['indicators']['atr_ratio']
        self.alert_config['volume_ratio'] = self.alert_config['indicators']['volume_ratio']
        self.alert_config['zigzag_deviation'] = self.alert_config['indicators']['zigzag_deviation']
        self.alert_config['zigzag_depth'] = self.alert_config['indicators']['zigzag_depth']
        
        # 加载阈值配置
        self.alert_config['price_change_threshold'] = config.getfloat('thresholds', 'price_change_threshold')
        self.alert_config['signal_score_change_threshold'] = config.getint('thresholds', 'signal_score_change_threshold')
        self.alert_config['rsi_change_threshold'] = config.getint('thresholds', 'rsi_change_threshold')
        
        # 加载数据库配置
        self.alert_config['db_path'] = os.path.abspath(os.path.join(
            self.config_dir, '..', config.get('database', 'db_path')))
        
        # 加载日志配置
        self.alert_config['log_path'] = os.path.abspath(os.path.join(
            self.config_dir, '..', config.get('logging', 'log_path')))
        self.alert_config['log_level'] = config.get('logging', 'log_level')
        
        return self.alert_config
    
    def load_symbols(self) -> Dict[str, str]:
        """加载交易对符号配置
        
        Returns:
            包含交易对符号和显示名称的字典
        """
        config = configparser.ConfigParser()
        config_path = os.path.join(self.config_dir, 'symbols.ini')
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"符号配置文件不存在: {config_path}")
            
        config.read(config_path, encoding='utf-8')
        
        # 加载交易对符号
        if 'symbols' in config:
            for symbol_id, display_name in config['symbols'].items():
                self.symbols[symbol_id] = display_name
        
        return self.symbols
    
    def load_templates(self) -> Dict[str, str]:
        """加载消息模板配置
        
        注意：此方法现在返回一个空字典，因为模板已经移动到templates.py模块中
        保留此方法是为了向后兼容
        
        Returns:
            空字典，因为模板已经移动到templates.py模块中
        """
        # 不再从templates.ini加载模板，而是使用templates.py中的函数
        # 返回空字典，因为模板已经移动到templates.py模块中
        return self.templates
    
    def get_symbols_list(self) -> List[Dict[str, str]]:
        """获取交易对列表，格式与原始代码兼容
        
        Returns:
            包含交易对信息的列表，每个元素是包含symbol和name的字典
        """
        return [{'symbol': symbol, 'name': name} for symbol, name in self.symbols.items()]
    
    def get_alert_config(self) -> Dict[str, Any]:
        """获取告警配置
        
        Returns:
            包含告警配置的字典
        """
        return self.alert_config
    
    def get_template(self, template_name: str) -> str:
        """获取指定名称的消息模板
        
        Args:
            template_name: 模板名称
            
        Returns:
            模板内容字符串
        """
        if template_name not in self.templates:
            raise ValueError(f"模板不存在: {template_name}")
        return self.templates[template_name]


# 便捷函数，用于加载配置
def load_config() -> Dict[str, Any]:
    """加载配置并返回配置字典
    
    Returns:
        包含所有配置的字典
    """
    # 获取配置目录路径
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_dir = os.path.join(base_dir, 'config')
    
    # 创建配置加载器
    config_loader = ConfigLoader(config_dir)
    
    # 加载配置
    config_loader.load_all_configs()
    
    # 获取告警配置
    config = config_loader.get_alert_config()
    
    # 添加额外的配置项
    config['symbols'] = config_loader.get_symbols_list()
    config['templates_path'] = os.path.join(base_dir, 'notifiers', 'templates.py')
    config['database_path'] = config['db_path']  # 兼容性别名
    
    return config