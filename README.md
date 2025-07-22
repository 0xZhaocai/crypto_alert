# Crypto Alert System

加密货币价格监控与提醒工具，基于技术指标发送做多/做空信号提醒，并支持回测和性能分析。

## 功能特点

1. 监控多个加密货币的价格和技术指标
2. 根据预设条件（分数、价格变化、RSI等）发送做多/做空信号提醒
3. 支持通过飞书机器人发送格式化消息
4. 包含请求重试、超时和全面的错误处理机制
5. 使用SQLite数据库存储状态，避免对同一信号的重复提醒
6. 内置信号冷静期：信号消失后进入观察期，防止因短期波动导致状态频繁切换
7. 使用INI格式的配置文件，易于修改和维护
8. 可配置的条件控制，支持灵活启用或禁用特定指标检查
9. 自动回测功能：记录信号发出后1小时、4小时和24小时的价格变化
10. 性能分析报告：生成HTML格式的性能分析报告，包含胜率、平均收益等统计数据和可视化图表
11. 支持ZigZag指标：识别市场关键转折点，过滤市场噪音
12. 详细的指标参数显示：支持查看各项技术指标的详细参数

## 项目结构

项目代码已重组到`src`目录下，主要结构如下：

```
crypto_alert/
├── run.py                  # 主入口点脚本
├── main.py                 # 原入口点（已更新导入路径）
├── tools/                  # 工具脚本目录
│   ├── check_db.py             # 检查数据库脚本
│   ├── example_import.py       # 导入示例脚本
│   ├── generate_report.py      # 生成报告脚本
│   ├── run_backtest.py         # 运行回测脚本
│   └── run_simplified.py       # 简化入口点脚本
└── src/                    # 源代码目录
    ├── config/             # 配置文件目录
    │   ├── alert_config.ini    # 主配置文件
    │   ├── symbols.ini         # 交易对配置
    │   └── templates.ini       # 消息模板配置
    ├── core/               # 核心功能模块
    │   ├── alert_engine.py     # 告警引擎
    │   ├── data_fetcher.py     # 数据获取
    │   └── signal_evaluator.py # 信号评估
    ├── indicators/         # 技术指标模块
    │   ├── __init__.py         # 指标加载器
    │   ├── base_indicator.py   # 指标基类
    │   ├── rsi_indicator.py    # RSI指标
    │   ├── ema_indicator.py    # EMA指标
    │   ├── atr_indicator.py    # ATR指标
    │   ├── volume_indicator.py # 成交量指标
    │   ├── price_ema_gap_indicator.py # 价格与EMA偏离指标
    │   └── zigzag_indicator.py # ZigZag指标
    ├── notifiers/          # 通知模块
    │   ├── feishu_notifier.py  # 飞书通知
    │   └── message_formatter.py # 消息格式化
    ├── utils/              # 工具模块
    │   ├── config_loader.py    # 配置加载器
    │   ├── database.py         # 数据库工具
    │   └── logger.py           # 日志工具
    ├── tasks/              # 任务模块
    │   └── backtest_task.py    # 回测任务
    ├── analysis/           # 分析模块
    │   └── performance_analyzer.py # 性能分析器
    ├── data/               # 数据目录
    │   └── crypto_alert.db     # SQLite数据库
    ├── logs/               # 日志目录
    └── reports/            # 报告目录
```

## 使用方法

### 运行告警检查

```bash
python run.py
```

### 执行回测任务

```bash
python run.py --backtest
# 或者直接运行回测脚本
python tools/run_backtest.py
```

### 显示指标详情

```bash
python run.py --show-metrics BTCUSDT
```

### 显示指标帮助信息

```bash
python run.py --help-metrics
```

### 生成性能报告

```bash
python tools/generate_report.py --days 30
```

### 检查数据库

```bash
python tools/check_db.py
```

### 使用简化入口点

```bash
python tools/run_simplified.py
```

## 配置说明

### 主配置文件 (alert_config.ini)

