#!/usr/bin/env python3
"""
Cineo AI Backend Startup Script
This script ensures proper Python path setup for the backend.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))  # backend/
project_root = os.path.dirname(project_root)              # Cineo-movie-gen/
sys.path.insert(0, project_root)

# Now import and run the main application
from backend.main import app
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Cineo AI Backend Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
