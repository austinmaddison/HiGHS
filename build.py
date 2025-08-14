#!/usr/bin/env python3
"""
Cross-platform build script for HiGHS
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Optional, Union


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


class BuildSystem:
    """Main build system class"""
    
    def __init__(self, root_dir: Optional[str] = None):
        self.root_dir = Path(root_dir) if root_dir else Path(__file__).parent
        self.presets_file = self.root_dir / "CMakePresets.json"
        self.config_file = self.root_dir / ".build_config.json"
        self.presets = self._load_presets()
        self.android_ndk_path = self._load_android_ndk_path()
        
    def _load_presets(self) -> Dict:
        """Load CMake presets from JSON file"""
        try:
            with open(self.presets_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self._print_error(f"CMakePresets.json not found at {self.presets_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            self._print_error(f"Invalid JSON in CMakePresets.json: {e}")
            sys.exit(1)
    
    def _load_android_ndk_path(self) -> Optional[str]:
        """Load Android NDK path from config file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    ndk_path = config.get('android_ndk_path')
                    if ndk_path and Path(ndk_path).exists():
                        return ndk_path
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return None
    
    def _save_android_ndk_path(self, ndk_path: str):
        """Save Android NDK path to config file"""
        config = {}
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            except json.JSONDecodeError:
                config = {}
        
        config['android_ndk_path'] = ndk_path
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def _print_info(self, message: str):
        """Print info message with color"""
        print(f"{Colors.OKBLUE}[INFO]{Colors.ENDC} {message}")
    
    def _print_success(self, message: str):
        """Print success message with color"""
        print(f"{Colors.OKGREEN}[SUCCESS]{Colors.ENDC} {message}")
    
    def _print_warning(self, message: str):
        """Print warning message with color"""
        print(f"{Colors.WARNING}[WARNING]{Colors.ENDC} {message}")
    
    def _print_error(self, message: str):
        """Print error message with color"""
        print(f"{Colors.FAIL}[ERROR]{Colors.ENDC} {message}")
    
    def _print_header(self, message: str):
        """Print header message with color"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}=== {message} ==={Colors.ENDC}")
    
    def _run_command(self, command: List[str], cwd: Optional[Path] = None, 
                     check: bool = True, env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
        """Run a command with proper error handling"""
        cmd_str = ' '.join(command)
        self._print_info(f"Running: {cmd_str}")
        
        # Merge environment variables
        full_env = os.environ.copy()
        if env:
            full_env.update(env)
        
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.root_dir,
                check=check,
                capture_output=False,
                text=True,
                env=full_env
            )
            return result
        except subprocess.CalledProcessError as e:
            self._print_error(f"Command failed: {cmd_str}")
            self._print_error(f"Exit code: {e.returncode}")
            if check:
                raise
            return e
    
    def cleanup(self):
        """Clean up build artifacts"""
        self._print_header("Cleaning Up")
        
        # Remove root-level CMake artifacts
        artifacts = ["CMakeCache.txt", "CMakeFiles"]
        for artifact in artifacts:
            path = self.root_dir / artifact
            if path.exists():
                self._print_info(f"Removing {artifact}")
                if path.is_file():
                    path.unlink()
                else:
                    shutil.rmtree(path)
        
        # Remove build directories
        for preset in self.presets.get("configurePresets", []):
            build_dir = Path(preset.get("binaryDir", "").replace("${sourceDir}/", ""))
            build_path = self.root_dir / build_dir
            if build_path.exists():
                self._print_info(f"Removing build directory: {build_dir}")
                shutil.rmtree(build_path)
        
        self._print_success("Cleanup completed")
    
    def get_available_platforms(self) -> List[str]:
        """Get list of available build platforms"""
        return [preset["name"] for preset in self.presets.get("configurePresets", [])]
    
    def configure_preset(self, preset_name: str) -> bool:
        """Configure a specific preset"""
        # Handle Android presets specially
        if preset_name.startswith("android-"):
            return self.configure_android_preset(preset_name)
        
        self._print_info(f"Configuring preset: {preset_name}")
        
        try:
            self._run_command(["cmake", "--preset", preset_name])
            self._print_success(f"Configuration successful for {preset_name}")
            return True
        except subprocess.CalledProcessError:
            self._print_error(f"Configuration failed for {preset_name}")
            return False
    
    def build_preset(self, preset_name: str) -> bool:
        """Build a specific preset"""
        # Handle Android presets specially
        if preset_name.startswith("android-"):
            return self.build_android_preset(preset_name)
        
        self._print_info(f"Building preset: {preset_name}")
        
        try:
            self._run_command(["cmake", "--build", "--preset", preset_name])
            self._print_success(f"Build successful for {preset_name}")
            return True
        except subprocess.CalledProcessError:
            self._print_error(f"Build failed for {preset_name}")
            return False
    
    def build_single(self, platform: str) -> bool:
        """Build a single platform"""
        self._print_header(f"Building {platform}")
        
        if not self.configure_preset(platform):
            return False
        
        if not self.build_preset(platform):
            return False
        
        return True
    
    def build_all(self, platforms: Optional[List[str]] = None) -> Dict[str, bool]:
        """Build all platforms or specified platforms"""
        if platforms is None:
            platforms = self.get_available_platforms()
        
        self._print_header("Building All Platforms")
        self._print_info(f"Platforms to build: {', '.join(platforms)}")
        
        results = {}
        
        for platform in platforms:
            success = self.build_single(platform)
            results[platform] = success
            
            if not success:
                self._print_warning(f"Build failed for {platform}, continuing with next platform")
        
        # Print summary
        self._print_header("Build Summary")
        for platform, success in results.items():
            status = "SUCCESS" if success else "FAILED"
            color = Colors.OKGREEN if success else Colors.FAIL
            print(f"{color}{platform}: {status}{Colors.ENDC}")
        
        successful_builds = sum(1 for success in results.values() if success)
        total_builds = len(results)
        
        if successful_builds == total_builds:
            self._print_success(f"All {total_builds} builds completed successfully!")
        else:
            self._print_warning(f"{successful_builds}/{total_builds} builds completed successfully")
        
        return results
    
    def build_ios(self) -> bool:
        """Build all iOS variants (device + simulators)"""
        ios_platforms = ["ios-arm64", "ios-simulator-x64", "ios-simulator-arm64"]
        
        self._print_header("Building HiGHS for iOS")
        
        # Clean up iOS build directories first
        for platform in ios_platforms:
            build_dir = self.root_dir / f"build-{platform}"
            if build_dir.exists():
                self._print_info(f"Cleaning up previous build: {build_dir}")
                shutil.rmtree(build_dir)
        
        results = self.build_all(ios_platforms)
        
        # Check if all iOS builds succeeded
        all_success = all(results.values())
        
        if all_success:
            self._print_success("All iOS builds completed successfully!")
        else:
            self._print_error("Some iOS builds failed")
        
        return all_success
    
    def create_ios_universal(self) -> bool:
        """Create universal iOS library combining all architectures"""
        self._print_header("Creating Universal HiGHS Library for iOS")
        
        # First build all iOS architectures
        if not self.build_ios():
            self._print_error("iOS builds failed, cannot create universal library")
            return False
        
        # Create dist directory
        dist_dir = self.root_dir / "dist" / "ios"
        dist_dir.mkdir(parents=True, exist_ok=True)
        
        # Define library paths
        lib_paths = [
            self.root_dir / "build-ios-arm64" / "Debug" / "lib" / "libhighs.a",
            self.root_dir / "build-ios-simulator-x64" / "Debug" / "lib" / "libhighs.a",
            self.root_dir / "build-ios-simulator-arm64" / "Debug" / "lib" / "libhighs.a"
        ]
        
        # Check if all libraries exist
        missing_libs = [path for path in lib_paths if not path.exists()]
        if missing_libs:
            self._print_error("Missing library files:")
            for lib in missing_libs:
                self._print_error(f"  {lib}")
            return False
        
        # Create universal library using lipo (macOS only)
        if platform.system() != "Darwin":
            self._print_error("Universal iOS library creation requires macOS")
            return False
        
        universal_lib = dist_dir / "libhighs-universal.a"
        
        try:
            lipo_cmd = ["lipo", "-create"] + [str(path) for path in lib_paths] + ["-output", str(universal_lib)]
            self._run_command(lipo_cmd)
            
            # Verify the universal library
            self._print_info("Universal Library Info:")
            self._run_command(["lipo", "-info", str(universal_lib)])
            
            self._print_success("Universal iOS library created successfully!")
            self._print_info(f"Universal library saved to: {universal_lib}")
            return True
            
        except subprocess.CalledProcessError:
            self._print_error("Failed to create universal iOS library")
            return False
    
    def set_android_ndk_path(self, ndk_path: str) -> bool:
        """Set the Android NDK path for building"""
        ndk_path_obj = Path(ndk_path)
        
        if not ndk_path_obj.exists():
            self._print_error(f"Android NDK path does not exist: {ndk_path}")
            return False
        
        # Check if this looks like a valid NDK installation
        toolchain_cmake = ndk_path_obj / "build" / "cmake" / "android.toolchain.cmake"
        if not toolchain_cmake.exists():
            self._print_error(f"Invalid Android NDK path: {ndk_path}")
            self._print_error("Expected to find: build/cmake/android.toolchain.cmake")
            return False
        
        self.android_ndk_path = str(ndk_path_obj.resolve())
        self._save_android_ndk_path(self.android_ndk_path)
        self._print_success(f"Android NDK path set to: {self.android_ndk_path}")
        self._print_info(f"NDK path saved to: {self.config_file}")
        return True
    
    def get_android_env(self) -> Dict[str, str]:
        """Get environment variables needed for Android builds"""
        if not self.android_ndk_path:
            raise ValueError("Android NDK path not set. Use set_android_ndk_path() first.")
        
        return {
            "ANDROID_NDK_ROOT": self.android_ndk_path,
            "ANDROID_NDK_HOME": self.android_ndk_path  # Some tools use this alternative name
        }
    
    def configure_android_preset(self, preset_name: str) -> bool:
        """Configure a specific Android preset with NDK environment"""
        if not self.android_ndk_path:
            self._print_error("Android NDK path not set. Use set_android_ndk_path() first.")
            return False
        
        self._print_info(f"Configuring Android preset: {preset_name}")
        
        try:
            env = self.get_android_env()
            self._run_command(["cmake", "--preset", preset_name], env=env)
            self._print_success(f"Configuration successful for {preset_name}")
            return True
        except subprocess.CalledProcessError:
            self._print_error(f"Configuration failed for {preset_name}")
            return False
    
    def build_android_preset(self, preset_name: str) -> bool:
        """Build a specific Android preset"""
        if not self.android_ndk_path:
            self._print_error("Android NDK path not set. Use set_android_ndk_path() first.")
            return False
        
        self._print_info(f"Building Android preset: {preset_name}")
        
        try:
            env = self.get_android_env()
            self._run_command(["cmake", "--build", "--preset", preset_name], env=env)
            self._print_success(f"Build successful for {preset_name}")
            return True
        except subprocess.CalledProcessError:
            self._print_error(f"Build failed for {preset_name}")
            return False
    
    def build_android_single(self, platform: str) -> bool:
        """Build a single Android platform"""
        if not platform.startswith("android-"):
            self._print_error(f"Not an Android platform: {platform}")
            return False
        
        self._print_header(f"Building {platform}")
        
        if not self.configure_android_preset(platform):
            return False
        
        if not self.build_android_preset(platform):
            return False
        
        return True
    
    def build_android(self) -> bool:
        """Build all Android variants"""
        android_platforms = ["android-arm64", "android-arm32", "android-x86", "android-x64"]
        
        self._print_header("Building HiGHS for Android")
        
        if not self.android_ndk_path:
            self._print_error("Android NDK path not set.")
            self._print_info("Use: python build.py android --ndk-path /path/to/ndk")
            return False
        
        # Clean up Android build directories first
        for platform in android_platforms:
            build_dir = self.root_dir / f"build-{platform}"
            if build_dir.exists():
                self._print_info(f"Cleaning up previous build: {build_dir}")
                shutil.rmtree(build_dir)
        
        results = {}
        for platform in android_platforms:
            success = self.build_android_single(platform)
            results[platform] = success
            
            if not success:
                self._print_warning(f"Build failed for {platform}, continuing with next platform")
        
        # Print Android build summary
        self._print_header("Android Build Summary")
        for platform, success in results.items():
            status = "SUCCESS" if success else "FAILED"
            color = Colors.OKGREEN if success else Colors.FAIL
            print(f"{color}{platform}: {status}{Colors.ENDC}")
        
        # Check if all Android builds succeeded
        all_success = all(results.values())
        
        if all_success:
            self._print_success("All Android builds completed successfully!")
        else:
            self._print_error("Some Android builds failed")
        
        return all_success
    
    def show_config(self):
        """Show current build configuration"""
        self._print_header("Build Configuration")
        
        print(f"Root directory: {self.root_dir}")
        print(f"CMake presets: {self.presets_file}")
        print(f"Config file: {self.config_file}")
        
        if self.android_ndk_path:
            print(f"{Colors.OKGREEN}Android NDK: {self.android_ndk_path}{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}Android NDK: Not configured{Colors.ENDC}")
            print("  Use: python build.py android --ndk-path /path/to/ndk")
        
        # Show available platforms
        print(f"\nAvailable platforms:")
        platforms = self.get_available_platforms()
        android_platforms = [p for p in platforms if p.startswith("android-")]
        other_platforms = [p for p in platforms if not p.startswith("android-")]
        
        for platform in other_platforms:
            print(f"  - {platform}")
        
        for platform in android_platforms:
            if self.android_ndk_path:
                print(f"  - {Colors.OKGREEN}{platform}{Colors.ENDC}")
            else:
                print(f"  - {Colors.WARNING}{platform} (requires NDK path){Colors.ENDC}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Cross-platform build script for HiGHS")
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Clean command
    clean_parser = subparsers.add_parser("clean", help="Clean up build artifacts")
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Show current build configuration")
    
    # List platforms command
    list_parser = subparsers.add_parser("list", help="List available build platforms")
    
    # Build single platform command
    build_parser = subparsers.add_parser("build", help="Build specific platform(s)")
    build_parser.add_argument("platforms", nargs="*", 
                             help="Platform(s) to build (default: all platforms)")
    build_parser.add_argument("--ndk-path", type=str,
                             help="Path to Android NDK (required for Android platforms)")
    
    # Build all command
    all_parser = subparsers.add_parser("all", help="Build all platforms")
    all_parser.add_argument("--ndk-path", type=str,
                           help="Path to Android NDK (required for Android platforms)")
    
    # iOS specific commands
    ios_parser = subparsers.add_parser("ios", help="Build all iOS variants")
    ios_universal_parser = subparsers.add_parser("ios-universal", 
                                               help="Build universal iOS library")
    
    # Android specific commands
    android_parser = subparsers.add_parser("android", help="Build all Android variants")
    android_parser.add_argument("--ndk-path", type=str, required=True,
                               help="Path to Android NDK (required)")
    android_parser.add_argument("--platform", type=str,
                               choices=["android-arm64", "android-arm32", "android-x86", "android-x64"],
                               help="Build specific Android platform only")
    
    args = parser.parse_args()
    
    # Create build system instance
    build_system = BuildSystem()
    
    # Set Android NDK path if provided
    if hasattr(args, 'ndk_path') and args.ndk_path:
        if not build_system.set_android_ndk_path(args.ndk_path):
            sys.exit(1)
    
    if args.command == "clean":
        build_system.cleanup()
        
    elif args.command == "config":
        build_system.show_config()
        
    elif args.command == "list":
        platforms = build_system.get_available_platforms()
        print("Available build platforms:")
        for platform in platforms:
            print(f"  - {platform}")
    
    elif args.command == "build":
        platforms = args.platforms if args.platforms else None
        if platforms:
            # Check if any Android platforms are requested and NDK path is required
            android_platforms_requested = [p for p in platforms if p.startswith("android-")]
            if android_platforms_requested and not args.ndk_path:
                build_system._print_error("Android NDK path is required for Android platforms")
                build_system._print_info("Use: --ndk-path /path/to/android/ndk")
                sys.exit(1)
            
            # Validate platforms
            available = build_system.get_available_platforms()
            invalid = [p for p in platforms if p not in available]
            if invalid:
                build_system._print_error(f"Invalid platforms: {', '.join(invalid)}")
                build_system._print_info(f"Available platforms: {', '.join(available)}")
                sys.exit(1)
        
        results = build_system.build_all(platforms)
        # Exit with error code if any builds failed
        if not all(results.values()):
            sys.exit(1)
    
    elif args.command == "all":
        # Check if Android NDK is needed for building all platforms
        available_platforms = build_system.get_available_platforms()
        android_platforms = [p for p in available_platforms if p.startswith("android-")]
        if android_platforms and not args.ndk_path:
            build_system._print_warning("Android NDK path not provided. Skipping Android platforms.")
            build_system._print_info("Use: --ndk-path /path/to/android/ndk to include Android builds")
            # Filter out Android platforms
            non_android_platforms = [p for p in available_platforms if not p.startswith("android-")]
            results = build_system.build_all(non_android_platforms)
        else:
            results = build_system.build_all()
        
        if not all(results.values()):
            sys.exit(1)
    
    elif args.command == "ios":
        if not build_system.build_ios():
            sys.exit(1)
    
    elif args.command == "ios-universal":
        if not build_system.create_ios_universal():
            sys.exit(1)
    
    elif args.command == "android":
        if args.platform:
            # Build specific Android platform
            if not build_system.build_android_single(args.platform):
                sys.exit(1)
        else:
            # Build all Android platforms
            if not build_system.build_android():
                sys.exit(1)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
