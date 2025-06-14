#!/usr/bin/env python3
"""
Script to run the Moving Average Consumer
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.moving_average_consumer import main

if __name__ == "__main__":
    print("Starting Moving Average Consumer...")
    print("Press Ctrl+C to stop")
    main()