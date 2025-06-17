#!/usr/bin/env python3
"""
Automated Environment Setup Script
Configures reVoAgent for development, production, or demo environments
"""

import os
import sys
import json
import subprocess
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional
import argparse

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnvironmentSetup:
    """Automated environment setup for reVoAgent"""
    
    def __init__(self, mode: str = 'development'):
        self.mode = mode
        self.root_dir = Path(__file__).parent.parent
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load environment configuration"""
        config_file = self.root_dir / 'config' / f'{self.mode}.json'
        
        # Default configurations
        default_configs = {
            'development': {
                'frontend_port': 12000,
                'backend_port': 12001,
                'database': 'sqlite',
                'memory_backend': 'in_memory',
                'auth_required': False,
                'debug': True,
                'hot_reload': True,
                'cors_origins': ['*'],
                'log_level': 'DEBUG'
            },
            'production': {
                'frontend_port': 12000,
                'backend_port': 12001,
                'database': 'postgresql',
                'memory_backend': 'cognee',
                'auth_required': True,
                'debug': False,
                'hot_reload': False,
                'cors_origins': ['https://your-domain.com'],
                'log_level': 'INFO'
            },
            'demo': {
                'frontend_port': 12000,
                'backend_port': 12001,
                'database': 'sqlite',
                'memory_backend': 'in_memory',
                'auth_required': False,
                'debug': False,
                'hot_reload': False,
                'cors_origins': ['*'],
                'log_level': 'INFO'
            }
        }
        
        if config_file.exists():
            with open(config_file) as f:
                return json.load(f)
        
        return default_configs.get(self.mode, default_configs['development'])
    
    def setup(self) -> bool:
        """Run complete environment setup"""
        logger.info(f"Setting up reVoAgent for {self.mode} environment...")
        
        try:
            # Create necessary directories
            self._create_directories()
            
            # Install dependencies
            self._install_dependencies()
            
            # Configure environment files
            self._configure_environment()
            
            # Setup database
            self._setup_database()
            
            # Configure frontend
            self._configure_frontend()
            
            # Configure backend
            self._configure_backend()
            
            # Setup Docker if needed
            if self.mode in ['production', 'demo']:
                self._setup_docker()
            
            # Create startup scripts
            self._create_startup_scripts()
            
            # Validate setup
            self._validate_setup()
            
            logger.info(f"✅ Environment setup completed successfully for {self.mode} mode!")
            self._print_next_steps()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Environment setup failed: {e}")
            return False
    
    def _create_directories(self):
        """Create necessary directories"""
        logger.info("Creating directories...")
        
        directories = [
            'data',
            'logs',
            'temp',
            'config',
            'models',
            'scripts',
            'tests/results',
            'frontend/dist',
            'src/packages/memory',
            'monitoring'
        ]
        
        for dir_path in directories:
            full_path = self.root_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {full_path}")
    
    def _install_dependencies(self):
        """Install Python and Node.js dependencies"""
        logger.info("Installing dependencies...")
        
        # Install Python dependencies
        requirements_files = [
            'requirements.txt',
            'requirements-working.txt'
        ]
        
        for req_file in requirements_files:
            req_path = self.root_dir / req_file
            if req_path.exists():
                logger.info(f"Installing Python dependencies from {req_file}...")
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', '-r', str(req_path)
                ], check=True)
        
        # Install Node.js dependencies
        frontend_dir = self.root_dir / 'frontend'
        if (frontend_dir / 'package.json').exists():
            logger.info("Installing Node.js dependencies...")
            subprocess.run(['npm', 'install'], cwd=frontend_dir, check=True)
    
    def _configure_environment(self):
        """Configure environment variables and files"""
        logger.info("Configuring environment...")
        
        # Create .env file
        env_content = f"""
# reVoAgent Environment Configuration - {self.mode.upper()}
REVOAGENT_MODE={self.mode}
REVOAGENT_DEBUG={str(self.config['debug']).lower()}
REVOAGENT_LOG_LEVEL={self.config['log_level']}

# Ports
FRONTEND_PORT={self.config['frontend_port']}
BACKEND_PORT={self.config['backend_port']}

# Database
DATABASE_TYPE={self.config['database']}
DATABASE_URL=sqlite:///data/revoagent.db

# Memory Backend
MEMORY_BACKEND={self.config['memory_backend']}

# Authentication
AUTH_REQUIRED={str(self.config['auth_required']).lower()}

# CORS
CORS_ORIGINS={','.join(self.config['cors_origins'])}

