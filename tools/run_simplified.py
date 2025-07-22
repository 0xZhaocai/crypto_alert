#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
加密货币价格告警系统入口点（简化导入版本）

此脚本作为项目的主入口点，导入src包并执行其main函数。
这样可以保持原有的使用方式不变，同时将代码结构重组到src目录下。
"""

import sys
import os

# 确保能够导入src包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 方法1：直接导入main函数
from src.main import main

# 方法2（可选）：如果在src/__init__.py中重导出了main函数，可以这样导入
# from src import main

if __name__ == "__main__":
    main()