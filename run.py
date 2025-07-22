#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
加密货币价格告警系统入口点

此脚本作为项目的主入口点，导入src.main模块并执行其main函数。
这样可以保持原有的使用方式不变，同时将代码结构重组到src目录下。
"""

import sys
import os

# 确保当前目录在系统路径中，以便能够导入src包
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == "__main__":
    main()