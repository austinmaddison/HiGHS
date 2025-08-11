# HiGHS Multi-Platform Build Guide

This guide explains how to build the HiGHS optimization library for multiple platforms using a unified CMake configuration.

## Supported Platforms

- **Windows** (x64)
- **Linux** (x64)
- **Android** (arm64-v8a, armeabi-v7a, x86, x86_64)
- **macOS** (Universal: arm64 + x86_64)
- **iOS** (arm64)

## Prerequisites

### General Requirements
- CMake 3.20 or higher
- Git

### Platform-Specific Requirements

#### Windows
- Visual Studio 2022 (with C++ build tools)
- Windows SDK

#### Linux
- GCC or Clang
- Ninja build system: `sudo apt install ninja-build`

#### Android
- Android NDK (version 21 or higher)
- Set `ANDROID_NDK_ROOT` environment variable:
  ```bash
  export ANDROID_NDK_ROOT="/path/to/android/ndk"
  ```

#### macOS/iOS
- Xcode with Command Line Tools
- macOS 10.15 or higher for macOS builds
- iOS 12.0 or higher for iOS builds

## Quick Start

### Option 1: Build All Platforms (Recommended)

1. **Set up environment variables:**
   ```bash
   # For Android builds
   export ANDROID_NDK_ROOT="/path/to/android/ndk"
   ```

2. **Run the unified build script:**
   ```bash
   ./build-all.sh
   ```

This will build for all supported platforms automatically.

### Option 2: Build Individual Platforms

Using CMake presets:

```bash
# Windows
cmake --preset windows-x64
cmake --build --preset windows-x64 --parallel

# Linux
cmake --preset linux-x64
cmake --build --preset linux-x64 --parallel

# Android ARM64
cmake --preset android-arm64
cmake --build --preset android-arm64 --parallel

# Android ARM32
cmake --preset android-arm32
cmake --build --preset android-arm32 --parallel

# macOS Universal
cmake --preset macos-universal
cmake --build --preset macos-universal --parallel

# iOS
cmake --preset ios-arm64
cmake --build --preset ios-arm64 --parallel
```

### Clean Up
```
   ./clean-up.sh

```

## Build Outputs

After building, libraries will be located in:

```
build-windows-x64/        # Windows libraries
build-linux-x64/          # Linux libraries
build-android-arm64/      # Android ARM64 libraries
build-android-32bit/      # Android ARM32 libraries
build-android-x86/        # Android x86 libraries
build-android-x64/        # Android x86_64 libraries
build-macos-universal/    # macOS Universal libraries
build-ios-arm64/          # iOS libraries
```

## Configuration Options

The build uses these CMake options:

- `BUILD_SHARED_LIBS=ON` - Build shared libraries (except iOS)
- `FAST_BUILD=ON` - Optimized build settings
- `BUILD_CXX=ON` - Build C++ interface (Android only)
- `CMAKE_BUILD_TYPE=Release` - Release configuration

## Platform-Specific Notes

### Android
- **NDK Version:** Tested with NDK 29.0.13599879
- **API Level:** Minimum Android API 24
- **ABIs:** Supports all major Android ABIs
- **Libraries:** Built as shared libraries (.so files)

### Windows
- **Generator:** Visual Studio 2022
- **Architecture:** x64 only
- **Libraries:** Built as shared libraries (.dll files)

### iOS
- **Deployment Target:** iOS 12.0+
- **Architecture:** ARM64 only (device builds)
- **Libraries:** Built as static libraries (.a files)
- **Note:** Code signing may be required for device deployment

### macOS
- **Deployment Target:** macOS 10.15+
- **Architecture:** Universal (ARM64 + x86_64)
- **Libraries:** Built as shared libraries (.dylib files)

### Linux
- **Architecture:** x86_64
- **Libraries:** Built as shared libraries (.so files)
- **Compiler:** Uses system default (GCC/Clang)

## Troubleshooting

### Common Issues

1. **"You cannot build in a source directory" error:**
   - Clean the source directory: `rm -f CMakeCache.txt && rm -rf CMakeFiles/`
   - Each platform uses separate build directories

2. **Android NDK not found:**
   - Verify `ANDROID_NDK_ROOT` environment variable is set
   - Check that the NDK path exists and contains `build/cmake/android.toolchain.cmake`

3. **Visual Studio not found (Windows):**
   - Install Visual Studio 2022 with C++ build tools
   - Alternatively, use Visual Studio Build Tools

4. **Ninja not found:**
   ```bash
   sudo apt install ninja-build  # Ubuntu/Debian
   sudo yum install ninja-build  # CentOS/RHEL
   brew install ninja            # macOS
   ```

### Build Cleanup

To clean all build directories:
```bash
rm -rf build-*
```

To clean only CMake cache files:
```bash
rm -f CMakeCache.txt
rm -rf CMakeFiles/
```

## Integration

### Android Integration
Copy the built `.so` files to your Android project:
```
app/src/main/jniLibs/
├── arm64-v8a/libhighs.so
├── armeabi-v7a/libhighs.so
├── x86/libhighs.so
└── x86_64/libhighs.so
```

In flutter, this can be done through flutter plugins or each platform. 
This bundles the binaries with the flutter build for that given platfrom

### iOS Integration
Add the built static library to your Xcode project and link against it.
In flutter, this can be done through flutter plugins or each platform. 
This bundles the binaries with the flutter build for that given platfrom

### Desktop Integration
Link against the shared libraries and ensure they're in your application's library search path.
In flutter, this can be done through flutter plugins or each platform. 
This bundles the binaries with the flutter build for that given platfrom

## Build Script Details

The unified build system uses:
- **CMake Presets** for configuration management
- **Separate build directories** to avoid conflicts
- **Parallel compilation** for faster builds
- **Error handling** to continue building other platforms if one fails

## Contributing

When adding support for new platforms:
1. Add the preset to `CMakePresets.json`
2. Update the platform list in `build-all.sh`
3. Update this README with platform-specific requirements
4. Test the build on the target platform