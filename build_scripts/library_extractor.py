"""
Library extraction and management functionality
"""

import shutil
from pathlib import Path
from typing import List

from .utils import Logger


class LibraryExtractor:
    """Handles extraction and management of library files"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
    
    def find_library_files(self, build_dir: Path) -> List[Path]:
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
    
    def extract_libraries(self, platform: str) -> bool:
        """Extract library files to platform build root and clean up other files"""
        
        potential_paths = [
            self.project_dir / "build" / platform,
            self.project_dir / "build" / platform / "Release",
            self.project_dir / "build" / platform / "Debug",
        ]
        
        build_dir = None
        for path in potential_paths:
            if path.exists():
                build_dir = path
                break

        if not build_dir:
            Logger.warning(f"Build directory not found for platform {platform} in standard locations.")
            return False
            
        Logger.info(f"Extracting libraries for {platform} from {build_dir}")
        
        # Find library files
        lib_files = self.find_library_files(build_dir)
        
        if not lib_files:
            Logger.warning(f"No library files found for {platform}")
            return False
        
        # Create temporary directory to hold libraries
        temp_libs = []
        for lib_file in lib_files:
            temp_path = build_dir.parent / f"temp_{platform}_{lib_file.name}"
            try:
                shutil.copy2(lib_file, temp_path)
                temp_libs.append(temp_path)
                Logger.info(f"Found library: {lib_file.name}")
            except Exception as e:
                Logger.error(f"Failed to copy {lib_file.name}: {e}")
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
                Logger.success(f"Extracted: {final_path.name}")

            # Platform-specific cleanup and renaming
            if "linux" in platform:
                # Keep only the main versioned library and create symlink
                main_lib = None
                for item in build_dir.iterdir():
                    if item.is_file() and "1.11" in item.name:
                        main_lib = item
                        break
                
                if main_lib:
                    # Remove other files
                    for item in build_dir.iterdir():
                        if item.is_file() and item != main_lib:
                            item.unlink()
                    
                    # Rename to standard .so name
                    final_lib = build_dir / "libhighs.so"
                    main_lib.rename(final_lib)

            if "macos" in platform:
                # Keep only the main versioned library and create symlink
                main_lib = None
                for item in build_dir.iterdir():
                    if item.is_file() and "1.11" in item.name:
                        main_lib = item
                        break
                
                if main_lib:
                    # Remove other files
                    for item in build_dir.iterdir():
                        if item.is_file() and item != main_lib:
                            item.unlink()
                    
                    # Rename to standard .dylib name
                    final_lib = build_dir / "libhighs.dylib"
                    main_lib.rename(final_lib)

                    


                
        except Exception as e:
            Logger.error(f"Failed to clean up build directory for {platform}: {e}")
            # Try to restore libraries from temp files
            for temp_lib in temp_libs:
                if temp_lib.exists():
                    temp_lib.unlink()
            return False
        
        return True
