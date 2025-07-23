# For Windows .dll
cmake -S . -B build -A x64 -G "Visual Studio 17 2022" . -DBUILD_SHARED_LIBS=ON
cmake --build build --parallel