```ini
[general]
# 飞书机器人webhook地址，用于发送提醒消息
feishu_webhook = https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-token

# 信号消失后的冷静期时间（分钟），超过此时间才会重置状态
cooldown_minutes = 60

# 触发信号所需的最低分数
signal_threshold = 6

[conditions]
# 条件控制部分，用于灵活启用或禁用特定指标检查
# 是否启用RSI指标检查
enable_rsi_check = true

# 是否启用价格与EMA偏离检查
enable_price_ema_check = true

# 是否启用ATR放大检查
enable_atr_check = false

# 是否启用成交量放大检查
enable_volume_check = true

# 是否启用ZigZag指标检查
enable_zigzag_check = true

# 是否启用价格变化阈值检查
enable_price_change_check = true

# 是否启用信号分数变化阈值检查
enable_signal_score_change_check = true

# 是否启用RSI变化阈值检查
enable_rsi_change_check = false

[indicators]
# RSI指标的范围
rsi_min = 40
rsi_max = 60

# 价格与EMA21的偏离比例阈值
price_ema_gap_ratio = 0.003

# ATR放大倍数阈值
atr_ratio = 1.1

# 成交量放大倍数阈值
volume_ratio = 1.3

# ZigZag指标的偏差百分比，用于过滤小波动
zigzag_deviation = 5

# ZigZag指标的极轴腿数量，用于控制转折点识别的灵敏度
zigzag_depth = 12

[scores]
# 各项指标的分数权重配置
# 理论最高分 = ema_15m_score + ema_1h_score + rsi_score + price_ema_gap_score + atr_score + volume_score + zigzag_score

# EMA趋势评分
ema_15m_score = 2
ema_1h_score = 2

# RSI区间评分
rsi_score = 1

# 价格贴近EMA评分
price_ema_gap_score = 2

# ATR放大评分
atr_score = 1

# 成交量放大评分
volume_score = 1

# ZigZag趋势评分
zigzag_score = 2

[thresholds]
# 价格变化阈值，价格变化超过此比例才会发送新提醒
price_change_threshold = 0.01

# 信号分数变化阈值，分数变化超过此值才会发送新提醒
signal_score_change_threshold = 1

# RSI变化阈值，RSI变化超过此值才会发送新提醒
rsi_change_threshold = 3

[database]
# SQLite数据库文件路径
db_path = ./data/crypto_alert.db

[logging]
# 日志文件路径
log_path = ./logs/crypto_alert.log
# 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
log_level = INFO
```

### 交易对配置 (symbols.ini)

```ini
[symbols]
# 格式: symbol_id = display_name
# symbol_id 是币安API使用的交易对符号
# display_name 是在提醒消息中显示的名称

BTCUSDT = BTC
ETHUSDT = ETH
SOLUSDT = SOL
XRPUSDT = XRP
AVAXUSDT = AVAX
BNBUSDT = BNB
```

### 消息模板配置 (templates.ini)

```ini
[message_templates]
# 消息模板使用Python的字符串格式化语法
# 可用变量:
# {symbol} - 交易对符号 (如 BTCUSDT)
# {name} - 显示名称 (如 BTC)
# {direction} - 信号方向 (多/空)
# {score} - 信号分数
# {price} - 当前价格
# {time} - 当前时间

# 标准提醒消息模板
alert = {name}\n🎯 信号：{direction} {score}/10\n💰 价格：{price:.4f} \n🕒 时间：{time} \nhttps://binance.com/zh-CN/futures/{symbol}
```

## 使用方法

1. 确保已安装Python 3.6+
2. 克隆或下载项目代码到本地
3. 安装依赖：`pip install -r requirements.txt`
4. 配置飞书机器人webhook地址和其他参数：
   - 修改 `src/config/alert_config.ini` 中的 `feishu_webhook` 为你的飞书机器人webhook地址
   - 根据需要调整其他配置参数

### 告警检查

运行程序：`python run.py`

建议使用任务计划定时运行：
- Linux/Mac (crontab)：
  ```
  */5 * * * * cd /path/to/crypto_alert && python run.py
  ```
- Windows (任务计划程序)：
  创建基本任务，设置触发器为每5分钟运行一次，操作为启动程序 `python`，参数为 `run.py`，起始位置为项目目录

### 回测功能

有两种方式运行回测：

1. 单次回测：`python run.py --backtest`
2. 持续回测服务：`python tools/run_backtest.py`（每小时自动执行回测任务）

回测功能会自动检查已发送的告警，并记录1小时、4小时和24小时后的价格变化情况。

### 性能分析

生成性能分析报告：`python tools/generate_report.py [--days 天数] [--output 输出文件路径]`

参数说明：
- `--days`：分析最近多少天的数据，默认30天
- `--output`：输出报告的路径，默认为`performance_report.html`

生成的报告包含以下内容：
- 总体性能统计（胜率、平均收益等）
- 按方向（多/空）的性能统计
- 收益率趋势图
- 各交易对性能对比图
- 各信号分数性能对比图
- 详细的告警性能数据表格

### 测试脚本

项目包含多个测试脚本，用于测试系统的各个组件和功能。详细说明请参考 `src/tests/README.md`。

```bash
# 运行基础组件测试
python src/tests/test_config_loader.py
python src/tests/test_database.py
python src/tests/test_data_fetcher.py
python src/tests/test_indicators.py

# 运行核心功能测试
python src/tests/test_signal_evaluator.py
python src/tests/test_alert_engine.py
python src/tests/test_alert.py
python src/tests/test_notifier.py

# 运行高级功能测试
python src/tests/test_backtest.py
python src/tests/test_performance_analyzer.py
```

## 信号评分与条件说明

### 信号评分规则

系统使用多项技术指标为交易信号评分，满分为12分，默认阈值为6分：

1. **基础价格指标**（最高4分）：
   - 价格 > EMA21(15m)：+2分（做多信号）
   - 价格 < EMA21(15m)：+2分（做空信号）
   - 价格 > EMA21(1h)：+2分（做多信号）
   - 价格 < EMA21(1h)：+2分（做空信号）

2. **RSI指标**（最高1分）：
   - RSI在设定区间内（默认40-60）：+1分
   - 示例：RSI = 45，在40-60区间内，得1分

