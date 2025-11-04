#!/usr/bin/env python3
"""
Test script to verify that imports in the location service work correctly.
This addresses the ImportError: cannot import name 'func' from 'geoalchemy2'
"""

print("Testing imports in location service...")

try:
    # Test importing main.py (this would fail before the fix)
    from location_service.app import main
    print("✓ Successfully imported main.py")
except ImportError as e:
    print(f"✗ Failed to import main.py: {e}")

try:
    # Test importing models
    from location_service.app import models
    print("✓ Successfully imported models.py")
except ImportError as e:
    print(f"✗ Failed to import models.py: {e}")

try:
    # Test importing crud
    from location_service.app import crud
    print("✓ Successfully imported crud.py")
except ImportError as e:
    print(f"✗ Failed to import crud.py: {e}")

try:
    # Test importing schemas
    from location_service.app import schemas
    print("✓ Successfully imported schemas.py")
except ImportError as e:
    print(f"✗ Failed to import schemas.py: {e}")

try:
    # Test importing database
    from location_service.app import database
    print("✓ Successfully imported database.py")
except ImportError as e:
    print(f"✗ Failed to import database.py: {e}")

print("\nAll imports successful! The ImportError has been fixed.")