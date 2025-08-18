# HiGHS GitHub Actions Build System

This document describes the redesigned GitHub Actions workflows that use the new Python build script for creating HiGHS prebuilt libraries across all supported platforms.

## 🚀 Overview

The build system now uses a unified Python build script (`build.py`) that provides consistent build processes across all platforms. Each platform gets its own workflow that creates platform-specific releases with multiple packaging options.

## 🏗️ Workflows

### Individual Platform Workflows

| Workflow | Trigger | Platforms | Outputs |
|----------|---------|-----------|---------|
| `build-ios.yml` | Manual/Push | iOS ARM64, iOS Simulator ARM64 | XCFramework + Individual Libraries |
| `build-android.yml` | Manual/Push | All Android ABIs | JNI Bundle + Legacy Layout + Individual |
| `build-macos.yml` | Manual/Push | macOS Universal (ARM64 + x86_64) | Dynamic Library (.dylib) |
| `build-windows.yml` | Manual/Push | Windows x64 | DLL Library |
| `build-linux.yml` | Manual/Push | Linux x64 | Shared Library (.so) |
| `build-includes.yml` | Manual/Push | Headers Only | C++ Headers Package |

### Complete Build Workflow

- `build-complete.yml` - Triggers all platform builds and provides a comprehensive summary

## 📦 Package Formats

### iOS Packages
- **XCFramework** (Recommended): `dart-highs-prebuilt-lib-ios.zip`
  - Universal framework supporting device and simulator
  - Ready for Xcode integration
- **Individual Libraries**: `dart-highs-prebuilt-lib-ios-individual.zip`
  - Separate `.a` files for each architecture
  - For advanced use cases

### Android Packages
- **JNI Bundle** (Recommended): `android-jni-libs-bundle.zip`
  ```
  jniLibs/
  ├── arm64-v8a/libhighs.so
  ├── armeabi-v7a/libhighs.so
  ├── x86/libhighs.so
  └── x86_64/libhighs.so
  ```
- **Legacy Plugin Layout**: `dart-highs-prebuilt-lib-android.zip`
  - Traditional `android/src/main/jniLibs/` structure
- **Individual Libraries**: `dart-highs-prebuilt-lib-android-individual.zip`
  - Separate directories per architecture

### Desktop Packages
- **macOS**: `dart-highs-prebuilt-lib-macos.zip` - Universal `.dylib`
- **Windows**: `dart-highs-prebuilt-lib-windows.zip` - x64 `.dll`
- **Linux**: `dart-highs-prebuilt-lib-linux.zip` - x64 `.so`

### Headers Package
- **Includes**: `highs-includes.zip` - Complete C++ headers with documentation

## ⚙️ Configuration

### Environment Variables

Each workflow defines consistent environment variables:

```yaml
env:
  CMAKE_BUILD_PARALLEL_LEVEL: 4
  PYTHON_VERSION: "3.11"
  BUILD_CONFIG: "Release"
  PACKAGE_NAME: "platform-specific-name"
```

### Customization Points

All naming conventions and configurations are defined at the top of each workflow file for easy modification:

- Package names
- Build configurations
- Python version
- Parallel build levels
- Release tag patterns

## 🔧 Build Script Integration

All workflows use the unified `build.py` script:

```bash
# Build single platform
python build.py build <platform> --config Release --extract-libs

# Build iOS XCFramework  
python build.py build ios --config Release

# Build all Android variants
python build.py build android --ndk-path $ANDROID_NDK_ROOT --config Release
```

## 📋 Triggers

### Automatic Triggers
Workflows trigger automatically on push when these paths change:
- `CMakeLists.txt`
- `cmake/**`
- `highs/**` (source code)
- `build_scripts/**`
- `build.py`
- Individual workflow files

### Manual Triggers
All workflows support manual dispatch for on-demand builds.

## 🏷️ Release Strategy

### Individual Releases
Each platform creates its own tagged release:
- `ios-v{run_number}-{sha}`
- `android-v{run_number}-{sha}`
- `macos-v{run_number}-{sha}`
- `windows-v{run_number}-{sha}`
- `linux-v{run_number}-{sha}`
- `includes-v{run_number}-{sha}`

### Benefits
- Platform-specific versioning
- Independent release cycles
- Clear artifact organization
- Easy integration with package managers

## 📖 Usage Examples

### iOS Development
```bash
# Download and extract XCFramework
unzip dart-highs-prebuilt-lib-ios.zip
# Drag ios/LibHighs.xcframework into Xcode project
```

### Android Development
```bash
# Download JNI bundle
unzip android-jni-libs-bundle.zip
# Copy jniLibs/ to app/src/main/jniLibs/
```

### Desktop Development
```bash
# Extract headers and libraries
unzip highs-includes.zip
unzip dart-highs-prebuilt-lib-linux.zip

# Compile
g++ -I./include -L./linux -lhighs app.cpp -o app
```

### CMake Integration
```cmake
# Find the library
find_library(HIGHS_LIB highs PATHS path/to/platform/lib)

# Set up includes
target_include_directories(your_target PRIVATE path/to/include)

# Link
target_link_libraries(your_target ${HIGHS_LIB})
```

## 🛠️ Development

### Adding New Platforms
1. Add platform preset to `CMakePresets.json`
2. Update build script if special handling needed
3. Create new workflow file following existing patterns
4. Add platform to `build-complete.yml`

### Modifying Packages
1. Update environment variables at top of workflow
2. Modify packaging steps as needed
3. Update release descriptions

### Testing Changes
1. Use manual workflow dispatch for testing
2. Check artifact structure and contents
3. Validate release descriptions and files

## 🚨 Troubleshooting

### Build Failures
- Check build script logs for detailed errors
- Verify CMake presets are valid
- Ensure all dependencies are available

### Artifact Issues  
- Verify file paths in upload steps
- Check that build outputs exist at expected locations
- Validate packaging directory structure

### Release Problems
- Ensure GitHub token has release permissions
- Check tag naming patterns
- Verify file paths in release step

## 📚 Additional Resources

- [HiGHS Build Script Documentation](../BUILD_PYTHON.md)
- [CMake Presets Reference](../highs_patched/CMakePresets.json)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
