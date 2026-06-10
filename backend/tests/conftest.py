"""GTCS 测试配置"""
import sys
from pathlib import Path

# 确保 backend 目录在 Python path 中
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# 测试用环境变量
import os
os.environ["GTCS_TAX_DIR"] = str(BACKEND_DIR / ".." / "税则库")
os.environ["SECRET_KEY"] = "test-secret-key-for-testing"
os.environ["CORS_ORIGINS"] = '["*"]'
