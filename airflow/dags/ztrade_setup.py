"""
Shared setup module for all Ztrade trading DAGs.

This module handles Python path configuration to ensure Ztrade modules
can be imported correctly in all Airflow DAG files.

Import this at the top of every DAG file:
    import ztrade_setup
"""
import sys
import os

# Add Ztrade package to Python path
# In Docker: /opt/airflow/ztrade
# Locally: configured via ZTRADE_PATH env var
ZTRADE_PATH = os.getenv('ZTRADE_PATH', '/opt/airflow/ztrade')

if ZTRADE_PATH not in sys.path:
    sys.path.insert(0, ZTRADE_PATH)