# Paths
PYTHONPATH=src
REVOAGENT_CONFIG=config/config.yaml
"""
        
        env_file = self.root_dir / '.env'
        with open(env_file, 'w') as f:
            f.write(env_content.strip())
        
        logger.debug(f"Created .env file: {env_file}")
    
    def _setup_database(self):
        """Setup database based on configuration"""
        logger.info("Setting up database...")
        
        if self.config['database'] == 'sqlite':
            # Create SQLite database directory
            db_dir = self.root_dir / 'data'
            db_dir.mkdir(exist_ok=True)
            
            # Create empty database file
            db_file = db_dir / 'revoagent.db'
            if not db_file.exists():
                db_file.touch()
            
            logger.info(f"SQLite database ready: {db_file}")
        
        elif self.config['database'] == 'postgresql':
            logger.info("PostgreSQL configuration detected. Please ensure PostgreSQL is running.")
            # Note: In production, this would include actual database setup
    
    def _configure_frontend(self):
        """Configure frontend build and settings"""
        logger.info("Configuring frontend...")
        
        frontend_dir = self.root_dir / 'frontend'
        
        # Update vite.config.ts with correct ports
        vite_config = frontend_dir / 'vite.config.ts'
        if vite_config.exists():
            with open(vite_config, 'r') as f:
                content = f.read()
            
            # Update ports in vite config
            content = content.replace('port: 12000', f'port: {self.config["frontend_port"]}')
            content = content.replace('target: \'http://localhost:12001\'', 
                                    f'target: \'http://localhost:{self.config["backend_port"]}\'')
            content = content.replace('target: \'ws://localhost:12001\'', 
                                    f'target: \'ws://localhost:{self.config["backend_port"]}\'')
            
            with open(vite_config, 'w') as f:
                f.write(content)
            
            logger.debug("Updated vite.config.ts")
        
        # Create environment-specific frontend config
        frontend_env = frontend_dir / '.env'
        with open(frontend_env, 'w') as f:
            f.write(f"""
VITE_APP_MODE={self.mode}
VITE_API_URL=http://localhost:{self.config['backend_port']}
VITE_WS_URL=ws://localhost:{self.config['backend_port']}
VITE_DEBUG={str(self.config['debug']).lower()}
""".strip())
        
        # Build frontend for production/demo
        if self.mode in ['production', 'demo']:
            logger.info("Building frontend...")
            subprocess.run(['npm', 'run', 'build'], cwd=frontend_dir, check=True)
    
    def _configure_backend(self):
        """Configure backend settings"""
        logger.info("Configuring backend...")
        
        # Update main.py with correct port
        main_py = self.root_dir / 'src' / 'backend' / 'main.py'
        if main_py.exists():
            with open(main_py, 'r') as f:
                content = f.read()
            
            # Update port in uvicorn.run
            content = content.replace('port=8000', f'port={self.config["backend_port"]}')
            content = content.replace('port=12001', f'port={self.config["backend_port"]}')
            
            with open(main_py, 'w') as f:
                f.write(content)
            
            logger.debug("Updated backend main.py")
        
        # Create backend configuration file
        config_dir = self.root_dir / 'config'
        config_file = config_dir / 'config.yaml'
        
        config_content = f"""
# reVoAgent Configuration - {self.mode.upper()}
mode: {self.mode}
debug: {self.config['debug']}

server:
  host: "0.0.0.0"
  port: {self.config['backend_port']}
  cors_origins: {self.config['cors_origins']}

database:
  type: {self.config['database']}
  url: "sqlite:///data/revoagent.db"

memory:
  backend: {self.config['memory_backend']}
  max_entries: 10000

auth:
  required: {self.config['auth_required']}
  secret_key: "your-secret-key-change-in-production"

logging:
  level: {self.config['log_level']}
  file: "logs/revoagent.log"
"""
        
        with open(config_file, 'w') as f:
            f.write(config_content.strip())
        
        logger.debug(f"Created config file: {config_file}")
    
    def _setup_docker(self):
        """Setup Docker configuration"""
        logger.info("Setting up Docker configuration...")
        
        # Update docker-compose.yml ports
        docker_compose = self.root_dir / 'docker-compose.yml'
        if docker_compose.exists():
            with open(docker_compose, 'r') as f:
                content = f.read()
            
            # Update port mappings
            content = content.replace('"8000:8000"', f'"{self.config["backend_port"]}:{self.config["backend_port"]}"')
            content = content.replace('"3000:3000"', f'"{self.config["frontend_port"]}:{self.config["frontend_port"]}"')
            
            with open(docker_compose, 'w') as f:
                f.write(content)
            
            logger.debug("Updated docker-compose.yml")
    
    def _create_startup_scripts(self):
        """Create startup scripts for different environments"""
        logger.info("Creating startup scripts...")
        
        scripts_dir = self.root_dir / 'scripts'
        
        # Development startup script
        dev_script = scripts_dir / 'start_dev.sh'
        with open(dev_script, 'w') as f:
            f.write(f"""#!/bin/bash
# Development startup script for reVoAgent

set -e

echo "🚀 Starting reVoAgent in development mode..."

# Set environment
export REVOAGENT_MODE=development
export PYTHONPATH=src

# Start backend in background
echo "Starting backend on port {self.config['backend_port']}..."
cd src/backend && python main.py &
BACKEND_PID=$!

# Start frontend
echo "Starting frontend on port {self.config['frontend_port']}..."
cd frontend && npm run dev &
FRONTEND_PID=$!

