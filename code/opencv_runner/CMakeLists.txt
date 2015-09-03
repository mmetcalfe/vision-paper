cmake_minimum_required(VERSION 2.8)
project(opencv_runner)

# Compiler settings
SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11 -O3")

# Shared libraries
FIND_PACKAGE(OpenCV REQUIRED)
FIND_PACKAGE(Boost COMPONENTS system filesystem REQUIRED)

INCLUDE_DIRECTORIES({$OpenCV_INCLUDE_DIRS} REQUIRED)
INCLUDE_DIRECTORIES(${Boost_INCLUDE_DIR} REQUIRED)

SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")

FILE(GLOB src_files "*.cpp" "*.h")

ADD_EXECUTABLE(opencv_runner ${src_files})
SET_TARGET_PROPERTIES(opencv_runner PROPERTIES LINKER_LANGUAGE CXX)
TARGET_LINK_LIBRARIES(opencv_runner
    ${OpenCV_LIBS}
    ${Boost_FILESYSTEM_LIBRARY}
    ${Boost_SYSTEM_LIBRARY}
    )
