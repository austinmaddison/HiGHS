"""
Platform-specific build implementations
"""

import platform
import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

from .config import ConfigManager
from .utils import CommandRunner, Logger


class PlatformBuilder(ABC):
    """Abstract base class for platform-specific builders"""
    
    def __init__(self, config: ConfigManager, runner: CommandRunner, build_config: str):
        self.config = config
        self.runner = runner
        self.build_config = build_config
    
    @abstractmethod
    def configure(self, preset_name: str) -> bool:
        """Configure the build for this platform"""
        pass
    
    @abstractmethod
    def build(self, preset_name: str) -> bool:
        """Build the platform"""
        pass
    
    def can_handle(self, preset_name: str) -> bool:
        """Check if this builder can handle the given preset"""
        return False


class StandardPlatformBuilder(PlatformBuilder):
    """Builder for standard platforms (Linux, macOS, Windows)"""
    
    def can_handle(self, preset_name: str) -> bool:
        return not preset_name.startswith(('android-', 'ios-'))
    
    def configure(self, preset_name: str) -> bool:
        """Configure a standard preset"""
        Logger.info(f"Configuring preset: {preset_name}")
        
        try:
            # Check if this is a single-config generator that needs CMAKE_BUILD_TYPE override
            preset = self._get_preset(preset_name)
            generator = preset.get("generator", "").lower()
            
            configure_args = ["cmake", "--preset", preset_name]
            if "ninja" in generator and self.build_config != "Release":
                # Override CMAKE_BUILD_TYPE for Ninja builds if not Release
                configure_args.extend(["-DCMAKE_BUILD_TYPE=" + self.build_config])
            
            self.runner.run(configure_args)
            Logger.success(f"Configuration successful for {preset_name}")
            return True
        except subprocess.CalledProcessError:
            Logger.error(f"Configuration failed for {preset_name}")
            return False
    
    def build(self, preset_name: str) -> bool:
        """Build a standard preset"""
        Logger.info(f"Building preset: {preset_name} ({self.build_config} configuration)")
        
        try:
            # Check if this is a multi-config generator that needs --config flag
            preset = self._get_preset(preset_name)
            generator = preset.get("generator", "").lower()
            
            if "visual studio" in generator or "xcode" in generator:
                # Multi-config generators need --config flag
                self.runner.run(["cmake", "--build", "--preset", preset_name, "--config", self.build_config])
            else:
                # Single-config generators like Ninja don't use --config flag
                self.runner.run(["cmake", "--build", "--preset", preset_name])
            
            Logger.success(f"Build successful for {preset_name}")
            return True
        except subprocess.CalledProcessError:
            Logger.error(f"Build failed for {preset_name}")
            return False

    def _get_preset(self, preset_name: str) -> dict:
        """Get preset configuration from CMakePresets.json"""
        presets = self.config.presets.get("configurePresets", [])
        for preset in presets:
            if preset.get("name") == preset_name:
                return preset
        return {}


class AndroidPlatformBuilder(PlatformBuilder):
    """Builder for Android platforms"""
    
    def can_handle(self, preset_name: str) -> bool:
        return preset_name.startswith('android-')
    
    def configure(self, preset_name: str) -> bool:
        """Configure an Android preset with NDK environment"""
        if not self.config.android_ndk_path:
            Logger.error("Android NDK path not set. Use set_android_ndk_path() first.")
            return False
        
        Logger.info(f"Configuring Android preset: {preset_name}")
        
        try:
            env = self.config.get_android_env()
            
            # For single-config generators like Ninja, we need to override CMAKE_BUILD_TYPE during configuration
            # if a different build type is requested than what's in the preset
            configure_args = ["cmake", "--preset", preset_name]
            if self.build_config != "Release":  # Only override if not the preset default
                configure_args.extend(["-DCMAKE_BUILD_TYPE=" + self.build_config])
            
            self.runner.run(configure_args, env=env)
            Logger.success(f"Configuration successful for {preset_name}")
            return True
        except subprocess.CalledProcessError:
            Logger.error(f"Configuration failed for {preset_name}")
            return False
    
    def build(self, preset_name: str) -> bool:
        """Build an Android preset"""
        if not self.config.android_ndk_path:
            Logger.error("Android NDK path not set. Use set_android_ndk_path() first.")
            return False
        
        Logger.info(f"Building Android preset: {preset_name} ({self.build_config} configuration)")
        
        try:
            env = self.config.get_android_env()
            # Android uses Ninja generator (single-config), so don't use --config flag
            self.runner.run(["cmake", "--build", "--preset", preset_name], env=env)
            Logger.success(f"Build successful for {preset_name}")
            return True
        except subprocess.CalledProcessError:
            Logger.error(f"Build failed for {preset_name}")
            return False


class iOSPlatformBuilder(PlatformBuilder):
    """Builder for iOS platforms"""
    
    def can_handle(self, preset_name: str) -> bool:
        return preset_name.startswith('ios-')
    
    def configure(self, preset_name: str) -> bool:
        """Configure an iOS preset"""
        Logger.info(f"Configuring iOS preset: {preset_name}")
        
        try:
            self.runner.run(["cmake", "--preset", preset_name])
            Logger.success(f"Configuration successful for {preset_name}")
            return True
        except subprocess.CalledProcessError:
            Logger.error(f"Configuration failed for {preset_name}")
            return False
    
    def build(self, preset_name: str) -> bool:
        """Build an iOS preset with explicit configuration"""
        Logger.info(f"Building iOS preset: {preset_name} ({self.build_config} configuration)")
        
        try:
            # For iOS builds, explicitly specify configuration to ensure it's used correctly
            self.runner.run(["cmake", "--build", "--preset", preset_name, "--config", self.build_config])
            Logger.success(f"Build successful for {preset_name}")
            return True
        except subprocess.CalledProcessError:
            Logger.error(f"Build failed for {preset_name}")
            return False


class PlatformBuilderFactory:
    """Factory for creating platform-specific builders"""
    
    @staticmethod
    def create_builders(config: ConfigManager, runner: CommandRunner, build_config: str) -> List[PlatformBuilder]:
        """Create all available platform builders"""
        return [
            StandardPlatformBuilder(config, runner, build_config),
            AndroidPlatformBuilder(config, runner, build_config),
            iOSPlatformBuilder(config, runner, build_config),
        ]
    
    @staticmethod
    def get_builder_for_preset(builders: List[PlatformBuilder], preset_name: str) -> Optional[PlatformBuilder]:
        """Get the appropriate builder for a given preset"""
        for builder in builders:
            if builder.can_handle(preset_name):
                return builder
        return None