3. **价格与EMA贴近度**（最高2分）：
   - 价格与EMA偏离比例小于阈值（默认0.3%）：+2分
   - 示例：价格偏离EMA仅0.2%，小于0.3%阈值，得2分

4. **ATR放大**（最高1分）：
   - ATR放大倍数大于等于阈值（默认1.1倍）：+1分
   - 示例：ATR放大1.5倍，大于1.1倍阈值，得1分

5. **成交量放大**（最高1分）：
   - 成交量放大倍数大于等于阈值（默认1.3倍）：+1分
   - 示例：成交量放大2倍，大于1.3倍阈值，得1分

6. **ZigZag趋势**（最高2分）：
   - ZigZag趋势与信号方向一致：+2分
   - 示例：ZigZag显示上升趋势，做多信号得2分

### 信号触发条件

系统使用两类条件来判断是否发送提醒：

#### 必要条件（一票否决）

以下条件必须全部满足，否则不会发送提醒：

1. **信号分数达标**：信号分数必须达到或超过阈值（默认6分）
   - 示例：BTC做多信号得分7分，超过阈值6分，满足条件
   - 示例：ETH做空信号得分5分，低于阈值6分，不满足条件

2. **RSI在合理区间**（如启用）：RSI必须在设定区间内
   - 示例：SOL的RSI为65，超出40-60区间，不满足条件
   - 示例：BNB的RSI为45，在40-60区间内，满足条件

3. **价格与EMA贴近**（如启用）：价格与EMA的偏离不能过大
   - 示例：AVAX价格偏离EMA 0.5%，超过0.3%阈值，不满足条件
   - 示例：XRP价格偏离EMA 0.2%，小于0.3%阈值，满足条件

#### 增强条件（防止重复提醒）

当存在上次提醒记录时，以下条件至少需要满足一项，才会发送新提醒：

1. **价格变化显著**：价格相比上次提醒变化超过阈值（默认1%）
   - 示例：BTC上次提醒价格30000，当前价格30500（变化1.67%），超过1%阈值，满足条件
   - 示例：ETH上次提醒价格2000，当前价格2015（变化0.75%），低于1%阈值，不满足条件

2. **信号分数变化显著**：信号分数相比上次提醒变化超过阈值（默认1分）
   - 示例：SOL上次提醒分数6分，当前分数8分（变化2分），超过1分阈值，满足条件
   - 示例：AVAX上次提醒分数7分，当前分数8分（变化1分），等于1分阈值，满足条件

3. **RSI变化显著**（如启用）：RSI相比上次提醒变化超过阈值（默认3点）
   - 示例：XRP上次提醒RSI为45，当前RSI为55（变化10点），超过3点阈值，满足条件
   - 示例：BNB上次提醒RSI为50，当前RSI为52（变化2点），低于3点阈值，不满足条件

## 扩展方向

### 功能扩展

1. **添加更多交易所API支持**
   - 支持OKX、Bybit、Huobi等主流交易所
   - 实现交易所接口抽象层，便于快速集成新交易所
   - 添加跨交易所套利信号检测

2. **增加更多技术指标和评分规则**
   - 布林带、MACD、KDJ等经典指标
   - 波动率指标（如Bollinger Bandwidth）
   - 自定义组合指标和条件逻辑
   - 示例：当价格突破上轨且RSI<70时，发出做多信号

3. **支持更多通知渠道**
   - Telegram机器人集成
   - Discord Webhook支持
   - 电子邮件通知
   - 短信通知（适用于重要信号）

4. **添加Web界面**
   - 实时监控面板，展示各币种信号状态
   - 历史信号查询和统计分析
   - 可视化配置界面，无需手动编辑配置文件
   - 移动端自适应设计

### 性能与可靠性

1. **优化数据获取**
   - 实现WebSocket实时数据订阅
   - 添加本地数据缓存，减少API调用
   - 多线程并行获取多币种数据

2. **增强错误处理**
   - 完善网络异常重试机制
   - 添加自动恢复和状态保存
   - 实现健康检查和自我修复

### 分析与回测增强

1. **回测功能增强**
   - 历史数据回测引擎（支持回溯测试）
   - 参数优化和敏感性分析
   - 示例：测试不同RSI区间（30-70、40-60）对信号质量的影响

2. **机器学习增强**
   - 使用机器学习模型预测信号可靠性
   - 自适应参数调整
   - 异常模式检测

### 集成与自动化

1. **交易执行集成**
   - 基于信号自动执行交易
   - 风险管理和仓位控制
   - 止损止盈策略

2. **多策略组合**
   - 支持多个策略并行运行
   - 策略投票机制
   - 自定义策略权重

## 贡献指南

欢迎贡献代码、报告问题或提出改进建议。请遵循以下步骤：

1. Fork 项目仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件

## 联系方式

如有问题或建议，请通过以下方式联系：

- 项目维护者：[Your Name](mailto:your.email@example.com)
- 项目仓库：[GitHub Repository](https://github.com/yourusername/crypto_alert)