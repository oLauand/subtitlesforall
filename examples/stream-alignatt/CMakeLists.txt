set(TARGET stream-alignatt)

add_executable(${TARGET} main.cpp)

target_link_libraries(${TARGET} PRIVATE
    common-sdl
    common
    whisper
    ${SDL2_LIBRARIES}
)

if(SDL2_FOUND)
    target_include_directories(${TARGET} PRIVATE ${SDL2_INCLUDE_DIRS})
endif()

install(TARGETS ${TARGET} RUNTIME)
