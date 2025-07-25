from typing import Dict, Any, Tuple, List

from src.utils.logger import get_logger

class SignalEvaluator:
    """信号评估类，用于评估交易信号"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化信号评估器
        
        Args:
            config: 配置字典，包含评估所需的各种阈值
        """
        self.config = config
        self.logger = get_logger()
        
        # 从配置中提取评估所需的阈值
        indicators_config = config.get('indicators', {})
        self.rsi_range = {
            'min': float(indicators_config.get('rsi_min', 40)),
            'max': float(indicators_config.get('rsi_max', 60))
        }
        self.price_ema_gap_ratio = float(indicators_config.get('price_ema_gap_ratio', 0.003))
        self.atr_ratio = float(indicators_config.get('atr_ratio', 1.1))
        self.volume_ratio = float(indicators_config.get('volume_ratio', 1.3))
        
        thresholds_config = config.get('thresholds', {})
        self.signal_threshold = int(config.get('signal_threshold', 3))  # 使用配置中的值，默认为3
        self.price_change_threshold = float(thresholds_config.get('price_change_threshold', 0.01))
        self.signal_score_change_threshold = int(thresholds_config.get('signal_score_change_threshold', 2))
        self.rsi_change_threshold = float(thresholds_config.get('rsi_change_threshold', 5.0))
        
        # 从配置中提取条件控制设置
        conditions = config.get('conditions', {})
        self.enable_rsi_check = self._parse_boolean_config(conditions.get('enable_rsi_check', True))
        self.enable_price_ema_check = self._parse_boolean_config(conditions.get('enable_price_ema_check', True))
        self.enable_atr_check = self._parse_boolean_config(conditions.get('enable_atr_check', False))
        self.enable_volume_check = self._parse_boolean_config(conditions.get('enable_volume_check', True))
        self.enable_zigzag_check = self._parse_boolean_config(conditions.get('enable_zigzag_check', False))
        
        # 从配置中提取阈值检查控制设置
        self.enable_price_change_check = self._parse_boolean_config(conditions.get('enable_price_change_check', True))
        self.enable_signal_score_change_check = self._parse_boolean_config(conditions.get('enable_signal_score_change_check', True))
        self.enable_rsi_change_check = self._parse_boolean_config(conditions.get('enable_rsi_change_check', True))
        
        # 从配置中提取各项指标的分数权重
        scores_config = config.get('scores', {})
        self.ema_15m_score = int(scores_config.get('ema_15m_score', 2))
        self.ema_1h_score = int(scores_config.get('ema_1h_score', 2))
        self.rsi_score = int(scores_config.get('rsi_score', 1))
        self.price_ema_gap_score = int(scores_config.get('price_ema_gap_score', 1))
        self.atr_score = int(scores_config.get('atr_score', 2))
        self.volume_score = int(scores_config.get('volume_score', 2))
        self.zigzag_score = int(scores_config.get('zigzag_score', 2))
        
        # 计算并记录理论最高分
        self.max_possible_score = self.calculate_max_possible_score()
        self.logger.info(f"当前配置下的理论最高分: {self.max_possible_score}分")
        self.logger.info(f"当前信号阈值: {self.signal_threshold}分 ({self.signal_threshold/self.max_possible_score*100:.1f}% of max score)")
    
    def _parse_boolean_config(self, value: Any) -> bool:
        """解析布尔值配置，处理不同类型的输入
        
        Args:
            value: 配置值，可能是布尔值、字符串或其他类型
            
        Returns:
            解析后的布尔值
        """
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            return value.lower() == 'true'
        else:
            # 对于其他类型，尝试转换为布尔值
            return bool(value)
    
    def calculate_max_possible_score(self) -> int:
        """计算当前配置下的理论最高分
        
        Returns:
            理论最高分
        """
        max_score = 0
        
        # EMA趋势评分（做多或做空只能选其一）
        max_score += self.ema_15m_score + self.ema_1h_score
        
        # RSI区间评分（如果启用）
        if self.enable_rsi_check:
            max_score += self.rsi_score
            
        # 价格贴近EMA评分（如果启用）
        if self.enable_price_ema_check:
            max_score += self.price_ema_gap_score
            
        # ATR放大评分（如果启用）
        if self.enable_atr_check:
            max_score += self.atr_score
            
        # 成交量放大评分（如果启用）
        if self.enable_volume_check:
            max_score += self.volume_score
            
        # ZigZag趋势评分（如果启用）
        if self.enable_zigzag_check:
            max_score += self.zigzag_score
            
        return max_score
    
    def evaluate_signals(self, metrics: Dict[str, Any]) -> Tuple[int, int, List[str], List[str]]:
        """根据各项指标为多空方向评分
        
        Args:
            metrics: 包含各种技术指标的字典
            
        Returns:
            多空方向的评分和详细信息的元组 (long_score, short_score, long_details, short_details)
        """
        long_score, short_score = 0, 0
        long_details, short_details = [], []

        # 做多信号评分
        # 价格与EMA21(15m)的关系
        if metrics["price"] > metrics["ema21_15m"]:
            long_score += self.ema_15m_score
            long_details.append(f"价格 > EMA21(15m): +{self.ema_15m_score}")
            
        # 价格与EMA21(1h)的关系
        if metrics["price"] > metrics["ema21_1h"]:
            long_score += self.ema_1h_score
            long_details.append(f"价格 > EMA21(1h): +{self.ema_1h_score}")
            
        # RSI在区间内检查
        if self.enable_rsi_check and self.rsi_range["min"] <= metrics["rsi_5m"] <= self.rsi_range["max"]:
            long_score += self.rsi_score
            long_details.append(f"RSI在区间内({metrics['rsi_5m']:.2f}): +{self.rsi_score}")
            
        # 价格贴近EMA检查
        if self.enable_price_ema_check and metrics["price_ema_gap_ratio"] < self.price_ema_gap_ratio:
            long_score += self.price_ema_gap_score
            long_details.append(f"价格贴近EMA({metrics['price_ema_gap_ratio']:.3%}): +{self.price_ema_gap_score}")
            
        # ATR放大检查
        if self.enable_atr_check and metrics["atr_ratio"] >= self.atr_ratio:
            long_score += self.atr_score
            long_details.append(f"ATR放大({metrics['atr_ratio']:.2f}x): +{self.atr_score}")
            
        # 成交量放大检查
        if self.enable_volume_check and metrics["volume_ratio"] >= self.volume_ratio:
            long_score += self.volume_score
            long_details.append(f"成交量放大({metrics['volume_ratio']:.2f}x): +{self.volume_score}")
            
        # ZigZag指标检查（做多）
        if self.enable_zigzag_check and "zigzag" in metrics:
            # 获取ZigZag趋势和形态
            zigzag_trend = metrics["zigzag"].get("trend", "neutral")
            zigzag_pattern = metrics["zigzag"].get("pattern", "")
            
            self.logger.debug(f"ZigZag做多信号评估 - 趋势: {zigzag_trend}, 形态: {zigzag_pattern}")
            
            # 如果是上升趋势或W底形态，加分
            # 确保M顶形态不会被错误地计入做多信号
            if (zigzag_trend == "up" and zigzag_pattern != "M顶") or zigzag_pattern == "W底":
                long_score += self.zigzag_score
                pattern_text = f"，形态：{zigzag_pattern}" if zigzag_pattern else ""
                long_details.append(f"ZigZag上升趋势{pattern_text}: +{self.zigzag_score}")

        # 做空信号评分
        # 价格与EMA21(15m)的关系
        if metrics["price"] < metrics["ema21_15m"]:
            short_score += self.ema_15m_score
            short_details.append(f"价格 < EMA21(15m): +{self.ema_15m_score}")
            
        # 价格与EMA21(1h)的关系
        if metrics["price"] < metrics["ema21_1h"]:
            short_score += self.ema_1h_score
            short_details.append(f"价格 < EMA21(1h): +{self.ema_1h_score}")
            
        # RSI在区间内检查
        if self.enable_rsi_check and self.rsi_range["min"] <= metrics["rsi_5m"] <= self.rsi_range["max"]:
            short_score += self.rsi_score
            short_details.append(f"RSI在区间内({metrics['rsi_5m']:.2f}): +{self.rsi_score}")
            
        # 价格贴近EMA检查
        if self.enable_price_ema_check and metrics["price_ema_gap_ratio"] < self.price_ema_gap_ratio:
            short_score += self.price_ema_gap_score
            short_details.append(f"价格贴近EMA({metrics['price_ema_gap_ratio']:.3%}): +{self.price_ema_gap_score}")
            
        # ATR放大检查
        if self.enable_atr_check and metrics["atr_ratio"] >= self.atr_ratio:
            short_score += self.atr_score
            short_details.append(f"ATR放大({metrics['atr_ratio']:.2f}x): +{self.atr_score}")
            
        # 成交量放大检查
        if self.enable_volume_check and metrics["volume_ratio"] >= self.volume_ratio:
            short_score += self.volume_score
            short_details.append(f"成交量放大({metrics['volume_ratio']:.2f}x): +{self.volume_score}")
            
        # ZigZag指标检查（做空）
        if self.enable_zigzag_check and "zigzag" in metrics:
            # 获取ZigZag趋势和形态
            zigzag_trend = metrics["zigzag"].get("trend", "neutral")
            zigzag_pattern = metrics["zigzag"].get("pattern", "")
            
            self.logger.debug(f"ZigZag做空信号评估 - 趋势: {zigzag_trend}, 形态: {zigzag_pattern}")
            
            # 如果是下降趋势或M顶形态，加分
            # 确保W底形态不会被错误地计入做空信号
            if (zigzag_trend == "down" and zigzag_pattern != "W底") or zigzag_pattern == "M顶":
                short_score += self.zigzag_score
                pattern_text = f"，形态：{zigzag_pattern}" if zigzag_pattern else ""
                short_details.append(f"ZigZag下降趋势{pattern_text}: +{self.zigzag_score}")

        return long_score, short_score, long_details, short_details
    
    def should_send_alert(self, symbol: str, metrics: Dict[str, Any], direction: str, score: int, status: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """判断是否应该发送提醒
        
        Args:
            symbol: 交易对符号
            metrics: 包含各种技术指标的字典
            direction: 信号方向 (long/short)
            score: 信号分数
            status: 交易对当前状态
            
        Returns:
            Tuple[bool, List[str]]: 是否应该发送提醒，以及不满足条件的原因列表
        """
        # 存储不满足的条件原因
        failed_conditions = []
        should_send = True
        
        # 检查信号分数是否达到阈值
        if score < self.signal_threshold:
            reason = f"{direction}信号分数{score}低于阈值{self.signal_threshold}"
            failed_conditions.append(reason)
            should_send = False
            
        # 1. 首要条件：检查价格自上次提醒后，是否有足够的变化。
        #    只有在启用价格变化检查且status中有上次提醒的价格时，才执行此检查
        if self.enable_price_change_check and status.get("last_price", 0) > 0:
            price_change = abs(metrics["price"] - status["last_price"]) / status["last_price"]
            if price_change < self.price_change_threshold:
                reason = f"价格自上次提醒({status['last_price']:.4f})后变化不足({price_change:.2%}<{self.price_change_threshold:.2%})"
                failed_conditions.append(reason)
                should_send = False

        # 2. 基础条件：检查其他必要指标是否达标。
        #    只有在价格变化达标（或首次运行时）后，才检查这些。
        if self.enable_rsi_check and not (self.rsi_range["min"] <= metrics["rsi_5m"] <= self.rsi_range["max"]):
            reason = f"RSI({metrics['rsi_5m']:.2f})不在区间内({self.rsi_range['min']}-{self.rsi_range['max']})"
            failed_conditions.append(reason)
            should_send = False
            
        if self.enable_price_ema_check and metrics["price_ema_gap_ratio"] >= self.price_ema_gap_ratio:
            reason = f"价格偏离EMA({metrics['price_ema_gap_ratio']:.3%})超过阈值({self.price_ema_gap_ratio:.3%})"
            failed_conditions.append(reason)
            should_send = False
            
        # 如果启用信号分数变化检查且存在上次提醒，检查信号分数变化
        if self.enable_signal_score_change_check and status.get("last_score", 0) > 0:
            score_change = abs(score - status["last_score"])
            if score_change < self.signal_score_change_threshold:
                reason = f"信号分数变化({score_change})不足阈值({self.signal_score_change_threshold})"
                failed_conditions.append(reason)
                should_send = False
                
        # 如果启用RSI变化检查、启用RSI检查且存在上次提醒，检查RSI变化
        if self.enable_rsi_change_check and self.enable_rsi_check and status.get("last_rsi", 0) > 0:
            rsi_change = abs(metrics["rsi_5m"] - status["last_rsi"])
            if rsi_change < self.rsi_change_threshold:
                reason = f"RSI变化({rsi_change:.2f})不足阈值({self.rsi_change_threshold:.2f})"
                failed_conditions.append(reason)
                should_send = False
            
        # 如果通过了以上所有关卡，说明这是一个值得发送的、状态有实际变化的信号
        if should_send:
            signal_is_active = status.get('long', False) or status.get('short', False)
            if not signal_is_active:
                self.logger.info(f"[{symbol}] 首次触发信号，且所有条件满足，准备发送提醒。")
            else:
                self.logger.info(f"[{symbol}] 价格变化显著，且信号条件依然满足，准备发送更新提醒。")

        return should_send, failed_conditions