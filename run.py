#!/usr/bin/env python3
"""
Run script that sets up everything and executes the main script.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    # Get the directory of this script
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("=" * 60)
    print("MooviDump Enhanced - Automatic Setup & Execution")
    print("=" * 60)
    
    # Step 1: Check if .env exists
    print("\n[1/3] Checking .env file...")
    env_file = script_dir / ".env"
    if not env_file.exists():
        print("❌ .env file not found!")
        print("   Please create a .env file with the following variables:")
        print("   - MOODLE_SITE=https://your-moodle-site.com")
        print("   - MOODLE_USERNAME=your_username")
        print("   - MOODLE_PASSWORD=your_password")
        print("\n   You can use example.env as a template.")
        sys.exit(1)
    print("✓ .env file found")
    
    # Step 2: Install requirements
    print("\n[2/3] Installing dependencies...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            print("✓ Dependencies installed successfully")
        else:
            print("⚠ Warning: Some dependencies may have failed to install")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        sys.exit(1)
    
    # Step 3: Run main.py
    print("\n[3/3] Running main.py...")
    print("-" * 60)
    try:
        result = subprocess.run(
            [sys.executable, "main.py"],
            check=False
        )
        sys.exit(result.returncode)
    except Exception as e:
        print(f"❌ Error running main.py: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
