#!/usr/bin/env python3
"""Make the CMake AMICRADLE option visible to AstroMenace C++ sources."""

from pathlib import Path
import sys

source = Path(sys.argv[1]).resolve()
cmake = source / "CMakeLists.txt"
text = cmake.read_text(encoding="utf-8")

compile_definition = "TARGET_COMPILE_DEFINITIONS(astromenace PRIVATE AMICRADLE=1)"
link_line = (
    "TARGET_LINK_LIBRARIES(astromenace ${ALL_LIBRARIES} "
    "${AMICRADLE_PNG_LIBRARY} ${AMICRADLE_ZLIB_LIBRARY})"
)

if compile_definition not in text:
    if link_line not in text:
        raise RuntimeError("AstroMenace patched target-link marker missing")
    block = (
        "IF(AMICRADLE)\n"
        f"    {compile_definition}\n"
        "ENDIF()\n"
        f"{link_line}"
    )
    text = text.replace(link_line, block, 1)
    cmake.write_text(text, encoding="utf-8")

print("patched AstroMenace target with AMICRADLE=1 compile definition")
