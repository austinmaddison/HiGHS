#!/usr/bin/env python3
"""
Cross-platform build script for HiGHS - Refactored for modularity

This is the main entry point for the HiGHS build system. The actual build
logic is now split into modular components for better maintainability.
"""

import argparse
import sys
from pathlib import Path

# Add the build module to the path
sys.path.insert(0, str(Path(__file__).parent))

from build_scripts import BuildOrchestrator, Logger


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser"""
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
    subparsers.add_parser("clean", help="Clean up build artifacts")
    
    # Config command
    subparsers.add_parser("config", help="Show current build configuration")
    
    # List platforms command
    subparsers.add_parser("list", help="List available build platforms")
    
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
    
    return parser


def handle_build_command(orchestrator: BuildOrchestrator, args) -> int:
    """Handle the build command and its various targets"""
    platforms = args.platforms if args.platforms else ["all"]
    
    # Handle special targets
    if "all" in platforms:
        if len(platforms) > 1:
            Logger.error("Cannot mix 'all' with specific platforms")
            return 1
        results = orchestrator.build_multiple_platforms()
        return 0 if all(results.values()) else 1
    
    elif "ios" in platforms:
        if len(platforms) > 1:
            Logger.error("Cannot mix 'ios' with other platforms")
            return 1
        return 0 if orchestrator.build_ios_xcframework() else 1
    
    elif "android" in platforms:
        if len(platforms) > 1:
            Logger.error("Cannot mix 'android' with other platforms")
            return 1
        # Check if NDK path is available (from command line or .env file)
        if not args.ndk_path and not orchestrator.config.android_ndk_path:
            Logger.error("Android NDK path is required for Android platforms")
            Logger.info("Use: --ndk-path /path/to/android/ndk or set ANDROID_NDK_PATH in .env file")
            return 1
        return 0 if orchestrator.build_android_all() else 1
    
    else:
        # Check if any Android platforms are requested and NDK path is required
        android_platforms_requested = [p for p in platforms if p.startswith("android-")]
        if android_platforms_requested and not args.ndk_path and not orchestrator.config.android_ndk_path:
            Logger.error("Android NDK path is required for Android platforms")
            Logger.info("Use: --ndk-path /path/to/android/ndk or set ANDROID_NDK_PATH in .env file")
            return 1
        
        # Validate platforms
        available = orchestrator.get_available_platforms()
        invalid = [p for p in platforms if p not in available]
        if invalid:
            Logger.error(f"Invalid platforms: {', '.join(invalid)}")
            Logger.info(f"Available platforms: {', '.join(available)}")
            Logger.info("Special targets: all, ios, android")
            return 1
        
        results = orchestrator.build_multiple_platforms(platforms)
        return 0 if all(results.values()) else 1


def main():
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Create build orchestrator with configuration
    extract_libs = getattr(args, 'extract_libs', False)
    build_config = getattr(args, 'config', 'Release')
    orchestrator = BuildOrchestrator(extract_libs=extract_libs, build_config=build_config)
    
    # Set Android NDK path if provided (for any command that might need it)
    if hasattr(args, 'ndk_path') and args.ndk_path:
        if not orchestrator.set_android_ndk_path(args.ndk_path):
            return 1
    
    # Handle commands
    if args.command == "clean":
        orchestrator.cleanup()
        return 0
    
    elif args.command == "config":
        orchestrator.show_config()
        return 0
    
    elif args.command == "list":
        platforms = orchestrator.get_available_platforms()
        print("Available build platforms:")
        for platform in platforms:
            print(f"  - {platform}")
        return 0
    
    elif args.command == "build":
        return handle_build_command(orchestrator, args)
    
    else:
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main())
