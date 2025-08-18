"""
Configuration management for the build system
"""

import json
import sys
from pathlib import Path
from typing import Dict, Optional

from .utils import Logger


class ConfigManager:
    """Manages build configuration and presets"""
    
    def __init__(self, project_dir: Path, script_dir: Path):
        self.project_dir = project_dir
        self.script_dir = script_dir
        self.presets_file = self.project_dir / "CMakePresets.json"
        self.env_file = self.script_dir / ".env"
        self._presets = None
        self._android_ndk_path = None
    
    @property
    def presets(self) -> Dict:
        """Get CMake presets, loading if necessary"""
        if self._presets is None:
            self._presets = self._load_presets()
        return self._presets
    
    @property
    def android_ndk_path(self) -> Optional[str]:
        """Get Android NDK path, loading if necessary"""
        if self._android_ndk_path is None:
            self._android_ndk_path = self._load_android_ndk_path()
        return self._android_ndk_path
    
    def _load_presets(self) -> Dict:
        """Load CMake presets from JSON file"""
        try:
            with open(self.presets_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            Logger.error(f"CMakePresets.json not found at {self.presets_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            Logger.error(f"Invalid JSON in CMakePresets.json: {e}")
            sys.exit(1)
    
    def _load_android_ndk_path(self) -> Optional[str]:
        """Load Android NDK path from .env file"""
        try:
            if self.env_file.exists():
                with open(self.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('ANDROID_NDK_PATH='):
                            ndk_path = line.split('=', 1)[1].strip('"\'')
                            if ndk_path and Path(ndk_path).exists():
                                return ndk_path
        except (FileNotFoundError, IOError):
            pass
        return None
    
    def set_android_ndk_path(self, ndk_path: str) -> bool:
        """Set and save Android NDK path"""
        ndk_path_obj = Path(ndk_path)
        
        if not ndk_path_obj.exists():
            Logger.error(f"Android NDK path does not exist: {ndk_path}")
            return False
        
        # Check if this looks like a valid NDK installation
        toolchain_cmake = ndk_path_obj / "build" / "cmake" / "android.toolchain.cmake"
        if not toolchain_cmake.exists():
            Logger.error(f"Invalid Android NDK path: {ndk_path}")
            Logger.error("Expected to find: build/cmake/android.toolchain.cmake")
            return False
        
        self._android_ndk_path = str(ndk_path_obj.resolve())
        self._save_android_ndk_path(self._android_ndk_path)
        Logger.success(f"Android NDK path set to: {self._android_ndk_path}")
        Logger.info(f"NDK path saved to: {self.env_file}")
        return True
    
    def _save_android_ndk_path(self, ndk_path: str):
        """Save Android NDK path to .env file"""
        env_vars = {}
        
        # Read existing .env file if it exists
        if self.env_file.exists():
            try:
                with open(self.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip('"\'')
            except (FileNotFoundError, IOError):
                pass
        
        # Update the NDK path
        env_vars['ANDROID_NDK_PATH'] = ndk_path
        
        # Write back to .env file
        with open(self.env_file, 'w') as f:
            f.write("# HiGHS Build Configuration\n")
            f.write("# Android NDK path for cross-compilation\n")
            for key, value in env_vars.items():
                f.write(f'{key}="{value}"\n')
    
    def get_available_platforms(self) -> list[str]:
        """Get list of available build platforms from presets"""
        return [preset["name"] for preset in self.presets.get("configurePresets", [])]
    
    def get_android_env(self) -> Dict[str, str]:
        """Get environment variables needed for Android builds"""
        if not self.android_ndk_path:
            raise ValueError("Android NDK path not set. Use set_android_ndk_path() first.")
        
        return {
            "ANDROID_NDK_ROOT": self.android_ndk_path,
            "ANDROID_NDK_HOME": self.android_ndk_path  # Some tools use this alternative name
        }
