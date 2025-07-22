# Crypto Alert 本地配置指南

本文档提供了关于如何配置和使用本地环境特定文件的指南，这些文件不会被提交到GitHub仓库。

## 本地配置文件

### config.local.ini

`config.local.ini` 文件包含敏感信息和本地环境特定的配置，如API密钥、webhook地址等。该文件已在 `.gitignore` 中设置为忽略，不会被提交到GitHub。

#### 使用方法

1. 复制示例配置文件：
   ```bash
   cp config.local.ini.example config.local.ini
   ```

2. 编辑 `config.local.ini` 文件，填入你的实际配置：
   ```ini
   [api_keys]
   binance_api_key = YOUR_ACTUAL_API_KEY
   binance_api_secret = YOUR_ACTUAL_API_SECRET
   
   [webhooks]
   feishu_webhook = https://open.feishu.cn/open-apis/bot/v2/hook/your-actual-token
   ```

3. 程序会自动加载此配置文件（如果存在），并覆盖默认配置。

### secrets.ini

如果你需要存储更多敏感信息，可以创建 `secrets.ini` 文件。该文件同样已在 `.gitignore` 中设置为忽略。

### .env.local

如果你使用环境变量进行配置，可以创建 `.env.local` 文件。该文件已在 `.gitignore` 中设置为忽略。

示例：
```
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
FEISHU_WEBHOOK=your_webhook_url
```

## 数据库文件

`src/data/crypto_alert.db` SQLite数据库文件已在 `.gitignore` 中设置为忽略，不会被提交到GitHub。这样可以避免将个人数据提交到公共仓库。

## 日志文件

`src/logs/` 目录下的所有 `.log` 文件已在 `.gitignore` 中设置为忽略，不会被提交到GitHub。

## 报告文件

`src/reports/` 目录下的所有 `.html` 文件已在 `.gitignore` 中设置为忽略，不会被提交到GitHub。

## IDE配置文件

`.idea/`, `.vscode/` 目录和 `*.swp`, `*.swo` 文件已在 `.gitignore` 中设置为忽略，不会被提交到GitHub。

## 本地配置加载逻辑

程序会按以下优先级加载配置：

1. 命令行参数（最高优先级）
2. 环境变量（如果存在 `.env.local` 文件）
3. `config.local.ini` 文件中的配置
4. `secrets.ini` 文件中的配置
5. 默认配置文件 `src/config/alert_config.ini`（最低优先级）

这样可以确保你的敏感信息和本地特定配置不会被意外提交到公共仓库。