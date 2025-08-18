# -*- coding: utf-8 -*-
"""项目根包"""
import sys
import os

# 确保项目根目录在Python路径中
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)
