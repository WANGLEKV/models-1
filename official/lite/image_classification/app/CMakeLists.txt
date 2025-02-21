# For more information about using CMake with Android Studio, read the
# documentation: https://d.android.com/studio/projects/add-native-code.html

# Sets the minimum version of CMake required to build the native library.

cmake_minimum_required(VERSION 3.4.1)

set(CMAKE_VERBOSE_MAKEFILE on)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/libs/${ANDROID_ABI})

set(MINDSPORELITE_VERSION mindspore-lite-1.5.0-android-aarch64)

# ============== Set MindSpore Dependencies. =============
include_directories(${CMAKE_SOURCE_DIR}/src/main/cpp/${MINDSPORELITE_VERSION})
include_directories(${CMAKE_SOURCE_DIR}/src/main/cpp/${MINDSPORELITE_VERSION}/runtime)
include_directories(${CMAKE_SOURCE_DIR}/src/main/cpp/${MINDSPORELITE_VERSION}/runtime/include)
include_directories(${CMAKE_SOURCE_DIR}/src/main/cpp/${MINDSPORELITE_VERSION}/runtime/include/dataset)
include_directories(${CMAKE_SOURCE_DIR}/src/main/cpp/${MINDSPORELITE_VERSION}/runtime/include/dataset/lite_cv)
include_directories(${CMAKE_SOURCE_DIR}/src/main/cpp/${MINDSPORELITE_VERSION}/runtime/include/schema)
include_directories(${CMAKE_SOURCE_DIR}/src/main/cpp/${MINDSPORELITE_VERSION}/runtime/include/ir/dtype)
include_directories(${CMAKE_SOURCE_DIR}/src/main/cpp/${MINDSPORELITE_VERSION}/runtime/third_party)

add_library(mindspore-lite SHARED IMPORTED)
add_library(minddata-lite SHARED IMPORTED)
add_library(libmindspore-lite-train SHARED IMPORTED)
add_library(libjpeg SHARED IMPORTED)
add_library(libturbojpeg SHARED IMPORTED)

set_target_properties(mindspore-lite PROPERTIES IMPORTED_LOCATION
        ${CMAKE_SOURCE_DIR}/src/main/cpp/${MINDSPORELITE_VERSION}/runtime/lib/libmindspore-lite.so)
set_target_properties(minddata-lite PROPERTIES IMPORTED_LOCATION
        ${CMAKE_SOURCE_DIR}/src/main/cpp/${MINDSPORELITE_VERSION}/runtime/lib/libminddata-lite.so)
set_target_properties(libmindspore-lite-train PROPERTIES IMPORTED_LOCATION
        ${CMAKE_SOURCE_DIR}/src/main/cpp/${MINDSPORELITE_VERSION}/runtime/lib/libmindspore-lite-train.so)
set_target_properties(libjpeg PROPERTIES IMPORTED_LOCATION
        ${CMAKE_SOURCE_DIR}/src/main/cpp/${MINDSPORELITE_VERSION}/runtime/third_party/libjpeg-turbo/lib/libjpeg.so)
set_target_properties(libturbojpeg PROPERTIES IMPORTED_LOCATION
        ${CMAKE_SOURCE_DIR}/src/main/cpp/${MINDSPORELITE_VERSION}/runtime/third_party/libjpeg-turbo/lib/libturbojpeg.so)

# --------------- MindSpore Lite set End. --------------------


# Creates and names a library, sets it as either STATIC
# or SHARED, and provides the relative paths to its source code.
# You can define multiple libraries, and CMake builds them for you.
# Gradle automatically packages shared libraries with your APK.

file(GLOB_RECURSE cpp_src "src/main/cpp/*.cpp" "src/main/cpp/*.h")

add_library( # Sets the name of the library.
        mlkit-label-MS

        # Sets the library as a shared library.
        SHARED

        # Provides a relative path to your source file(s).
        ${cpp_src})


# Searches for a specified prebuilt library and stores the path as a
# variable. Because CMake includes system libraries in the search path by
# default, you only need to specify the name of the public NDK library
# you want to add. CMake verifies that the library exists before
# completing its build.

find_library( # Sets the name of the path variable.
        log-lib

        # Specifies the name of the NDK library that
        # you want CMake to locate.
        log)


find_library(jnigraphics-lib jnig·raphics)

# Specifies libraries CMake should link to your target library. You
# can link multiple libraries, such as libraries you define in this
# build script, prebuilt third-party libraries, or system libraries.
add_definitions(-DMNN_USE_LOGCAT)
target_link_libraries( # Specifies the target library.
        mlkit-label-MS

        # --- mindspore ---
        minddata-lite
        mindspore-lite
        libmindspore-lite-train
        libjpeg
        libturbojpeg

        # --- other dependencies.---
        -ljnigraphics
        android

        # Links the target library to the log library
        ${log-lib}
        )