# HiGHS - High Performance Linear Optimization Software

This repository contains a patched version of HiGHS optimized for use with Dart and Flutter via FFI.

## About

HiGHS is a high-performance linear optimization solver that implements the simplex method and interior point method for linear programming. This fork provides prebuilt binary libraries for multiple platforms.

## Releases

All platform libraries are published in a single unified release with version numbering (e.g., v1.0.0).

### Prebuilt Libraries

The following platforms are supported:

- **Desktop**: Windows (x64), macOS (Universal), Linux (x64)
- **Mobile**: iOS (arm64), Android (arm64-v8a, armeabi-v7a, x86_64, x86)

### Header Files

The includes package contains all necessary C++ headers required for developing against HiGHS.


### Platform Integration

- **Desktop**: Libraries are automatically loaded from the package
- **iOS**: Extract the XCFramework and add to your Podfile
- **Android**: Extract the JNI bundle to your project's jniLibs directory

## Development

For custom builds or development:

1. Download the "highs-includes" package from releases
2. Download the appropriate platform libraries
3. Configure your build system to link against the libraries

## Links

- [Original HiGHS Project](https://github.com/ERGO-Code/HiGHS)
- [Dart HiGHS Package](https://pub.dev/packages/dart_highs)