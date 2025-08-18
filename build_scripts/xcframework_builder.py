"""
XCFramework creation for iOS builds
"""

import platform
import shutil
import subprocess
from pathlib import Path
from typing import List

from .utils import Colors, Logger


class XCFrameworkBuilder:
    """Handles creation of iOS XCFramework bundles"""
    
    def __init__(self, project_dir: Path, build_config: str):
        self.project_dir = project_dir
        self.build_config = build_config
    
    def create_xcframework(self, ios_platforms: List[str]) -> bool:
        """Create XCFramework for iOS combining device and simulator architectures"""
        Logger.header("Creating HiGHS XCFramework for iOS")
        
        # Check if we're on macOS
        if platform.system() != "Darwin":
            Logger.error("XCFramework creation requires macOS")
            return False
        
        xcframework_dir = Path(self.project_dir / "build" / "ios-xcframework")
        xcframework_dir.mkdir(parents=True, exist_ok=True)
        
        # Define library paths using the configured build type
        library_paths = []
        for ios_platform in ios_platforms:
            lib_path = (self.project_dir / "build" / ios_platform / self.build_config / "lib" / "libhighs.a").resolve()
            library_paths.append(lib_path)
        
        # Check if all libraries exist
        missing_libs = [path for path in library_paths if not path.exists()]
        if missing_libs:
            Logger.error("Missing library files:")
            for lib in missing_libs:
                Logger.error(f"  {lib}")
            return False
        
        xcframework_path = xcframework_dir / "highs.xcframework"
        
        # Remove existing XCFramework if it exists
        if xcframework_path.exists():
            Logger.info(f"Removing existing XCFramework: {xcframework_path}")
            shutil.rmtree(xcframework_path)
        
        try:
            # Build xcodebuild command
            xcodebuild_cmd = ["xcodebuild", "-create-xcframework"]
            
            # Add all library paths
            for lib_path in library_paths:
                xcodebuild_cmd.extend(["-library", str(lib_path)])
            
            # Add output path
            xcodebuild_cmd.extend(["-output", str(xcframework_path)])
            
            # Execute the command
            Logger.info(f"Creating XCFramework with libraries: {[lib.name for lib in library_paths]}")
            result = subprocess.run(xcodebuild_cmd, capture_output=True, text=True, check=True)
            
            Logger.success("XCFramework created successfully!")
            Logger.info(f"XCFramework saved to: {xcframework_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            Logger.error("Failed to create XCFramework")
            if e.stderr:
                Logger.error(f"xcodebuild error: {e.stderr}")
            return False
        except FileNotFoundError:
            Logger.error("xcodebuild not found. Make sure Xcode is installed.")
            return False
