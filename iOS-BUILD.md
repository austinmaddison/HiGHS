# Building HiGHS for iOS

This document explains how to build HiGHS for iOS devices and simulators.

## Prerequisites

- Xcode installed with iOS SDK
- CMake 3.15 or later
- Command line tools configured to use Xcode

## Quick Start

To build all iOS targets at once:

```bash
./build-ios.sh
```

## Individual Builds

### iOS Device (ARM64)
```bash
cmake --preset ios-arm64
cmake --build --preset ios-arm64
```

### iOS Simulator (x86_64)
```bash
cmake --preset ios-simulator-x64
cmake --build --preset ios-simulator-x64
```

### iOS Simulator (ARM64)
```bash
cmake --preset ios-simulator-arm64
cmake --build --preset ios-simulator-arm64
```

## Output

The builds will create:

- **iOS Device**: `build-ios-arm64/Debug/lib/libhighs.a`
- **iOS Simulator (x64)**: `build-ios-simulator-x64/Debug/lib/libhighs.a`
- **iOS Simulator (ARM64)**: `build-ios-simulator-arm64/Debug/lib/libhighs.a`

Additionally, iOS app bundles are created for testing:
- `highs.app` - Command line interface as iOS app
- `call_highs_from_cpp.app` - C++ example
- `call_highs_from_c_minimal.app` - C example

## Creating Universal Libraries

To create a universal library that works on both device and simulator:

```bash
# Combine device and simulator libraries
lipo -create \
    build-ios-arm64/Debug/lib/libhighs.a \
    build-ios-simulator-x64/Debug/lib/libhighs.a \
    build-ios-simulator-arm64/Debug/lib/libhighs.a \
    -output libhighs-universal.a
```

## Integration

To use the HiGHS library in your iOS project:

1. Add `libhighs.a` to your Xcode project
2. Include the headers from `highs/` directory
3. Link against the library in your target settings

## Configuration Options

The iOS builds use these key settings:
- `CMAKE_SYSTEM_NAME=iOS`
- `CMAKE_OSX_DEPLOYMENT_TARGET=12.0` (iOS 12.0+)
- `BUILD_SHARED_LIBS=OFF` (static libraries for iOS)
- `FAST_BUILD=ON` (optimized build settings)

## Troubleshooting

### SDK Not Found
If you get "iphoneos is not an iOS SDK", ensure xcode-select is set correctly:
```bash
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
xcodebuild -showsdks
```

### Code Signing Issues
The builds disable code signing by default. If you need signed builds for device testing, modify the presets to include your development team ID.
