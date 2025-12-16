#!/usr/bin/env python3
"""
Setup script for Flight Price Monitor Bot
This script helps you set up the bot for the first time
"""

import os
import sys
from pathlib import Path

def print_header():
    print("""
    ╔═══════════════════════════════════════════════════╗
    ║   Hotel Price Monitor Bot - Setup Wizard         ║
    ╚═══════════════════════════════════════════════════╝
    """)

def check_env_file():
    """Check if .env file exists"""
    if os.path.exists('.env'):
        print("[OK] .env file found")
        return True
    else:
        print("[WARN] .env file not found")
        return False

def create_env_from_example():
    """Create .env from .env.example"""
    if not os.path.exists('.env.example'):
        print("❌ .env.example not found!")
        return False
    
    print("\nCreating .env file from template...")
    
    with open('.env.example', 'r') as f:
        example_content = f.read()
    
    with open('.env', 'w') as f:
        f.write(example_content)
    
    print("[OK] .env file created")
    print("\n[IMPORTANT] Edit .env file and add your actual API keys")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    print("\nChecking dependencies...")
    
    required_packages = [
        'telethon',
        'anthropic',
        'aiohttp',
        'dotenv',
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"[OK] {package}")
        except ImportError:
            print(f"[MISS] {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("\nAll dependencies installed")
    return True

def create_directories():
    """Create necessary directories"""
    print("\nCreating directories...")
    
    directories = ['db', 'logs']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"[OK] {directory}/")
    
    return True

def check_git_security():
    """Check if sensitive files are properly gitignored"""
    print("\nChecking Git security...")
    
    if not os.path.exists('.git'):
        print("[WARN] Not a Git repository")
        return True
    
    # Check if .env is in .gitignore
    with open('.gitignore', 'r') as f:
        gitignore_content = f.read()
    
    if '.env' in gitignore_content:
        print("[OK] .env is gitignored")
    else:
        print("[ERROR] .env is NOT gitignored - SECURITY RISK")
        return False
    
    # Check if .env is tracked by git
    import subprocess
    result = subprocess.run(['git', 'ls-files', '.env'], 
                          capture_output=True, text=True)
    
    if result.stdout.strip():
        print("[ERROR] .env is tracked by Git")
        print("Run: git rm --cached .env")
        return False
    else:
        print("[OK] .env is not tracked by Git")
    
    return True

def print_next_steps():
    """Print next steps for the user"""
    print("""
    ╔═══════════════════════════════════════════════════╗
    ║              Next Steps                           ║
    ╚═══════════════════════════════════════════════════╝
    
    1. Edit .env file and add your API keys:
       
       Telegram: my.telegram.org + @BotFather
       Anthropic: console.anthropic.com
       RapidAPI (optional): rapidapi.com
    
    2. Install dependencies:
       pip install -r requirements.txt
    
    3. Run the bot:
       python hotel_monitor_bot.py
    
    4. Documentation:
       README.md - Full guide
       QUICKSTART.md - Quick setup
       SECURITY.md - Security practices
    
    IMPORTANT: Never commit .env to version control
    """)

def main():
    """Main setup function"""
    print_header()
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    # Create directories
    create_directories()
    
    # Check/create .env file
    env_exists = check_env_file()
    if not env_exists:
        response = input("\nCreate .env file from template? (y/n): ")
        if response.lower() == 'y':
            create_env_from_example()
        else:
            print("⚠️  You'll need to create .env file manually")
    
    # Check git security
    check_git_security()
    
    # Print next steps
    print_next_steps()
    
    if deps_ok:
        print("Setup complete. Configure .env and run the bot.\n")
    else:
        print("Install missing dependencies first.\n")

if __name__ == "__main__":
    main()
