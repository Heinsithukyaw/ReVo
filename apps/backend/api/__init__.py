#!/usr/bin/env python3
"""
Refactored Backend API for reVoAgent
Clean, modular API structure extracted from the monolithic main.py
"""

from .main_api import create_refactored_app

__all__ = [
    'create_refactored_app'
]