#!/usr/bin/env python3
"""
Simple test to verify router files can be parsed
"""

import ast
import sys
from pathlib import Path

def test_file_syntax(file_path):
    """Test that a Python file has valid syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        print(f"✓ {file_path.name}: Syntax OK")
        return True
    except SyntaxError as e:
        print(f"✗ {file_path.name}: Syntax error - {e}")
        return False
    except Exception as e:
        print(f"✗ {file_path.name}: Error reading file - {e}")
        return False

def main():
    """Main test function"""
    print("Testing HTTP Solution Router Files")
    print("=" * 40)
    
    success = True
    
    # Test router files
    router_files = [
        "src/routers/projects.py",
        "src/routers/work_packages.py", 
        "src/routers/users.py",
        "src/routers/__init__.py"
    ]
    
    for file_path in router_files:
        path = Path(file_path)
        if path.exists():
            success &= test_file_syntax(path)
        else:
            print(f"✗ {file_path}: File not found")
            success = False
    
    # Test main application file
    main_file = Path("src/main.py")
    if main_file.exists():
        success &= test_file_syntax(main_file)
    else:
        print(f"✗ {main_file}: File not found")
        success = False
    
    # Test dependencies file
    deps_file = Path("src/dependencies.py")
    if deps_file.exists():
        success &= test_file_syntax(deps_file)
    else:
        print(f"✗ {deps_file}: File not found")
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("✓ All files have valid syntax!")
        return 0
    else:
        print("✗ Some files have syntax errors!")
        return 1

if __name__ == "__main__":
    sys.exit(main())