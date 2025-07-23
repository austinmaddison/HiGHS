set NDK_PATH=C:\Users\Austi\AppData\Local\Android\Sdk\ndk\29.0.13599879
set TOOLCHAIN=%NDK_PATH%\build\cmake\android.toolchain.cmake

mkdir build-android-32bit
cd build-android-32bit

cmake .. ^
  -G "Ninja" ^
  -DCMAKE_TOOLCHAIN_FILE=%TOOLCHAIN% ^
  -DANDROID_ABI=armeabi-v7a ^
  -DANDROID_PLATFORM=android-24 ^
  -DBUILD_CXX=ON ^
  -DBUILD_SHARED_LIBS=ON ^
  -DFAST_BUILD=ON ^
  -DCMAKE_BUILD_TYPE=Release

if %ERRORLEVEL% NEQ 0 (
  echo CMake configuration failed
  exit /b %ERRORLEVEL%
)

cmake --build . --config Release

if %ERRORLEVEL% NEQ 0 (
  echo Build failed
  exit /b %ERRORLEVEL%
)

echo Build completed successfully