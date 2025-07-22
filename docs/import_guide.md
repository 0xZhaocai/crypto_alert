# 导入指南：使用重导出模块简化导入语句

## 概述

为了简化项目中的导入语句，我们在`src`目录和各个子模块目录下添加了`__init__.py`文件，用于重导出常用的类和函数。这样可以减少导入语句的数量，使代码更加简洁。

## 重导出的模块

### src包

`src/__init__.py`文件重导出了以下模块：

```python
# 从utils模块导出
from src.utils.config_loader import ConfigLoader, load_config
from src.utils.database import Database
from src.utils.logger import get_logger, setup_logger

# 从core模块导出
from src.core.alert_engine import AlertEngine
from src.core.data_fetcher import DataFetcher
from src.core.signal_evaluator import SignalEvaluator

# 从tasks模块导出
from src.tasks.backtest_task import run_backtest_task

# 从indicators模块导出
from src.indicators import load_indicators

# 从notifiers模块导出
from src.notifiers.feishu_notifier import FeishuNotifier

# 从analysis模块导出
from src.analysis.performance_analyzer import run_performance_analysis
```

### utils包

`src/utils/__init__.py`文件重导出了以下模块：

```python
from src.utils.config_loader import ConfigLoader, load_config
from src.utils.database import Database
from src.utils.logger import get_logger, setup_logger
```

## 使用方法

### 方法1：直接从src包导入

```python
# 导入所需的类和函数
from src import ConfigLoader, Database, get_logger, AlertEngine

# 使用导入的类和函数
config_loader = ConfigLoader("path/to/config")
db = Database("path/to/db")
logger = get_logger()
```

### 方法2：导入整个src包

```python
import src

# 使用点号访问导出的类和函数
config_loader = src.ConfigLoader("path/to/config")
db = src.Database("path/to/db")
logger = src.get_logger()
```

### 方法3：从子模块导入

```python
# 从utils子模块导入
from src.utils import ConfigLoader, Database, get_logger

# 使用导入的类和函数
config_loader = ConfigLoader("path/to/config")
db = Database("path/to/db")
logger = get_logger()
```

## 对比：原始导入方式

原始导入方式需要多行导入语句：

```python
from src.utils.config_loader import ConfigLoader
from src.utils.database import Database
from src.utils.logger import get_logger
from src.core.alert_engine import AlertEngine
from src.tasks.backtest_task import run_backtest_task
from src.indicators import load_indicators
```

使用重导出模块后，可以简化为：

```python
from src import ConfigLoader, Database, get_logger, AlertEngine, run_backtest_task, load_indicators
```

## 注意事项

1. 使用重导出模块时，仍然需要确保`src`目录在Python的导入路径中。可以通过以下代码添加：

```python
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```

2. 如果需要导入未在`__init__.py`中重导出的模块，仍然需要使用完整的导入路径。

3. 在添加新的模块时，记得更新相应的`__init__.py`文件，以便将新模块也重导出。

## 示例文件

项目中提供了两个示例文件，展示了如何使用重导出模块：

- `example_import.py`：展示了不同的导入方式
- `main_simplified.py`：展示了如何简化`main.py`中的导入语句