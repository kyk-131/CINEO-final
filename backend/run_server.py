#!/usr/bin/env python3
"""
Cineo AI Backend Startup Script
This script ensures proper Python path setup for the backend.
"""

import sys
import os

# Add the parent directory to Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Now import and run the main application
from backend.main import app
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Cineo AI Backend Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