# Wait for interrupt
echo "✅ reVoAgent is running!"
echo "Frontend: http://localhost:{self.config['frontend_port']}"
echo "Backend: http://localhost:{self.config['backend_port']}"
echo "Press Ctrl+C to stop..."

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
""")
        
        dev_script.chmod(0o755)
        
        # Production startup script
        prod_script = scripts_dir / 'start_prod.sh'
        with open(prod_script, 'w') as f:
            f.write(f"""#!/bin/bash
# Production startup script for reVoAgent

set -e

echo "🚀 Starting reVoAgent in production mode..."

# Set environment
export REVOAGENT_MODE=production
export PYTHONPATH=src

# Start with Docker Compose
docker-compose up -d

echo "✅ reVoAgent is running in production mode!"
echo "Frontend: http://localhost:{self.config['frontend_port']}"
echo "Backend: http://localhost:{self.config['backend_port']}"
""")
        
        prod_script.chmod(0o755)
        
        # Quick start script
        quick_script = scripts_dir / 'quick_start.py'
        with open(quick_script, 'w') as f:
            f.write(f"""#!/usr/bin/env python3
\"\"\"
Quick start script for reVoAgent
Automatically detects environment and starts appropriate services
\"\"\"

import os
import sys
import subprocess
import time
from pathlib import Path

def main():
    root_dir = Path(__file__).parent.parent
    mode = os.getenv('REVOAGENT_MODE', '{self.mode}')
    
    print(f"🚀 Quick starting reVoAgent in {{mode}} mode...")
    
    if mode == 'development':
        # Start development servers
        backend_cmd = [sys.executable, 'src/backend/main.py']
        frontend_cmd = ['npm', 'run', 'dev']
        
        print("Starting backend...")
        backend_proc = subprocess.Popen(backend_cmd, cwd=root_dir)
        
        time.sleep(3)  # Give backend time to start
        
        print("Starting frontend...")
        frontend_proc = subprocess.Popen(frontend_cmd, cwd=root_dir / 'frontend')
        
        try:
            print("✅ reVoAgent is running!")
            print(f"Frontend: http://localhost:{self.config['frontend_port']}")
            print(f"Backend: http://localhost:{self.config['backend_port']}")
            print("Press Ctrl+C to stop...")
            
            backend_proc.wait()
        except KeyboardInterrupt:
            print("\\nStopping services...")
            backend_proc.terminate()
            frontend_proc.terminate()
    
    elif mode == 'production':
        # Use Docker Compose
        subprocess.run(['docker-compose', 'up', '-d'], cwd=root_dir)
        print("✅ reVoAgent started in production mode!")
    
    else:
        print(f"Unknown mode: {{mode}}")
        sys.exit(1)

if __name__ == '__main__':
    main()
""")
        
        quick_script.chmod(0o755)
        
        logger.debug("Created startup scripts")
    
    def _validate_setup(self):
        """Validate the setup"""
        logger.info("Validating setup...")
        
        # Check required files
        required_files = [
            '.env',
            'config/config.yaml',
            'frontend/package.json',
            'src/backend/main.py',
            'scripts/quick_start.py'
        ]
        
        for file_path in required_files:
            full_path = self.root_dir / file_path
            if not full_path.exists():
                raise FileNotFoundError(f"Required file missing: {file_path}")
        
        # Check Python imports
        try:
            import fastapi
            import uvicorn
        except ImportError as e:
            raise ImportError(f"Required Python package missing: {e}")
        
        # Check Node.js dependencies (if frontend exists)
        frontend_dir = self.root_dir / 'frontend'
        if (frontend_dir / 'package.json').exists():
            node_modules = frontend_dir / 'node_modules'
            if not node_modules.exists():
                raise FileNotFoundError("Node.js dependencies not installed")
        
        logger.info("✅ Setup validation passed")
    
    def _print_next_steps(self):
        """Print next steps for the user"""
        print(f"""
🎉 reVoAgent setup completed for {self.mode} mode!

Next steps:
1. Start the application:
   ./scripts/quick_start.py
   
   Or manually:
   - Backend: cd src/backend && python main.py
   - Frontend: cd frontend && npm run dev

2. Access the application:
   - Frontend: http://localhost:{self.config['frontend_port']}
   - Backend API: http://localhost:{self.config['backend_port']}/docs

3. Configuration files created:
   - .env (environment variables)
   - config/config.yaml (application config)
   - scripts/start_dev.sh (development startup)
   - scripts/start_prod.sh (production startup)

4. For production deployment:
   ./scripts/start_prod.sh

Happy coding! 🚀
""")


def main():
    parser = argparse.ArgumentParser(description='Setup reVoAgent environment')
    parser.add_argument('--mode', choices=['development', 'production', 'demo'], 
                       default='development', help='Environment mode')
    parser.add_argument('--force', action='store_true', 
                       help='Force setup even if files exist')
    
    args = parser.parse_args()
    
    setup = EnvironmentSetup(args.mode)
    success = setup.setup()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()