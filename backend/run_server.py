#!/usr/bin/env python3
"""
Cineo AI Backend Startup Script
This script ensures proper Python path setup for the backend.
"""

import sys
import os

# Detect if running in Kaggle/Colab
if "kaggle" in os.getcwd() or "content" in os.getcwd():
    # Path to the project root
    project_root = "/kaggle/working/Cineo-movie-gen"  # Change if cloned elsewhere
else:
    # Local path
    project_root = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))

# Add project root to Python path
sys.path.insert(0, project_root)

# Now import and run the main application
from backend.main import app
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Cineo AI Backend Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
