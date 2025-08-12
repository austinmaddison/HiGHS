#!/bin/bash

echo "Cleaning up source directory..."
rm -f CMakeCache.txt
rm -rf CMakeFiles/

platforms=("windows-x64" "linux-x64" "android-arm64" "android-arm32" "android-x86" "android-x64" "ios-arm64" "ios-simulator-x64" "ios-simulator-arm64" "macos-universal")

for platform in "${platforms[@]}"; do
    echo "Building for $platform..."
    
    # Configure
    if cmake --preset "$platform"; then
        echo "Configuration successful for $platform"
    else
        echo "Configuration failed for $platform"
        continue
    fi
    
    # Build
    if cmake --build --preset "$platform"; then
        echo "Build successful for $platform"
    else
        echo "Build failed for $platform"
    fi
    
done

echo "Build process completed!"