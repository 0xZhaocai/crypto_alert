# 信号记录数据库结构说明

## 数据库文件
- **文件名**: `signals.db`
- **位置**: 与 `alert_15m.py` 同目录
- **类型**: SQLite 数据库

## 表结构

### signal_records 表

存储所有触发的交易信号记录，用于后续分析和统计。

#### 字段说明

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `id` | INTEGER | 主键，自增 | 1, 2, 3... |
| `symbol` | TEXT | 代币符号 | "BTCUSDT", "ETHUSDT" |
| `timestamp` | TEXT | 信号触发时间 | "2024-01-15 14:30:25" |
| `direction` | TEXT | 交易方向 | "多", "空" |
| `score` | INTEGER | 信号评分 | 8, 10, 12 |
| `price` | REAL | 触发时价格 | 43250.5678 |
| `price_above_ema21_15m` | INTEGER | 价格 > EMA21(15m) | 0 或 1 |
| `price_above_ema21_1h` | INTEGER | 价格 > EMA21(1h) | 0 或 1 |
| `price_below_ema21_15m` | INTEGER | 价格 < EMA21(15m) | 0 或 1 |
| `price_below_ema21_1h` | INTEGER | 价格 < EMA21(1h) | 0 或 1 |
| `rsi_in_range` | INTEGER | RSI在区间内 | 0 或 1 |
| `price_near_ema21` | INTEGER | 价格贴近15mEMA21 | 0 或 1 |
| `atr_amplified` | INTEGER | ATR放大 | 0 或 1 |
| `volume_amplified` | INTEGER | 成交量放大 | 0 或 1 |
| `ema_convergence` | INTEGER | EMA9/21靠近 | 0 或 1 |
| `created_at` | TEXT | 记录创建时间 | 自动生成 |

#### 条件字段详解

所有条件字段使用布尔值表示（0=不满足，1=满足）：

**多头条件**：
- `price_above_ema21_15m`: 当前价格高于15分钟EMA21
- `price_above_ema21_1h`: 当前价格高于1小时EMA21

**空头条件**：
- `price_below_ema21_15m`: 当前价格低于15分钟EMA21
- `price_below_ema21_1h`: 当前价格低于1小时EMA21

**通用条件**：
- `rsi_in_range`: RSI在配置的区间内
- `price_near_ema21`: 价格贴近15分钟EMA21（偏离度小于阈值）
- `atr_amplified`: ATR放大（波动性增加）
- `volume_amplified`: 成交量放大
- `ema_convergence`: EMA9和EMA21靠近（任一周期）

## 使用示例

### 查询所有记录
```sql
SELECT * FROM signal_records ORDER BY timestamp DESC;
```

### 查询特定代币的记录
```sql
SELECT * FROM signal_records WHERE symbol = 'BTCUSDT' ORDER BY timestamp DESC;
```

### 统计各条件出现频率
```sql
SELECT 
    COUNT(*) as total_signals,
    SUM(price_above_ema21_15m) as price_above_ema21_15m_count,
    SUM(rsi_in_range) as rsi_in_range_count,
    SUM(volume_amplified) as volume_amplified_count,
    SUM(ema_convergence) as ema_convergence_count
FROM signal_records;
```

### 查询高分信号
```sql
SELECT * FROM signal_records WHERE score >= 10 ORDER BY timestamp DESC;
```

### 按方向统计
```sql
SELECT direction, COUNT(*) as count, AVG(score) as avg_score 
FROM signal_records 
GROUP BY direction;
```

## 数据维护

- 数据库会在首次运行时自动创建
- 每次触发信号并发送提醒时自动插入记录
- 建议定期备份数据库文件
- 可根据需要清理历史数据

## 扩展建议

如需添加新的条件字段：
1. 在 `init_database()` 函数中添加新字段到 CREATE TABLE 语句
2. 在 `save_signal_record()` 函数中添加对应的解析逻辑
3. 更新此文档说明