#!/usr/bin/env python3
"""Test script to verify statsmodels import is working"""

import sys

print("=" * 60)
print("Testing statsmodels import...")
print("=" * 60)

try:
    from statsmodels import api as sm
    print("✓ SUCCESS: statsmodels.api imported successfully")
    print(f"  statsmodels version: {sm.__version__}")
    print(f"  VAR available: {hasattr(sm, 'VAR')}")
    if hasattr(sm, 'VAR'):
        print(f"  VAR class: {sm.VAR}")
    print("\n✓ The statsmodels import error has been FIXED!")
    sys.exit(0)
except ImportError as e:
    print(f"✗ ERROR: {e}")
    print("\nDebug info:")
    try:
        import statsmodels
        print(f"  statsmodels module found: {statsmodels}")
        print(f"  statsmodels.__file__: {statsmodels.__file__}")
    except ImportError as e2:
        print(f"  Cannot import statsmodels: {e2}")
    sys.exit(1)
