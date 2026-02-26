"""
Redis Installation Helper Script

Helps users install and configure Redis for the caching layer.
"""
import subprocess
import sys
import platform
import os


def check_redis_installed():
    """Check if Redis is already installed"""
    try:
        result = subprocess.run(
            ['redis-cli', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✅ Redis is already installed: {result.stdout.strip()}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    print("❌ Redis is not installed")
    return False


def check_redis_running():
    """Check if Redis server is running"""
    try:
        result = subprocess.run(
            ['redis-cli', 'ping'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and 'PONG' in result.stdout:
            print("✅ Redis server is running")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    print("❌ Redis server is not running")
    return False


def check_python_redis():
    """Check if Python Redis package is installed"""
    try:
        import redis
        print(f"✅ Python redis package is installed (version {redis.__version__})")
        return True
    except ImportError:
        print("❌ Python redis package is not installed")
        return False


def install_python_redis():
    """Install Python Redis package"""
    print("\n📦 Installing Python redis package...")
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', 'redis[hiredis]==5.0.1'],
            check=True
        )
        print("✅ Python redis package installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Python redis package: {e}")
        return False


def print_installation_instructions():
    """Print platform-specific installation instructions"""
    system = platform.system()
    
    print("\n" + "=" * 80)
    print("REDIS SERVER INSTALLATION INSTRUCTIONS")
    print("=" * 80)
    
    if system == "Windows":
        print("\n🪟 Windows Installation Options:")
        print("\n1. Using Docker (Recommended - Easiest):")
        print("   docker run -d -p 6379:6379 --name redis redis:latest")
        
        print("\n2. Using Chocolatey:")
        print("   choco install redis-64")
        
        print("\n3. Using WSL (Windows Subsystem for Linux):")
        print("   wsl --install")
        print("   wsl")
        print("   sudo apt-get update")
        print("   sudo apt-get install redis-server")
        print("   redis-server")
        
        print("\n4. Manual Installation:")
        print("   Download from: https://github.com/microsoftarchive/redis/releases")
        print("   Extract to C:\\Program Files\\Redis")
        print("   Run redis-server.exe")
    
    elif system == "Linux":
        print("\n🐧 Linux Installation:")
        print("   sudo apt-get update")
        print("   sudo apt-get install redis-server")
        print("   sudo systemctl start redis-server")
        print("   sudo systemctl enable redis-server")
    
    elif system == "Darwin":  # macOS
        print("\n🍎 macOS Installation:")
        print("   brew install redis")
        print("   brew services start redis")
    
    else:
        print(f"\n❓ Unknown system: {system}")
        print("   Please refer to: https://redis.io/download")
    
    print("\n" + "=" * 80)


def update_env_file():
    """Update .env file with Redis configuration"""
    env_file = ".env"
    env_example = ".env.example"
    
    # Check if .env exists
    if not os.path.exists(env_file):
        if os.path.exists(env_example):
            print(f"\n📝 Creating .env from .env.example...")
            with open(env_example, 'r') as f:
                content = f.read()
            with open(env_file, 'w') as f:
                f.write(content)
            print("✅ .env file created")
        else:
            print("⚠️  .env.example not found, creating minimal .env...")
            with open(env_file, 'w') as f:
                f.write("# Redis Cache\n")
                f.write("REDIS_URL=redis://localhost:6379/0\n")
                f.write("CACHE_ENABLED=True\n")
            print("✅ Minimal .env file created")
    else:
        # Check if Redis config exists in .env
        with open(env_file, 'r') as f:
            content = f.read()
        
        if 'REDIS_URL' not in content:
            print(f"\n📝 Adding Redis configuration to .env...")
            with open(env_file, 'a') as f:
                f.write("\n# Redis Cache\n")
                f.write("REDIS_URL=redis://localhost:6379/0\n")
                f.write("CACHE_ENABLED=True\n")
            print("✅ Redis configuration added to .env")
        else:
            print("✅ Redis configuration already exists in .env")


def main():
    """Main installation helper"""
    print("=" * 80)
    print("REDIS INSTALLATION HELPER")
    print("=" * 80)
    
    print("\n🔍 Checking Redis installation status...\n")
    
    # Check Python redis package
    python_redis_installed = check_python_redis()
    
    # Check Redis server
    redis_installed = check_redis_installed()
    redis_running = False
    
    if redis_installed:
        redis_running = check_redis_running()
    
    # Summary
    print("\n" + "=" * 80)
    print("INSTALLATION STATUS")
    print("=" * 80)
    print(f"Python redis package: {'✅ Installed' if python_redis_installed else '❌ Not installed'}")
    print(f"Redis server:         {'✅ Installed' if redis_installed else '❌ Not installed'}")
    print(f"Redis running:        {'✅ Running' if redis_running else '❌ Not running'}")
    
    # Install Python package if needed
    if not python_redis_installed:
        print("\n" + "=" * 80)
        response = input("\n📦 Install Python redis package? (y/n): ").lower()
        if response == 'y':
            install_python_redis()
    
    # Show Redis server installation instructions if needed
    if not redis_installed or not redis_running:
        print_installation_instructions()
    
    # Update .env file
    print("\n" + "=" * 80)
    response = input("\n📝 Update .env file with Redis configuration? (y/n): ").lower()
    if response == 'y':
        update_env_file()
    
    # Final instructions
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    
    if not python_redis_installed:
        print("1. Install Python redis package:")
        print("   pip install redis[hiredis]==5.0.1")
    
    if not redis_installed:
        print("2. Install Redis server (see instructions above)")
    
    if redis_installed and not redis_running:
        print("2. Start Redis server:")
        if platform.system() == "Windows":
            print("   redis-server")
        else:
            print("   sudo systemctl start redis-server")
    
    print("\n3. Verify Redis is working:")
    print("   redis-cli ping")
    print("   (Should return: PONG)")
    
    print("\n4. Run cache tests:")
    print("   pytest tests/test_cache_manager.py -v")
    
    print("\n5. Run demo script:")
    print("   python demo_quick_mode_cache.py <tenant_id>")
    
    print("\n6. Start the application:")
    print("   python -m uvicorn src.main:app --reload")
    
    print("\n" + "=" * 80)
    print("📚 For detailed instructions, see: REDIS_SETUP.md")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Installation helper cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
