"""
Automated Unit Tests for eSim Automated Tool Manager (Task 5).
Verifies Requirements 1, 2, 3, 4, 5, and 6.
"""
import tempfile
import unittest
from pathlib import Path
from esim_tool_manager.config_handler import ESimConfigHandler
from esim_tool_manager.dependency_checker import DependencyDoctor, version_satisfies
from esim_tool_manager.installer import ToolInstallationManager
from esim_tool_manager.manifest import TOOL_REGISTRY
from esim_tool_manager.updater import ToolUpdateManager
from esim_tool_manager.cli import main as cli_main


class TestESimToolManager(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.cfg_dir = Path(self.tmp_dir.name)
        self.doctor = DependencyDoctor()
        self.installer = ToolInstallationManager(esim_home=self.cfg_dir, dry_run=True)
        self.updater = ToolUpdateManager(installer=self.installer, doctor=self.doctor)
        self.cfg_handler = ESimConfigHandler(esim_config_dir=self.cfg_dir)

    def tearDown(self) -> None:
        self.installer.close()
        self.tmp_dir.cleanup()

    def test_version_satisfies(self) -> None:
        self.assertTrue(version_satisfies("8.0.8", ">=6.0.0"))
        self.assertTrue(version_satisfies("10.99.0", ">=6.0.0"))
        self.assertFalse(version_satisfies("5.1.2", ">=6.0.0"))
        self.assertFalse(version_satisfies("not-found", ">=1.0.0"))

    def test_tool_installation_dry_run_and_logging(self) -> None:
        for tool_name in TOOL_REGISTRY:
            ok, msg = self.installer.install_tool(tool_name, target_version="8.0.8" if tool_name == "kicad" else None)
            self.assertTrue(ok)
            self.assertIn("DRY-RUN", msg)
        self.assertTrue(self.installer.log_file.exists())

    def test_updater_snapshot_and_version_check(self) -> None:
        statuses = self.updater.check_updates()
        self.assertEqual(len(statuses), len(TOOL_REGISTRY))
        snap = self.updater.create_snapshot()
        self.assertIn("versions", snap)
        self.assertTrue(self.updater.snapshot_file.exists())

    def test_config_ini_and_kicad_sym_lib_table_generation(self) -> None:
        ini_path = self.cfg_handler.generate_config_ini()
        self.assertTrue(ini_path.exists())
        content = ini_path.read_text(encoding="utf-8")
        self.assertIn("[eSim]", content)
        self.assertIn("[ToolPaths]", content)
        self.assertIn("KICAD_PATH", content)

        tables = self.cfg_handler.sync_kicad_sym_lib_table(kicad_config_root=self.cfg_dir / "kicad")
        self.assertEqual(len(tables), 3)
        self.assertIn("eSim_Sources", tables[1].read_text(encoding="utf-8"))

    def test_cli_commands(self) -> None:
        for cmd in [["status"], ["doctor"], ["install", "all"], ["update"], ["configure"], ["logs"]]:
            rc = cli_main(["--dry-run", "--config-dir", str(self.cfg_dir)] + cmd)
            self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
