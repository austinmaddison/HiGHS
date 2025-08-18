"""
Main build orchestrator that coordinates all build operations
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

from .cleaner import BuildCleaner
from .config import ConfigManager
from .library_extractor import LibraryExtractor
from .platform_builders import PlatformBuilderFactory
from .utils import Colors, CommandRunner, Logger
from .xcframework_builder import XCFrameworkBuilder


class BuildOrchestrator:
    """Main class that orchestrates all build operations"""
    
    def __init__(self, root_dir: Optional[str] = './highs_patched', 
                 extract_libs: bool = False, build_config: str = "Release"):
        # Set up paths
        self.script_dir = Path(__file__).parent.parent  # Go up from build/ to root
        self.project_dir = Path(root_dir) if root_dir else self.script_dir / 'highs_patched'
        self.extract_libs = extract_libs
        self.build_config = build_config
        
        # Initialize components
        self.config = ConfigManager(self.project_dir, self.script_dir)
        self.runner = CommandRunner(self.project_dir)
        self.cleaner = BuildCleaner(self.project_dir, self.config.presets)
        self.library_extractor = LibraryExtractor(self.project_dir)
        self.xcframework_builder = XCFrameworkBuilder(self.project_dir, self.build_config)
        self.platform_builders = PlatformBuilderFactory.create_builders(
            self.config, self.runner, self.build_config
        )
    
    def set_android_ndk_path(self, ndk_path: str) -> bool:
        """Set the Android NDK path"""
        return self.config.set_android_ndk_path(ndk_path)
    
    def cleanup(self):
        """Clean up build artifacts"""
        self.cleaner.cleanup_all()
    
    def get_available_platforms(self) -> List[str]:
        """Get list of available build platforms"""
        return self.config.get_available_platforms()
    
    def build_single_platform(self, platform: str) -> bool:
        """Build a single platform"""
        Logger.header(f"Building {platform}")
        
        # Find the appropriate builder
        builder = PlatformBuilderFactory.get_builder_for_preset(self.platform_builders, platform)
        if not builder:
            Logger.error(f"No builder found for platform: {platform}")
            return False
        
        # Configure the build
        if not builder.configure(platform):
            return False
        
        # Build the platform
        if not builder.build(platform):
            return False
        
        # Extract libraries if requested
        if self.extract_libs:
            if not self.library_extractor.extract_libraries(platform):
                Logger.warning(f"Library extraction failed for {platform}")
        
        return True
    
    def build_multiple_platforms(self, platforms: Optional[List[str]] = None) -> Dict[str, bool]:
        """Build multiple platforms"""
        if platforms is None:
            platforms = self.get_available_platforms()
            platforms = self._filter_available_platforms(platforms)
        
        if not platforms:
            Logger.error("No platforms to build")
            return {}
        
        Logger.header("Building Multiple Platforms")
        Logger.info(f"Platforms to build: {', '.join(platforms)}")
        
        results = {}
        
        for platform in platforms:
            success = self.build_single_platform(platform)
            results[platform] = success
            
            if not success:
                Logger.warning(f"Build failed for {platform}, continuing with next platform")
        
        self._print_build_summary(results)
        return results
    
    def build_ios_xcframework(self) -> bool:
        """Build iOS XCFramework bundle (combines device + simulators)"""
        ios_platforms = ["ios-arm64", "ios-simulator-arm64"]
        
        Logger.header("Building HiGHS XCFramework for iOS")
        self.cleaner.clean_platforms(ios_platforms)
        
        # Build all iOS architectures first
        results = self.build_multiple_platforms(ios_platforms)
        all_success = all(results.values())
        
        if not all_success:
            Logger.error("iOS builds failed, cannot create XCFramework")
            return False
        
        # Create the XCFramework
        return self.xcframework_builder.create_xcframework(ios_platforms)
    
    def build_android_all(self) -> bool:
        """Build all Android variants"""
        android_platforms = ["android-arm64", "android-arm32", "android-x86", "android-x64"]
        
        Logger.header("Building HiGHS for Android")
        
        if not self.config.android_ndk_path:
            Logger.error("Android NDK path not set.")
            Logger.info("Use: python build.py android --ndk-path /path/to/ndk")
            return False
        
        self.cleaner.clean_platforms(android_platforms)
        
        results = self.build_multiple_platforms(android_platforms)
        all_success = all(results.values())
        
        if all_success:
            Logger.success("All Android builds completed successfully!")
        else:
            Logger.error("Some Android builds failed")
        
        return all_success
    
    def show_config(self):
        """Show current build configuration"""
        Logger.header("Build Configuration")
        
        print(f"Script directory: {self.script_dir}")
        print(f"Project directory: {self.project_dir}")
        print(f"CMake presets: {self.config.presets_file}")
        print(f"Environment file: {self.config.env_file}")
        print(f"Build configuration: {self.build_config}")
        print(f"Extract libraries: {self.extract_libs}")
        
        if self.config.android_ndk_path:
            print(f"{Colors.OKGREEN}Android NDK: {self.config.android_ndk_path}{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}Android NDK: Not configured{Colors.ENDC}")
            print("  Use: python build.py build android --ndk-path /path/to/ndk")
        
        # Show available platforms
        print(f"\nAvailable platforms:")
        platforms = self.get_available_platforms()
        android_platforms = [p for p in platforms if p.startswith("android-")]
        other_platforms = [p for p in platforms if not p.startswith("android-")]
        
        for platform in other_platforms:
            print(f"  - {platform}")
        
        for platform in android_platforms:
            if self.config.android_ndk_path:
                print(f"  - {Colors.OKGREEN}{platform}{Colors.ENDC}")
            else:
                print(f"  - {Colors.WARNING}{platform} (requires NDK path){Colors.ENDC}")
    
    def _filter_available_platforms(self, platforms: List[str]) -> List[str]:
        """Filter platforms based on availability and configuration"""
        # Filter out Android platforms if NDK path is not set
        if not self.config.android_ndk_path:
            android_platforms = [p for p in platforms if p.startswith("android-")]
            if android_platforms:
                Logger.warning("Android NDK path not set. Skipping Android platforms:")
                for p in android_platforms:
                    Logger.warning(f"  - {p}")
                Logger.info("Use --ndk-path to include Android builds")
                platforms = [p for p in platforms if not p.startswith("android-")]

        # Note: iOS platforms are now included in 'all' builds
        # They can be built individually or as XCFramework bundles using 'python build.py build ios'
        
        return platforms

    def _print_build_summary(self, results: Dict[str, bool]):
        """Print a summary of build results"""
        Logger.header("Build Summary")
        for platform, success in results.items():
            status = "SUCCESS" if success else "FAILED"
            color = Colors.OKGREEN if success else Colors.FAIL
            print(f"{color}{platform}: {status}{Colors.ENDC}")
        
        successful_builds = sum(1 for success in results.values() if success)
        total_builds = len(results)
        
        if successful_builds == total_builds:
            Logger.success(f"All {total_builds} builds completed successfully!")
        else:
            Logger.warning(f"{successful_builds}/{total_builds} builds completed successfully")
