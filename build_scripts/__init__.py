"""
HiGHS Build System

A modular, extensible build system for cross-platform compilation
"""

from .cleaner import BuildCleaner
from .config import ConfigManager
from .library_extractor import LibraryExtractor
from .orchestrator import BuildOrchestrator
from .platform_builders import (
    AndroidPlatformBuilder,
    iOSPlatformBuilder,
    PlatformBuilder,
    PlatformBuilderFactory,
    StandardPlatformBuilder,
)
from .utils import Colors, CommandRunner, Logger
from .xcframework_builder import XCFrameworkBuilder

__all__ = [
    'BuildOrchestrator',
    'ConfigManager',
    'CommandRunner',
    'Logger',
    'Colors',
    'PlatformBuilder',
    'StandardPlatformBuilder',
    'AndroidPlatformBuilder',
    'iOSPlatformBuilder',
    'PlatformBuilderFactory',
    'LibraryExtractor',
    'XCFrameworkBuilder',
    'BuildCleaner',
]
