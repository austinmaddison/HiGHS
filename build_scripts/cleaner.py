"""
Cleanup utilities for build artifacts
"""

import shutil
from pathlib import Path
from typing import Dict

from .utils import Logger


class BuildCleaner:
    """Handles cleanup of build artifacts and directories"""
    
    def __init__(self, project_dir: Path, presets: Dict):
        self.project_dir = project_dir
        self.presets = presets
    
    def cleanup_all(self):
        """Clean up all build artifacts"""
        Logger.header("Cleaning Up")
        
        # Remove root-level CMake artifacts from project directory
        artifacts = ["CMakeCache.txt", "CMakeFiles"]
        for artifact in artifacts:
            path = self.project_dir / artifact
            if path.exists():
                Logger.info(f"Removing {artifact}")
                if path.is_file():
                    path.unlink()
                else:
                    shutil.rmtree(path)
        
        # Remove all build directories (both old and new structure)
        build_root = self.project_dir / "build"
        if build_root.exists():
            Logger.info(f"Removing build directory: build/")
            shutil.rmtree(build_root)
            
        # Remove old-style build directories
        for preset in self.presets.get("configurePresets", []):
            binary_dir = preset.get("binaryDir", "")
            if binary_dir.startswith("${sourceDir}/build/"):
                build_dir = Path(binary_dir.replace("${sourceDir}/", ""))
                build_path = self.project_dir / build_dir
                if build_path.exists():
                    Logger.info(f"Removing old build directory: {build_dir}")
                    shutil.rmtree(build_path)
        
        Logger.success("Cleanup completed")
    
    def clean_platforms(self, platforms: list[str]):
        """Clean build directories for specific platforms"""
        for platform in platforms:
            build_dir = self.project_dir / "build" / platform
            if build_dir.exists():
                Logger.info(f"Cleaning previous build: {build_dir.name}")
                shutil.rmtree(build_dir)
