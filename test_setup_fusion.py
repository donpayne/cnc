"""Run with: python3 -B -m unittest test_setup_fusion"""
import tempfile
import unittest
from pathlib import Path

import setup_fusion


class FusionDataDirTest(unittest.TestCase):
    def test_fusion_data_dir_windows_uses_appdata(self):
        fusion_dir = setup_fusion.fusion_data_dir("win32", {"APPDATA": "roaming"}, Path("home"))
        self.assertEqual(fusion_dir, Path("roaming", "Autodesk", "Autodesk Fusion 360"))

    def test_fusion_data_dir_macos_uses_application_support(self):
        fusion_dir = setup_fusion.fusion_data_dir("darwin", {}, Path("home"))
        self.assertEqual(fusion_dir, Path("home", "Library", "Application Support", "Autodesk", "Autodesk Fusion 360"))

    def test_fusion_data_dir_other_platform_raises(self):
        with self.assertRaises(ValueError):
            setup_fusion.fusion_data_dir("linux", {}, Path("home"))


class InstallScriptTest(unittest.TestCase):
    def test_install_script_copies_every_file_under_scripts_folder(self):
        with tempfile.TemporaryDirectory() as fusion_dir:
            script_dir = setup_fusion.install_script(Path(fusion_dir))
            installed_names = sorted(path.name for path in script_dir.iterdir())
        self.assertEqual(script_dir.relative_to(fusion_dir), Path("API", "Scripts", "KnightBuild"))
        self.assertEqual(installed_names, sorted(path.name for path in setup_fusion.SCRIPT_FILES))

    def test_install_script_run_twice_succeeds(self):
        with tempfile.TemporaryDirectory() as fusion_dir:
            setup_fusion.install_script(Path(fusion_dir))
            setup_fusion.install_script(Path(fusion_dir))


if __name__ == "__main__":
    unittest.main()
