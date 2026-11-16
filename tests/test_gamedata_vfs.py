"""Synthetic, host-only tests for the AstroMenace release VFS builder."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("astro_vfs", Path(__file__).resolve().parents[1] / "build_gamedata_vfs.py")
assert SPEC and SPEC.loader
import sys
from dataclasses import dataclass
sys.modules[SPEC.name] = __import__("types").ModuleType(SPEC.name)
SPEC.loader.exec_module(sys.modules[SPEC.name])
vfs = sys.modules[SPEC.name]


def write_pack(path: Path, entries):
    records = []
    data = bytearray(b"VFS_v1.6" + struct.pack("<II", 250208, 0))
    for name, payload in entries:
        offset = len(data)
        data.extend(payload)
        records.append((name, offset, len(payload)))
    table_offset = len(data)
    for name, offset, size in records:
        nb = name.encode("utf-8")
        data.extend(struct.pack("<H", len(nb)))
        data.extend(nb)
        data.extend(struct.pack("<II", offset, size))
    struct.pack_into("<I", data, 12, table_offset)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


class VfsTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name) / "game"
        (self.root / "src/utils").mkdir(parents=True)
        (self.root / "gamedata/models").mkdir(parents=True)
        (self.root / "src/build_config.h").write_text("#define GAME_VFS_BUILD 250208\n", encoding="utf-8")
        (self.root / "src/utils/fs2vfs.cpp").write_text('const std::string GameData[] = {\n"pilot.txt",\n};\n', encoding="utf-8")
        (self.root / "gamedata/pilot.txt").write_bytes(b"pilot-data")
        write_pack(self.root / "gamedata/models/models.pack", [(f"model{i}.vw3d", bytes([i])) for i in range(100)])

    def test_end_to_end_vfs_table_roundtrip(self):
        output = self.root.parent / "out.vfs"
        vfs.build(self.root, output)
        data, entries = vfs.parse_models_pack(output)
        self.assertEqual(len(entries), 101)
        self.assertEqual(data[entries[-1][1]:entries[-1][1] + entries[-1][2]], b"pilot-data")
        self.assertEqual(entries[-1][0], "pilot.txt")

    def test_rejects_escape_in_game_data(self):
        p = self.root / "src/utils/fs2vfs.cpp"
        p.write_text('const std::string GameData[] = {\n"../../outside.txt",\n};\n')
        with self.assertRaisesRegex(RuntimeError, "unsafe"):
            vfs.build(self.root, self.root.parent / "escape.vfs")

    def test_rejects_model_table_traversal(self):
        write_pack(self.root / "gamedata/models/models.pack", [("../escape", b"bad")])
        with self.assertRaisesRegex(RuntimeError, "unsafe"):
            vfs.build(self.root, self.root.parent / "escape.vfs")

    def test_rejects_gamedata_symlink_escape(self):
        outside = self.root.parent / "outside.txt"
        outside.write_bytes(b"secret")
        (self.root / "gamedata/pilot.txt").unlink()
        (self.root / "gamedata/pilot.txt").symlink_to(outside)
        with self.assertRaisesRegex(RuntimeError, "escapes"):
            vfs.build(self.root, self.root.parent / "escape.vfs")

    def test_rejects_duplicate_models(self):
        write_pack(self.root / "gamedata/models/models.pack", [("x", b"a"), ("x", b"b")])
        with self.assertRaisesRegex(RuntimeError, "duplicate"):
            vfs.build(self.root, self.root.parent / "duplicate.vfs")

    def test_rejects_truncated_model_table(self):
        path = self.root / "gamedata/models/models.pack"
        path.write_bytes(path.read_bytes()[:-1])
        with self.assertRaises(RuntimeError):
            vfs.build(self.root, self.root.parent / "truncated.vfs")


if __name__ == "__main__":
    unittest.main()
