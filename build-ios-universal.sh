#!/bin/bash

set -e

echo "Creating Universal HiGHS Library for iOS..."

# First build all architectures
./build-ios.sh

# Create universal library combining all architectures
echo "Creating universal library..."
mkdir -p dist/ios
lipo -create \
    build-ios-arm64/Debug/lib/libhighs.a \
    build-ios-simulator-x64/Debug/lib/libhighs.a \
    build-ios-simulator-arm64/Debug/lib/libhighs.a \
    -output dist/ios/libhighs-universal.a

# Verify the universal library
echo "=== Universal Library Info ==="
lipo -info dist/ios/libhighs-universal.a

echo ""
echo "Universal iOS library created successfully!"
