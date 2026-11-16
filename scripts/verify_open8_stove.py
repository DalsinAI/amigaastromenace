#!/usr/bin/env python3
"""Fail-closed Open8 toolchain receipt check for AstroMenace AmigaOS builds.

The core compiler/runtime files must agree with the official Open8 archive
lock. Donor NDK/SDK files are recorded in the stove receipt as *reused*;
this guard does not claim those donors were rebuilt or runtime-qualified.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys

RELEASE = "16.2.0-open8"
ARCHIVE_SHA256 = "4855915429d8d623037af5aa911b2c3dd6b3ae98eb557eb22c4e76c4fbacf31b"


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def verify(stove: Path, *, check_version: bool = True) -> dict:
    stove = stove.resolve(strict=True)
    receipt = json.loads((stove / "provenance.json").read_text(encoding="utf-8"))
    if (receipt.get("schema") != 1
            or receipt.get("release") != RELEASE
            or receipt.get("archive_sha256") != ARCHIVE_SHA256):
        raise ValueError("AstroMenace requires verified GCC 16.2.0-open8 stove")
    files = receipt.get("compiler_runtime_sha256")
    if not isinstance(files, dict) or not files:
        raise ValueError("Missing compiler/runtime provenance")
    root = stove / "prefix"
    for name, expected in files.items():
        p = PurePosixPath(name)
        if (p.is_absolute() or ".." in p.parts or p.as_posix() != name
                or len(expected) != 64):
            raise ValueError(f"Invalid compiler/runtime receipt entry: {name!r}")
        source = root / name
        if not source.is_file() or not source.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Missing or external compiler/runtime entry: {name}")
        if digest(source) != expected:
            raise ValueError(f"Compiler/runtime checksum mismatch: {name}")
    compiler = root / "bin/m68k-amigaos-g++"
    if check_version:
        result = subprocess.run([str(compiler), "--version"],
                                text=True, capture_output=True, check=True,
                                timeout=20)
        if "GFOpenAmigaGCC 16.2.0-open8" not in result.stdout.splitlines()[0]:
            raise ValueError("Wrong compiler executable version")
    print(f"ASTROMENACE_OPEN8_STOVE_PASS: {len(files)} compiler/runtime files")
    return receipt


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_open8_stove.py /path/to/open8-stove")
    try:
        verify(Path(sys.argv[1]))
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        raise SystemExit(f"ASTROMENACE_OPEN8_STOVE_FAIL: {exc}") from exc
