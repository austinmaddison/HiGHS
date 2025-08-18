"""
Utility functions and classes for the build system
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Logger:
    """Centralized logging functionality"""
    
    @staticmethod
    def info(message: str):
        """Print info message with color"""
        print(f"{Colors.OKBLUE}[INFO]{Colors.ENDC} {message}")
    
    @staticmethod
    def success(message: str):
        """Print success message with color"""
        print(f"{Colors.OKGREEN}[SUCCESS]{Colors.ENDC} {message}")
    
    @staticmethod
    def warning(message: str):
        """Print warning message with color"""
        print(f"{Colors.WARNING}[WARNING]{Colors.ENDC} {message}")
    
    @staticmethod
    def error(message: str):
        """Print error message with color"""
        print(f"{Colors.FAIL}[ERROR]{Colors.ENDC} {message}")
    
    @staticmethod
    def header(message: str):
        """Print header message with color"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}=== {message} ==={Colors.ENDC}")


class CommandRunner:
    """Handles command execution with proper logging and error handling"""
    
    def __init__(self, cwd: Optional[Path] = None):
        self.cwd = cwd
    
    def run(self, command: List[str], cwd: Optional[Path] = None, 
            check: bool = True, env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
        """Run a command with proper error handling"""
        cmd_str = ' '.join(command)
        Logger.info(f"Running: {cmd_str}")
        
        # Merge environment variables
        full_env = os.environ.copy()
        if env:
            full_env.update(env)
        
        working_dir = cwd or self.cwd
        
        try:
            result = subprocess.run(
                command,
                cwd=working_dir,
                check=check,
                capture_output=False,
                text=True,
                env=full_env
            )
            return result
        except subprocess.CalledProcessError as e:
            Logger.error(f"Command failed: {cmd_str}")
            Logger.error(f"Exit code: {e.returncode}")
            if check:
                raise
            return e
