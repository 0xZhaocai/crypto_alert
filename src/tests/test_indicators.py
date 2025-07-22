import unittest
import sys
import os
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from indicators import create_indicator, get_indicator_class, get_all_indicators, load_indicators
from indicators.base_indicator import BaseIndicator
from indicators.zigzag_indicator import ZigZagIndicator
from indicators.rsi_indicator import RSIIndicator
from indicators.ema_indicator import EMAIndicator
from indicators.atr_indicator import ATRIndicator
from indicators.volume_indicator import VolumeIndicator
from indicators.price_ema_gap_indicator import PriceEmaGapIndicator

class TestIndicators(unittest.TestCase):
    """测试指标插件系统"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 确保指标已加载
        load_indicators()
        
        # 创建测试用的K线数据
        self.klines = [
            [1625097600000, "35000", "36000", "34500", "35500", "100", 1625097899999, "3550000", 100, "50", "1750000", "0"],
            [1625097900000, "35500", "36500", "35000", "36000", "120", 1625098199999, "4320000", 120, "60", "2160000", "0"],
            [1625098200000, "36000", "37000", "35800", "36500", "150", 1625098499999, "5475000", 150, "75", "2737500", "0"],
            [1625098500000, "36500", "37500", "36200", "37000", "180", 1625098799999, "6660000", 180, "90", "3330000", "0"],
            [1625098800000, "37000", "38000", "36800", "37500", "200", 1625099099999, "7500000", 200, "100", "3750000", "0"],
            [1625099100000, "37500", "38500", "37200", "38000", "220", 1625099399999, "8360000", 220, "110", "4180000", "0"],
            [1625099400000, "38000", "39000", "37800", "38500", "240", 1625099699999, "9240000", 240, "120", "4620000", "0"],
            [1625099700000, "38500", "39500", "38200", "39000", "260", 1625099999999, "10140000", 260, "130", "5070000", "0"],
            [1625100000000, "39000", "40000", "38800", "39500", "280", 1625100299999, "11060000", 280, "140", "5530000", "0"],
            [1625100300000, "39500", "40500", "39200", "40000", "300", 1625100599999, "12000000", 300, "150", "6000000", "0"],
            [1625100600000, "40000", "41000", "39800", "40500", "320", 1625100899999, "12960000", 320, "160", "6480000", "0"],
            [1625100900000, "40500", "41500", "40200", "41000", "340", 1625101199999, "13940000", 340, "170", "6970000", "0"],
            [1625101200000, "41000", "42000", "40800", "41500", "360", 1625101499999, "14940000", 360, "180", "7470000", "0"],
            [1625101500000, "41500", "42500", "41200", "42000", "380", 1625101799999, "15960000", 380, "190", "7980000", "0"],
            [1625101800000, "42000", "43000", "41800", "42500", "400", 1625102099999, "17000000", 400, "200", "8500000", "0"],
            [1625102100000, "42500", "43500", "42200", "43000", "420", 1625102399999, "18060000", 420, "210", "9030000", "0"],
            [1625102400000, "43000", "44000", "42800", "43500", "440", 1625102699999, "19140000", 440, "220", "9570000", "0"],
            [1625102700000, "43500", "44500", "43200", "44000", "460", 1625102999999, "20240000", 460, "230", "10120000", "0"],
            [1625103000000, "44000", "45000", "43800", "44500", "480", 1625103299999, "21360000", 480, "240", "10680000", "0"],
            [1625103300000, "44500", "45500", "44200", "45000", "500", 1625103599999, "22500000", 500, "250", "11250000", "0"],
            [1625103600000, "45000", "46000", "44800", "45500", "520", 1625103899999, "23660000", 520, "260", "11830000", "0"],
            [1625103900000, "45500", "46500", "45200", "46000", "540", 1625104199999, "24840000", 540, "270", "12420000", "0"],
            [1625104200000, "46000", "47000", "45800", "46500", "560", 1625104499999, "26040000", 560, "280", "13020000", "0"],
            [1625104500000, "46500", "47500", "46200", "47000", "580", 1625104799999, "27260000", 580, "290", "13630000", "0"],
            [1625104800000, "47000", "48000", "46800", "47500", "600", 1625105099999, "28500000", 600, "300", "14250000", "0"],
            [1625105100000, "47500", "48500", "47200", "48000", "620", 1625105399999, "29760000", 620, "310", "14880000", "0"],
            [1625105400000, "48000", "49000", "47800", "48500", "640", 1625105699999, "31040000", 640, "320", "15520000", "0"],
            [1625105700000, "48500", "49500", "48200", "49000", "660", 1625105999999, "32340000", 660, "330", "16170000", "0"],
            [1625106000000, "49000", "50000", "48800", "49500", "680", 1625106299999, "33660000", 680, "340", "16830000", "0"],
            [1625106300000, "49500", "50500", "49200", "50000", "700", 1625106599999, "35000000", 700, "350", "17500000", "0"],
        ]
        
        # 创建测试用的配置
        self.config = {
            'indicators': {
                'rsi_min': '30',
                'rsi_max': '70',
                'rsi_period': '14',
                'ema_period': '21',
                'atr_period': '14',
                'atr_history_period': '100',
                'volume_history_period': '20',
                'price_ema_gap_ratio': '0.003',
                'zigzag_deviation': '5.0'
            }
        }
    
    def test_indicator_registration(self):
        """测试指标注册机制"""
        # 获取所有注册的指标
        indicators = get_all_indicators()
        
        # 验证所有指标都已注册
        self.assertIn('zigzag', indicators)
        self.assertIn('rsi', indicators)
        self.assertIn('ema', indicators)
        self.assertIn('atr', indicators)
        self.assertIn('volume', indicators)
        self.assertIn('price_ema_gap', indicators)
        
        # 验证可以获取指标类
        zigzag_class = get_indicator_class('zigzag')
        self.assertEqual(zigzag_class, ZigZagIndicator)
        
        rsi_class = get_indicator_class('rsi')
        self.assertEqual(rsi_class, RSIIndicator)
    
    def test_create_indicator(self):
        """测试创建指标实例"""
        # 创建ZigZag指标实例
        zigzag = create_indicator('zigzag', self.config)
        self.assertIsInstance(zigzag, ZigZagIndicator)
        self.assertEqual(zigzag.name, 'zigzag')
        self.assertEqual(zigzag.deviation_pct, 5.0)
        
        # 创建RSI指标实例
        rsi = create_indicator('rsi', self.config)
        self.assertIsInstance(rsi, RSIIndicator)
        self.assertEqual(rsi.name, 'rsi')
        self.assertEqual(rsi.period, 14)
    
    def test_zigzag_indicator(self):
        """测试ZigZag指标"""
        zigzag = create_indicator('zigzag', self.config)
        result = zigzag.calculate(self.klines)
        
        # 验证结果包含必要的键
        self.assertIn('zigzag_points', result)
        self.assertIn('zigzag_values', result)
        self.assertIn('trend', result)
        
        # 验证结果类型
        self.assertIsInstance(result['zigzag_points'], list)
        self.assertIsInstance(result['zigzag_values'], list)
        self.assertIsInstance(result['trend'], str)
    
    def test_rsi_indicator(self):
        """测试RSI指标"""
        rsi = create_indicator('rsi', self.config)
        result = rsi.calculate(self.klines)
        
        # 验证结果包含必要的键
        self.assertIn('rsi', result)
        self.assertIn('zone', result)
        
        # 验证结果类型
        self.assertIsInstance(result['rsi'], float)
        self.assertIsInstance(result['zone'], str)
    
    def test_ema_indicator(self):
        """测试EMA指标"""
        ema = create_indicator('ema', self.config)
        result = ema.calculate(self.klines)
        
        # 验证结果包含必要的键
        self.assertIn('ema', result)
        self.assertIn('price_position', result)
        self.assertIn('price_ema_gap_ratio', result)
        
        # 验证结果类型
        self.assertIsInstance(result['ema'], float)
        self.assertIsInstance(result['price_position'], str)
        self.assertIsInstance(result['price_ema_gap_ratio'], float)
    
    def test_atr_indicator(self):
        """测试ATR指标"""
        atr = create_indicator('atr', self.config)
        result = atr.calculate(self.klines)
        
        # 验证结果包含必要的键
        self.assertIn('atr', result)
        self.assertIn('atr_ratio', result)
        self.assertIn('volatility', result)
        
        # 验证结果类型
        self.assertIsInstance(result['atr'], float)
        self.assertIsInstance(result['atr_ratio'], float)
        self.assertIsInstance(result['volatility'], str)
    
    def test_volume_indicator(self):
        """测试成交量指标"""
        volume = create_indicator('volume', self.config)
        result = volume.calculate(self.klines)
        
        # 验证结果包含必要的键
        self.assertIn('volume', result)
        self.assertIn('volume_ratio', result)
        self.assertIn('volume_zone', result)
        
        # 验证结果类型
        self.assertIsInstance(result['volume'], float)
        self.assertIsInstance(result['volume_ratio'], float)
        self.assertIsInstance(result['volume_zone'], str)
    
    def test_price_ema_gap_indicator(self):
        """测试价格与EMA偏离比例指标"""
        price_ema_gap = create_indicator('price_ema_gap', self.config)
        result = price_ema_gap.calculate(self.klines)
        
        # 验证结果包含必要的键
        self.assertIn('price_ema_gap_ratio', result)
        self.assertIn('deviation', result)
        self.assertIn('position', result)
        
        # 验证结果类型
        self.assertIsInstance(result['price_ema_gap_ratio'], float)
        self.assertIsInstance(result['deviation'], str)
        self.assertIsInstance(result['position'], str)

if __name__ == '__main__':
    unittest.main()