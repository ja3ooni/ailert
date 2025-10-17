#!/usr/bin/env python3
"""
Simple test runner to verify the application works
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all imports work"""
    print("Testing imports...")
    
    try:
        from app.main import scheduler, health_check
        print("[OK] Main imports successful")
    except Exception as e:
        print(f"[ERROR] Main imports failed: {e}")
        return False
    
    try:
        from router.routes import bp
        print("[OK] Router imports successful")
    except Exception as e:
        print(f"[ERROR] Router imports failed: {e}")
        return False
    
    try:
        from launch import app
        print("[OK] Flask app imports successful")
    except Exception as e:
        print(f"[ERROR] Flask app imports failed: {e}")
        return False
    
    return True

def test_health():
    """Test health check"""
    print("\nTesting health check...")
    
    try:
        from app.main import health_check
        health = health_check()
        print(f"Health status: {health['status']}")
        
        for check, status in health['checks'].items():
            print(f"  {check}: {'[OK]' if status else '[FAIL]'}")
        
        return health['status'] == 'healthy'
    except Exception as e:
        print(f"[ERROR] Health check failed: {e}")
        return False

def main():
    """Run basic tests"""
    print("Running Newsletter Application Tests...\n")
    
    # Test imports
    if not test_imports():
        print("\n[ERROR] Import tests failed. Please check your configuration.")
        return False
    
    # Test health
    if not test_health():
        print("\n[WARNING] Health check shows issues, but application can still run.")
    
    print("\n[OK] Basic tests completed!")
    print("\nTo run the full application:")
    print("  uv run python run.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)