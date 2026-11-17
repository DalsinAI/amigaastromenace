"""AstroMenace package step: the drawer's icons, the Installer and the LhA archive."""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import lha_archive  # noqa: E402


class PackageLayoutTests(unittest.TestCase):
    def test_every_icon_is_there_and_copied(self):
        spec = json.loads((ROOT / "icons/icons.json").read_text())
        script = (ROOT / "package/build-amiga.sh").read_text()
        for icon in spec["icons"]:
            self.assertTrue((ROOT / "icons" / icon["file"]).is_file(), icon["file"])
            self.assertIn(f"icons/{icon['file']}", script)
        drawer = spec["drawer"]["file"]
        self.assertTrue((ROOT / "icons" / drawer).is_file())
        self.assertIn(f'cp icons/{drawer} "$DIST/AstroMenace.info"', script)

    def test_installer_matches_its_spec(self):
        spec = json.loads((ROOT / "package/installer.json").read_text())
        script = (ROOT / "package" / spec["script"]).read_text()
        self.assertTrue((ROOT / "package" / f"{spec['script']}.info").is_file())
        ver = re.match(r"; \$VER: (\S+) (\S+) \(", script.split("\n", 1)[0])
        self.assertEqual(ver.groups(), (spec["script"], spec["version"]))
        self.assertIn(f'(set #drawer "{spec["drawer"]}")', script)
        self.assertIn(f'(set #program "{spec["program"]}")', script)
        for module in spec["modules"]:
            self.assertIn(module, script)
        for keep in spec["keep"]:
            self.assertIn(keep, script)


class PackDistTests(unittest.TestCase):
    def dist(self, with_installer=True):
        d = Path(tempfile.mkdtemp())
        (d / "AstroMenace").mkdir()
        (d / "AstroMenace/AstroMenace").write_bytes(b"\0\0\3\xf3 launcher")
        (d / "AstroMenace.info").write_bytes((ROOT / "icons/AstroMenace-drawer.info").read_bytes())
        if with_installer:
            for name in ("Install-AstroMenace", "Install-AstroMenace.info"):
                (d / name).write_bytes((ROOT / "package" / name).read_bytes())
        return d

    def pack(self, dist):
        out = dist / "out"
        r = subprocess.run([sys.executable, str(ROOT / "tools/pack_dist.py"), "--dist", str(dist),
                            "--name", "AstroMenace", "--out", str(out)], capture_output=True, text=True, cwd=ROOT)
        return r, out

    def test_archive_root_holds_drawer_and_installer(self):
        r, out = self.pack(self.dist())
        self.assertEqual(r.returncode, 0, r.stderr)
        lha = next(out.glob("AstroMenace-git-bbdb3ac-amigaos3-68040.lha"))
        paths = [m.path for m in lha_archive.read(lha.read_bytes())]
        self.assertEqual(sorted(p for p in paths if "/" not in p),
                         ["AstroMenace.info", "Install-AstroMenace", "Install-AstroMenace.info"])
        self.assertIn("AstroMenace/AstroMenace", paths)

    def test_refuses_a_dist_without_the_installer(self):
        r, _ = self.pack(self.dist(with_installer=False))
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
