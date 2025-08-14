# HiGHS Cross-Platform Build System

This Python script replaces the bash build scripts (`build-all.sh`, `build-ios.sh`, `build-ios-universal.sh`) with a cross-platform solution that works on Windows, macOS, and Linux.

## Requirements

- Python 3.6+
- CMake
- Platform-specific build tools (Visual Studio, Xcode, Android NDK, etc.)

## Usage

### Basic Commands

```bash
# Show help
./build.py --help

# List all available platforms
./build.py list

# Clean up all build artifacts
./build.py clean

# Build all platforms
./build.py all

# Build specific platforms
./build.py build windows-x64 linux-x64
./build.py build macos-universal

# iOS specific builds
./build.py ios                # Build all iOS variants
./build.py ios-universal     # Build universal iOS library
```

## Available Platforms

The script automatically reads from `CMakePresets.json` and supports:

- `windows-x64` - Windows 64-bit
- `linux-x64` - Linux 64-bit  
- `android-arm64` - Android ARM64
- `android-arm32` - Android ARM32
- `android-x86` - Android x86
- `android-x64` - Android x64
- `ios-arm64` - iOS Device
- `ios-simulator-x64` - iOS Simulator x64
- `ios-simulator-arm64` - iOS Simulator ARM64
- `macos-universal` - macOS Universal (ARM64 + x64)

## Features

- **Cross-platform**: Works on Windows, macOS, and Linux
- **Colored output**: Easy to read build status and logs
- **Error handling**: Graceful failure handling with detailed error messages
- **Parallel builds**: Continues building other platforms if one fails
- **Clean command**: Removes all build artifacts and directories
- **iOS Universal**: Creates fat binaries combining all iOS architectures
- **Build summary**: Shows success/failure status for each platform

## Migration from Bash Scripts

### Old vs New Commands

| Old Bash Script | New Python Command |
|----------------|-------------------|
| `./build-all.sh` | `./build.py all` |
| `./build-ios.sh` | `./build.py ios` |
| `./build-ios-universal.sh` | `./build.py ios-universal` |
| `./clean-up.sh` | `./build.py clean` |

### Benefits of Python Script

1. **Cross-platform compatibility** - Works on Windows without WSL/Git Bash
2. **Better error handling** - More detailed error messages and graceful failures
3. **Colored output** - Easier to spot issues during builds
4. **Modular design** - Easy to extend with new platforms or features
5. **JSON integration** - Automatically reads CMake presets
6. **Build summaries** - Clear overview of what succeeded/failed

## Environment Variables

Some platforms may require environment variables:

- **Android**: `ANDROID_NDK_ROOT` - Path to Android NDK
- **iOS**: Xcode command line tools must be installed

## Examples

```bash
# Clean and build everything
./build.py clean
./build.py all

# Build only mobile platforms
./build.py build android-arm64 android-x64 ios-arm64

# Build iOS universal library
./build.py ios-universal

# Build single platform with verbose output
./build.py build linux-x64
```

## Troubleshooting

- **Permission denied**: Run `chmod +x build.py` to make script executable
- **CMake not found**: Ensure CMake is installed and in your PATH
- **Android builds fail**: Set `ANDROID_NDK_ROOT` environment variable
- **iOS builds fail**: Ensure Xcode and command line tools are installed
- **Windows builds fail**: Ensure Visual Studio 2022 is installed

## Extending the Script

The script is designed to be easily extensible. To add new platforms:

1. Add the platform to `CMakePresets.json`
2. The Python script will automatically detect it
3. For special handling (like iOS universal), add methods to the `BuildSystem` class
