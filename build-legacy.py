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
    
    def __init__(self, root_dir: Optional[str] = './highs_patched', extract_libs: bool = False, build_config: str = "Release"):
        self.script_dir = Path(__file__).parent  # Directory where the build script is located
        self.project_dir = Path(root_dir) if root_dir else self.script_dir / 'highs_patched'
        self.presets_file = self.project_dir / "CMakePresets.json"
        self.env_file = self.script_dir / ".env"  # .env goes with the build script
        self.presets = self._load_presets()
        self.android_ndk_path = self._load_android_ndk_path()
        self.extract_libs = extract_libs
        self.build_config = build_config
        
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
                cwd=cwd or self.project_dir,
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
    
    def _find_library_files(self, build_dir: Path) -> List[Path]:
        """Find library files in the build directory"""
        lib_extensions = ['.a', '.so', '.dylib', '.dll', '.lib']
        lib_files = []
        
        # Look for library files recursively
        for lib_ext in lib_extensions:
            lib_files.extend(build_dir.rglob(f'*{lib_ext}'))
        
        # Filter out system libraries and intermediate files
        filtered_libs = []
        for lib_file in lib_files:
            lib_name = lib_file.name.lower()
            # Keep HiGHS libraries and avoid system/intermediate files
            if ('highs' in lib_name or 'HiGHS' in lib_file.name) and not any(
                exclude in lib_name for exclude in ['cmake', 'test', 'example', 'benchmark', 'obj.', 'pdb']
            ):
                filtered_libs.append(lib_file)
        
        return filtered_libs
    
    def _extract_libraries(self, platform: str) -> bool:
        """Extract library files to platform build root and clean up other files"""
        if not self.extract_libs:
            return True
            
        build_dir = self.project_dir / "build" / platform
        if not build_dir.exists():
            self._print_warning(f"Build directory does not exist: {build_dir}")
            return False
            
        self._print_info(f"Extracting libraries for {platform}")
        
        # Find library files
        lib_files = self._find_library_files(build_dir)
        
        if not lib_files:
            self._print_warning(f"No library files found for {platform}")
            return False
        
        # Create temporary directory to hold libraries
        temp_libs = []
        for lib_file in lib_files:
            temp_path = build_dir.parent / f"temp_{platform}_{lib_file.name}"
            try:
                shutil.copy2(lib_file, temp_path)
                temp_libs.append(temp_path)
                self._print_info(f"Found library: {lib_file.name}")
            except Exception as e:
                self._print_error(f"Failed to copy {lib_file.name}: {e}")
                return False
        
        # Remove build directory contents except the directory itself
        try:
            # Remove all contents of build directory
            for item in build_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            
            # Move libraries back to build directory root
            for temp_lib in temp_libs:
                final_path = build_dir / temp_lib.name.replace(f"temp_{platform}_", "")
                shutil.move(temp_lib, final_path)
                self._print_success(f"Extracted: {final_path.name}")
                
        except Exception as e:
            self._print_error(f"Failed to clean up build directory for {platform}: {e}")
            # Try to restore libraries from temp files
            for temp_lib in temp_libs:
                if temp_lib.exists():
                    temp_lib.unlink()
            return False
        
        return True
    
    def cleanup(self):
        """Clean up build artifacts"""
        self._print_header("Cleaning Up")
        
        # Remove root-level CMake artifacts from project directory
        artifacts = ["CMakeCache.txt", "CMakeFiles"]
        for artifact in artifacts:
            path = self.project_dir / artifact
            if path.exists():
                self._print_info(f"Removing {artifact}")
                if path.is_file():
                    path.unlink()
                else:
                    shutil.rmtree(path)
        
        # Remove all build directories (both old and new structure)
        build_root = self.project_dir / "build"
        if build_root.exists():
            self._print_info(f"Removing build directory: build/")
            shutil.rmtree(build_root)
            
        # Remove old-style build directories
        for preset in self.presets.get("configurePresets", []):
            binary_dir = preset.get("binaryDir", "")
            if binary_dir.startswith("${sourceDir}/build/"):
                build_dir = Path(binary_dir.replace("${sourceDir}/", ""))
                build_path = self.project_dir / build_dir
                if build_path.exists():
                    self._print_info(f"Removing old build directory: {build_dir}")
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
        
        self._print_info(f"Building preset: {preset_name} ({self.build_config} configuration)")
        
        try:
            # For iOS builds, explicitly specify configuration to ensure it's used correctly
            if preset_name.startswith("ios-"):
                self._run_command(["cmake", "--build", "--preset", preset_name, "--config", self.build_config])
            else:
                # For single-config generators, build configuration is set at configure time
                # For multi-config generators (like Xcode), we need to specify it at build time
                self._run_command(["cmake", "--build", "--preset", preset_name, "--config", self.build_config])
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
        
        # Extract libraries if requested
        if not self._extract_libraries(platform):
            self._print_warning(f"Library extraction failed for {platform}")
        
        return True
    
    def build_all(self, platforms: Optional[List[str]] = None) -> Dict[str, bool]:
        """Build all platforms or specified platforms"""
        if platforms is None:
            platforms = self.get_available_platforms()
            # Filter out Android platforms if NDK path is not set
            if not self.android_ndk_path:
                android_platforms = [p for p in platforms if p.startswith("android-")]
                if android_platforms:
                    self._print_warning("Android NDK path not set. Skipping Android platforms:")
                    for p in android_platforms:
                        self._print_warning(f"  - {p}")
                    self._print_info("Use --ndk-path to include Android builds")
                    platforms = [p for p in platforms if not p.startswith("android-")]
            
            # Filter out iOS platforms - they should only be built as XCFramework bundles
            ios_platforms = [p for p in platforms if p.startswith("ios-")]
            if ios_platforms:
                self._print_info("iOS platforms are built as XCFramework bundles. Use 'python build.py build ios' instead.")
                self._print_info("Skipping iOS platforms from 'all' command:")
                for p in ios_platforms:
                    self._print_info(f"  - {p}")
                platforms = [p for p in platforms if not p.startswith("ios-")]
        
        if not platforms:
            self._print_error("No platforms to build")
            return {}
        
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
    
    def _clean_platform_builds(self, platforms: List[str]):
        """Clean build directories for specified platforms"""
        for platform in platforms:
            build_dir = self.project_dir / "build" / platform
            if build_dir.exists():
                self._print_info(f"Cleaning previous build: {build_dir.name}")
                shutil.rmtree(build_dir)

    def build_ios(self) -> bool:
        """Build iOS XCFramework bundle (combines device + simulators)"""
        return self.create_ios_xcframework()

    def create_ios_xcframework(self) -> bool:
        """Create XCFramework for iOS combining device and simulator architectures"""
        ios_platforms = ["ios-arm64", "ios-simulator-arm64"]
        
        self._print_header("Building HiGHS XCFramework for iOS")
        self._clean_platform_builds(ios_platforms)
        
        # Build all iOS architectures first
        results = self.build_all(ios_platforms)
        all_success = all(results.values())
        
        if not all_success:
            self._print_error("iOS builds failed, cannot create XCFramework")
            return False
        
        xcframework_dir = Path(self.project_dir / "build" / "ios-xcframework")
        xcframework_dir.mkdir(parents=True, exist_ok=True)
        
        # Define library paths using the configured build type
        device_lib = (self.project_dir / "build" / "ios-arm64" / self.build_config / "lib" / "libhighs.a").resolve()
        sim_libs = [
            (self.project_dir / "build" / "ios-simulator-arm64" / self.build_config / "lib" / "libhighs.a").resolve()
        ]
        
        # Check if all libraries exist
        all_libs = [device_lib] + sim_libs
        missing_libs = [path for path in all_libs if not path.exists()]
        if missing_libs:
            self._print_error("Missing library files:")
            for lib in missing_libs:
                self._print_error(f"  {lib}")
            return False
        
        # Create XCFramework using xcodebuild (macOS only)
        if platform.system() != "Darwin":
            self._print_error("XCFramework creation requires macOS")
            return False
        
        xcframework_path = xcframework_dir / "highs.xcframework"
        
        # Remove existing XCFramework if it exists
        if xcframework_path.exists():
            self._print_info(f"Removing existing XCFramework: {xcframework_path}")
            shutil.rmtree(xcframework_path)
        
        try:
            # Build xcodebuild command
            xcodebuild_cmd = [
                "xcodebuild", 
                "-create-xcframework",
                "-library", str(device_lib)
            ]
            
            # Add simulator libraries
            for sim_lib in sim_libs:
                xcodebuild_cmd.extend(["-library", str(sim_lib)])
            
            # Add output path
            xcodebuild_cmd.extend(["-output", str(xcframework_path)])
            
            self._run_command(xcodebuild_cmd)
            
            self._print_success("XCFramework created successfully!")
            self._print_info(f"XCFramework saved to: {xcframework_path}")
            return True
            
        except subprocess.CalledProcessError:
            self._print_error("Failed to create XCFramework")
            return False
        except FileNotFoundError:
            self._print_error("xcodebuild not found. Make sure Xcode is installed.")
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
        self._print_info(f"NDK path saved to: {self.env_file}")
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
        
        self._clean_platform_builds(android_platforms)
        
        results = {}
        for platform in android_platforms:
            success = self.build_android_single(platform)
            results[platform] = success
            
            if not success:
                self._print_warning(f"Build failed for {platform}, continuing with next platform")
        
        # Print build summary
        self._print_header("Android Build Summary")
        for platform, success in results.items():
            status = "SUCCESS" if success else "FAILED"
            color = Colors.OKGREEN if success else Colors.FAIL
            print(f"{color}{platform}: {status}{Colors.ENDC}")
        
        all_success = all(results.values())
        if all_success:
            self._print_success("All Android builds completed successfully!")
        else:
            self._print_error("Some Android builds failed")
        
        return all_success
    
    def show_config(self):
        """Show current build configuration"""
        self._print_header("Build Configuration")
        
        print(f"Script directory: {self.script_dir}")
        print(f"Project directory: {self.project_dir}")
        print(f"CMake presets: {self.presets_file}")
        print(f"Environment file: {self.env_file}")
        
        if self.android_ndk_path:
            print(f"{Colors.OKGREEN}Android NDK: {self.android_ndk_path}{Colors.ENDC}")
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
            if self.android_ndk_path:
                print(f"  - {Colors.OKGREEN}{platform}{Colors.ENDC}")
            else:
                print(f"  - {Colors.WARNING}{platform} (requires NDK path){Colors.ENDC}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Cross-platform build script for HiGHS",
        epilog="""
Examples:
  python build.py build all                    # Build all platforms
  python build.py build ios                    # Build iOS XCFramework
  python build.py build android --ndk-path ... # Build all Android variants  
  python build.py build linux-x64 macos  # Build specific platforms
  python build.py build --config Debug ios     # Build iOS XCFramework in Debug mode
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Clean command
    clean_parser = subparsers.add_parser("clean", help="Clean up build artifacts")
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Show current build configuration")
    
    # List platforms command
    list_parser = subparsers.add_parser("list", help="List available build platforms")
    
    # Build command (combines build, all, ios, and android functionality)
    build_parser = subparsers.add_parser("build", help="Build specific platform(s) or special targets")
    build_parser.add_argument("platforms", nargs="*", 
                             help="Platform(s) to build, 'all' for all platforms, 'ios' for iOS XCFramework, 'android' for all Android variants")
    build_parser.add_argument("--ndk-path", type=str,
                             help="Path to Android NDK (required for Android platforms)")
    build_parser.add_argument("--extract-libs", action="store_true",
                             help="Extract library files and clean up build artifacts")
    build_parser.add_argument("--config", type=str, choices=["Release", "Debug"], default="Release",
                             help="Build configuration (default: Release)")
    
    # Keep legacy 'all' command for backwards compatibility
    all_parser = subparsers.add_parser("all", help="Build all platforms (legacy, use 'build all' instead)")
    all_parser.add_argument("--ndk-path", type=str,
                           help="Path to Android NDK (required for Android platforms)")
    all_parser.add_argument("--extract-libs", action="store_true",
                           help="Extract library files and clean up build artifacts")
    all_parser.add_argument("--config", type=str, choices=["Release", "Debug"], default="Release",
                           help="Build configuration (default: Release)")
    
    # Keep legacy 'ios' command for backwards compatibility  
    ios_parser = subparsers.add_parser("ios", help="Build iOS XCFramework bundle (legacy, use 'build ios' instead)")
    ios_parser.add_argument("--extract-libs", action="store_true",
                           help="Extract library files and clean up build artifacts")
    ios_parser.add_argument("--config", type=str, choices=["Release", "Debug"], default="Release",
                           help="Build configuration (default: Release)")
    
    args = parser.parse_args()
    
    # Create build system instance with extract_libs flag and build config
    extract_libs = getattr(args, 'extract_libs', False)
    build_config = getattr(args, 'config', 'Release')
    build_system = BuildSystem(extract_libs=extract_libs, build_config=build_config)
    
    # Set Android NDK path if provided (for any command that might need it)
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
        platforms = args.platforms if args.platforms else ["all"]
        
        # Handle special targets
        if "all" in platforms:
            if len(platforms) > 1:
                build_system._print_error("Cannot mix 'all' with specific platforms")
                sys.exit(1)
            results = build_system.build_all()
            if not all(results.values()):
                sys.exit(1)
        elif "ios" in platforms:
            if len(platforms) > 1:
                build_system._print_error("Cannot mix 'ios' with other platforms")
                sys.exit(1)
            if not build_system.build_ios():
                sys.exit(1)
        elif "android" in platforms:
            if len(platforms) > 1:
                build_system._print_error("Cannot mix 'android' with other platforms")
                sys.exit(1)
            android_platforms = ["android-arm64", "android-arm32", "android-x86", "android-x64"]
            if not args.ndk_path:
                build_system._print_error("Android NDK path is required for Android platforms")
                build_system._print_info("Use: --ndk-path /path/to/android/ndk")
                sys.exit(1)
            results = build_system.build_all(android_platforms)
            if not all(results.values()):
                sys.exit(1)
        else:
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
                build_system._print_info("Special targets: all, ios, android")
                sys.exit(1)
            
            results = build_system.build_all(platforms)
            if not all(results.values()):
                sys.exit(1)
    
    elif args.command == "all":
        build_system._print_warning("'all' command is deprecated, use 'build all' instead")
        results = build_system.build_all()
        if not all(results.values()):
            sys.exit(1)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
