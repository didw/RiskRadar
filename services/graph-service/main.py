#!/usr/bin/env python3
"""Graph Service Entry Point - 새로운 구조 사용"""
import sys
import os

# src 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SERVICE_PORT", "8003"))
    uvicorn.run(app, host="0.0.0.0", port=port)