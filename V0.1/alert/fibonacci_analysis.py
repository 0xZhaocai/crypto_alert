import sys
import os

# 添加当前目录到Python路径，以便导入utils模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import get_klines

"""
斐波那契数列与K线价格分析工具

功能：
1. 生成斐波那契数列
2. 调用utils.py的get_klines函数获取不同周期的K线数据
3. 分析1D、4h、1h周期288根K线的最高价和最低价
4. 结合斐波那契比例进行价格分析

实现逻辑：
- 斐波那契数列：用于计算回调位和扩展位
- K线数据获取：分别获取日线、4小时线、1小时线的288根K线
- 价格分析：提取每个周期的最高价和最低价
- 斐波那契分析：计算关键的斐波那契回调位（23.6%, 38.2%, 50%, 61.8%, 78.6%）
"""


def generate_fibonacci_sequence(n):
    """
    生成斐波那契数列
    
    Args:
        n (int): 生成数列的长度
    
    Returns:
        list: 斐波那契数列
    """
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    fib_sequence = [0, 1]
    for i in range(2, n):
        fib_sequence.append(fib_sequence[i-1] + fib_sequence[i-2])
    
    return fib_sequence


def get_fibonacci_ratios():
    """
    获取常用的斐波那契比例
    
    Returns:
        dict: 斐波那契比例字典
    """
    return {
        '23.6%': 0.236,
        '38.2%': 0.382,
        '50.0%': 0.500,
        '61.8%': 0.618,
        '78.6%': 0.786
    }


def analyze_kline_prices(symbol, interval, limit=288):
    """
    分析K线数据的价格信息
    
    Args:
        symbol (str): 交易对符号
        interval (str): K线周期
        limit (int): K线数量
    
    Returns:
        dict: 包含最高价、最低价等信息的字典
    """
    try:
        print(f"\n📊 获取 {symbol} {interval} 周期的 {limit} 根K线数据...")
        klines = get_klines(symbol, interval, limit)
        
        if not klines or len(klines) == 0:
            raise Exception(f"未获取到 {interval} 周期的K线数据")
        
        # 提取价格数据
        highs = [float(kline[2]) for kline in klines]  # 最高价
        lows = [float(kline[3]) for kline in klines]   # 最低价
        closes = [float(kline[4]) for kline in klines] # 收盘价
        
        # 计算关键价格
        highest_price = max(highs)
        lowest_price = min(lows)
        current_price = closes[-1]
        price_range = highest_price - lowest_price
        
        # 找到最高价和最低价的位置
        highest_index = highs.index(highest_price)
        lowest_index = lows.index(lowest_price)
        
        return {
            'interval': interval,
            'kline_count': len(klines),
            'highest_price': highest_price,
            'lowest_price': lowest_price,
            'current_price': current_price,
            'price_range': price_range,
            'highest_index': highest_index,
            'lowest_index': lowest_index,
            'highs': highs,
            'lows': lows,
            'closes': closes
        }
        
    except Exception as e:
        print(f"❌ 分析 {interval} 周期K线失败: {e}")
        return None


def calculate_fibonacci_levels(high_price, low_price, is_uptrend=True):
    """
    计算斐波那契回调位
    
    Args:
        high_price (float): 最高价
        low_price (float): 最低价
        is_uptrend (bool): 是否为上升趋势
    
    Returns:
        dict: 斐波那契回调位字典
    """
    price_range = high_price - low_price
    ratios = get_fibonacci_ratios()
    
    fib_levels = {}
    
    if is_uptrend:
        # 上升趋势：从高点回调
        for name, ratio in ratios.items():
            fib_levels[name] = high_price - (price_range * ratio)
    else:
        # 下降趋势：从低点反弹
        for name, ratio in ratios.items():
            fib_levels[name] = low_price + (price_range * ratio)
    
    return fib_levels


