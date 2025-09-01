#!/usr/bin/env python3
"""
Symphony Monorepo Development Setup

Install all Symphony packages in development mode for local development.
"""

import subprocess
import sys
from pathlib import Path

def run_command(command, cwd=None):
    """Run a command and return success status"""
    try:
        # Use python3 -m pip instead of just pip
        if command.startswith("pip "):
            command = command.replace("pip ", "python3 -m pip ", 1)
        
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Command failed: {command}")
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"❌ Exception running command: {command}")
        print(f"Error: {e}")
        return False

def main():
    """Setup Symphony development environment"""
    print("🎼 Setting up Symphony Development Environment")
    print("=" * 50)
    
    symphony_root = Path(__file__).parent
    print(f"Symphony Root: {symphony_root}")
    
    # List of packages to install in development mode
    packages = [
        "libs/symphony-core",
        "libs/symphony-integrations", 
        "libs/symphony-templates",
        "apps/symphony-cli"
    ]
    
    # Install each package in development mode
    success_count = 0
    for package in packages:
        package_path = symphony_root / package
        if package_path.exists():
            print(f"\n📦 Installing {package}...")
            if run_command(f"pip install -e .", cwd=package_path):
                print(f"✅ {package} installed successfully")
                success_count += 1
            else:
                print(f"❌ Failed to install {package}")
        else:
            print(f"⚠️ Package directory not found: {package_path}")
    
    print(f"\n📊 Installation Summary:")
    print(f"✅ Successful: {success_count}/{len(packages)}")
    
    if success_count == len(packages):
        print("\n🎯 Development environment setup complete!")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and configure API tokens")
        print("2. Run: symphony setup env")
        print("3. Test with: symphony --version")
        print("4. Start developing: symphony --help")
    else:
        print(f"\n⚠️ Some packages failed to install. Please check errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()