#!/usr/bin/env python3
"""
Run script that sets up everything and executes the main script.
"""
import subprocess
import sys
import os
from pathlib import Path
import getpass

def create_env_file(env_file):
    """Create .env file interactively if it doesn't exist."""
    print("\n❌ .env file not found!")
    print("   Let's create it now.\n")
    
    # Get MOODLE_SITE
    default_site = "https://moovi.uvigo.gal"
    site_input = input(f"   MOODLE_SITE [{default_site}]: ").strip()
    moodle_site = site_input if site_input else default_site
    
    # Get USERNAME
    username = input("   MOODLE_USERNAME: ").strip()
    if not username:
        print("   ❌ Username is required!")
        return False
    
    # Get PASSWORD
    password = getpass.getpass("   MOODLE_PASSWORD: ")
    if not password:
        print("   ❌ Password is required!")
        return False
    
    # Create .env file
    try:
        env_content = f"""MOODLE_SITE="{moodle_site}"
MOODLE_USERNAME="{username}"
MOODLE_PASSWORD="{password}"
"""
        env_file.write_text(env_content)
        print(f"\n✓ .env file created successfully!")
        return True
    except Exception as e:
        print(f"   ❌ Error creating .env file: {e}")
        return False

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
        if not create_env_file(env_file):
            sys.exit(1)
    else:
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