def analyze_fibonacci_convergence(analysis_results, convergence_threshold=2.0):
    """
    分析多周期斐波那契价位的收敛性，判断是否形成横盘区
    
    Args:
        analysis_results (dict): 各周期的分析结果
        convergence_threshold (float): 收敛阈值（百分比）
    
    Returns:
        dict: 收敛性分析结果
    """
    if len(analysis_results) < 2:
        return None
    
    print(f"\n🔄 多周期斐波那契收敛性分析 (阈值: {convergence_threshold}%):")
    print("=" * 50)
    
    # 计算各周期的斐波那契回调位
    fib_data = {}
    ratios = get_fibonacci_ratios()
    
    for interval, result in analysis_results.items():
        is_uptrend = result['highest_index'] > result['lowest_index']
        fib_levels = calculate_fibonacci_levels(
            result['highest_price'], 
            result['lowest_price'], 
            is_uptrend
        )
        fib_data[interval] = fib_levels
    
    # 分析每个斐波那契比例的收敛性
    convergence_analysis = {}
    
    for ratio_name in ratios.keys():
        prices = [fib_data[interval][ratio_name] for interval in analysis_results.keys()]
        
        # 计算价格振幅
        max_price = max(prices)
        min_price = min(prices)
        price_range = max_price - min_price
        avg_price = sum(prices) / len(prices)
        amplitude_percent = (price_range / avg_price) * 100
        
        # 判断是否收敛
        is_convergent = amplitude_percent <= convergence_threshold
        
        convergence_analysis[ratio_name] = {
            'prices': prices,
            'max_price': max_price,
            'min_price': min_price,
            'avg_price': avg_price,
            'price_range': price_range,
            'amplitude_percent': amplitude_percent,
            'is_convergent': is_convergent
        }
        
        # 输出分析结果
        status = "✅ 收敛" if is_convergent else "❌ 发散"
        print(f"\n📊 {ratio_name} 斐波那契位分析:")
        
        intervals = list(analysis_results.keys())
        for i, interval in enumerate(intervals):
            print(f"   {interval:>3}: {prices[i]:>10.4f}")
        
        print(f"   最高价: {max_price:>10.4f}")
        print(f"   最低价: {min_price:>10.4f}")
        print(f"   平均价: {avg_price:>10.4f}")
        print(f"   振幅: {price_range:>12.4f} ({amplitude_percent:.2f}%)")
        print(f"   状态: {status}")
        
        if is_convergent:
            print(f"   💡 在 {avg_price:.4f} 附近形成潜在横盘区")
    
    return convergence_analysis


def calculate_time_equivalent_limits(base_interval, base_limit, target_intervals):
    """
    根据基准周期和K线数量，计算其他周期的等时间K线数量
    
    Args:
        base_interval (str): 基准周期
        base_limit (int): 基准K线数量
        target_intervals (list): 目标周期列表
    
    Returns:
        dict: 各周期对应的K线数量
    """
    # 定义各周期对应的小时数
    interval_hours = {
        "1m": 1/60,
        "5m": 5/60,
        "15m": 15/60,
        "30m": 30/60,
        "1h": 1,
        "4h": 4,
        "1d": 24,
        "1w": 24 * 7
    }
    
    if base_interval not in interval_hours:
        raise ValueError(f"不支持的基准周期: {base_interval}")
    
    # 计算基准时间范围（小时）
    base_hours = interval_hours[base_interval] * base_limit
    
    # 计算各周期对应的K线数量
    limits = {}
    for interval in target_intervals:
        if interval not in interval_hours:
            print(f"⚠️ 警告: 不支持的周期 {interval}，跳过")
            continue
        
        # 计算该周期需要的K线数量
        required_limit = int(base_hours / interval_hours[interval])
        
        # 确保至少有足够的K线用于技术指标计算
        min_limit = 50
        limits[interval] = max(required_limit, min_limit)
    
    return limits, base_hours


