#!/bin/bash

set -e

echo "Building HiGHS for iOS..."

# Clean any existing build artifacts
echo "Cleaning up previous builds..."
rm -rf build-ios-arm64
rm -rf build-ios-simulator-x64  
rm -rf build-ios-simulator-arm64

# Build iOS Device (ARM64)
echo "Building iOS Device (ARM64)"
if cmake --preset ios-arm64; then
    echo "iOS ARM64 configuration successful"
    if cmake --build --preset ios-arm64; then
        echo "iOS ARM64 build successful"
    else
        echo "iOS ARM64 build failed"
        exit 1
    fi
else
    echo "iOS ARM64 configuration failed"
    exit 1
fi

# Build iOS Simulator (x64)
echo "Building iOS Simulator (x64)"
if cmake --preset ios-simulator-x64; then
    echo "iOS Simulator x64 configuration successful"
    if cmake --build --preset ios-simulator-x64; then
        echo "iOS Simulator x64 build successful"
    else
        echo "iOS Simulator x64 build failed"
        exit 1
    fi
else
    echo "iOS Simulator x64 configuration failed"
    exit 1
fi

echo "Building iOS Simulator (ARM64)"
if cmake --preset ios-simulator-arm64; then
    echo "iOS Simulator ARM64 configuration successful"
    if cmake --build --preset ios-simulator-arm64; then
        echo "iOS Simulator ARM64 build successful"
    else
        echo "iOS Simulator ARM64 build failed"
        exit 1
    fi
else
    echo "iOS Simulator ARM64 configuration failed"
    exit 1
fi

echo "All iOS builds completed successfully!"