def main():
    """
    主函数：执行斐波那契分析
    """
    print("🔢 斐波那契数列与K线价格分析工具")
    print("=" * 50)
    
    # 1. 生成斐波那契数列
    print("\n📈 生成斐波那契数列（前20项）:")
    fib_sequence = generate_fibonacci_sequence(20)
    print(f"斐波那契数列: {fib_sequence}")
    
    # 2. 显示斐波那契比例
    print("\n📊 常用斐波那契比例:")
    ratios = get_fibonacci_ratios()
    for name, ratio in ratios.items():
        print(f"{name}: {ratio}")
    
    # 3. 设置分析参数
    symbol = "BTCUSDT"  # 可以修改为其他交易对
    intervals = ["1d", "4h", "1h"]
    base_interval = "1h"  # 基准周期
    base_limit = 288     # 基准K线数量
    convergence_threshold = 2.0  # 收敛阈值：2%
    
    # 计算各周期的等时间K线数量
    interval_limits, total_hours = calculate_time_equivalent_limits(base_interval, base_limit, intervals)
    
    print(f"\n🎯 分析目标: {symbol}")
    print(f"📅 K线周期: {', '.join(intervals)}")
    print(f"⏰ 基准周期: {base_interval} ({base_limit} 根)")
    print(f"🕒 总时间范围: {total_hours:.0f} 小时 ({total_hours/24:.1f} 天)")
    print(f"🎚️ 收敛阈值: {convergence_threshold}%")
    
    print(f"\n📊 各周期K线数量 (等时间范围):")
    for interval in intervals:
        if interval in interval_limits:
            print(f"   {interval:>3}: {interval_limits[interval]:>3} 根")
    
    # 4. 分析各周期的K线数据
    analysis_results = {}
    
    for interval in intervals:
        if interval not in interval_limits:
            print(f"⚠️ 跳过不支持的周期: {interval}")
            continue
            
        limit = interval_limits[interval]
        result = analyze_kline_prices(symbol, interval, limit)
        if result:
            analysis_results[interval] = result
            
            print(f"\n📈 {interval} 周期分析结果:")
            print(f"   K线数量: {result['kline_count']} 根 (目标: {limit} 根)")
            print(f"   最高价: {result['highest_price']:.4f} (第 {result['highest_index']+1} 根K线)")
            print(f"   最低价: {result['lowest_price']:.4f} (第 {result['lowest_index']+1} 根K线)")
            print(f"   当前价: {result['current_price']:.4f}")
            print(f"   价格区间: {result['price_range']:.4f}")
            
            # 计算斐波那契回调位
            is_uptrend = result['highest_index'] > result['lowest_index']
            trend_direction = "上升趋势" if is_uptrend else "下降趋势"
            print(f"   趋势方向: {trend_direction}")
            
            fib_levels = calculate_fibonacci_levels(
                result['highest_price'], 
                result['lowest_price'], 
                is_uptrend
            )
            
            print(f"   斐波那契回调位:")
            for level_name, level_price in fib_levels.items():
                print(f"     {level_name}: {level_price:.4f}")
    
    # 5. 多周期斐波那契收敛性分析
    if len(analysis_results) >= 2:
        convergence_analysis = analyze_fibonacci_convergence(analysis_results, convergence_threshold)
        
        # 统计收敛的斐波那契位
        if convergence_analysis:
            convergent_levels = [name for name, data in convergence_analysis.items() if data['is_convergent']]
            
            print(f"\n🎯 收敛性总结:")
            print(f"   收敛的斐波那契位: {len(convergent_levels)}/{len(convergence_analysis)}")
            
            if convergent_levels:
                print(f"   收敛位列表: {', '.join(convergent_levels)}")
                print(f"\n💡 交易建议:")
                for level_name in convergent_levels:
                    avg_price = convergence_analysis[level_name]['avg_price']
                    print(f"   - {level_name} 位 ({avg_price:.4f}) 可作为关键支撑/阻力位")
            else:
                print(f"   ⚠️ 当前没有收敛的斐波那契位，市场可能处于高波动状态")
    
    # 6. 综合分析
    print("\n🔍 综合分析:")
    print("=" * 30)
    
    if analysis_results:
        # 比较不同周期的价格区间
        print("\n📊 各周期价格区间对比:")
        for interval, result in analysis_results.items():
            volatility = (result['price_range'] / result['current_price']) * 100
            print(f"   {interval:>3}: 区间 {result['price_range']:.4f}, 波动率 {volatility:.2f}%")
        
        # 寻找关键支撑阻力位
        print("\n🎯 关键价位分析:")
        all_highs = []
        all_lows = []
        
        for result in analysis_results.values():
            all_highs.append(result['highest_price'])
            all_lows.append(result['lowest_price'])
        
        overall_high = max(all_highs)
        overall_low = min(all_lows)
        
        print(f"   整体最高价: {overall_high:.4f}")
        print(f"   整体最低价: {overall_low:.4f}")
        
        # 计算整体斐波那契位
        overall_fib = calculate_fibonacci_levels(overall_high, overall_low, True)
        print(f"\n🔢 整体斐波那契回调位:")
        for level_name, level_price in overall_fib.items():
            print(f"     {level_name}: {level_price:.4f}")
    
    print("\n✅ 分析完成！")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 程序执行失败: {e}")
        import traceback
        traceback.print_exc()