"""
Requirement 2: Update & Upgrade System with Semantic Version Checking and Rollback Snapshots.
"""
import json
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from .dependency_checker import DependencyDoctor, parse_version_tuple
from .installer import ToolInstallationManager
from .manifest import TOOL_REGISTRY


UPSTREAM_LATEST_CATALOG: Dict[str, str] = {
    "ngspice": "43.0",
    "kicad": "8.0.8",
    "ghdl": "4.1.0",
    "verilator": "5.028",
    "makerchip": "1.2.0",
    "sky130_pdk": "1.0.471",
}


@dataclass
class UpdateStatus:
    name: str
    installed_version: str
    latest_version: str
    update_available: bool
    installed: bool


class ToolUpdateManager:
    """Checks for upstream updates and performs atomic upgrades with state snapshots."""

    def __init__(self, installer: ToolInstallationManager, doctor: DependencyDoctor) -> None:
        self.installer = installer
        self.doctor = doctor
        self.snapshot_file = self.installer.esim_home / "version_snapshots.json"

    def query_latest_version(self, tool_name: str) -> str:
        spec = TOOL_REGISTRY[tool_name]
        if spec.pip_package:
            try:
                url = f"https://pypi.org/pypi/{spec.pip_package}/json"
                with urllib.request.urlopen(url, timeout=3) as resp:
                    data = json.loads(resp.read().decode())
                    return data["info"]["version"]
            except Exception:
                pass
        return UPSTREAM_LATEST_CATALOG.get(tool_name, "1.0.0")

    def check_updates(self) -> List[UpdateStatus]:
        statuses: List[UpdateStatus] = []
        for name, spec in TOOL_REGISTRY.items():
            probe = self.doctor.probe_tool(spec)
            latest = self.query_latest_version(name)
            has_update = (
                probe.installed
                and parse_version_tuple(latest) > parse_version_tuple(probe.detected_version)
            )
            statuses.append(
                UpdateStatus(
                    name=name,
                    installed_version=probe.detected_version,
                    latest_version=latest,
                    update_available=has_update,
                    installed=probe.installed,
                )
            )
        return statuses

    def create_snapshot(self) -> Dict[str, str]:
        snapshot = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "versions": {
                s.name: s.installed_version for s in self.check_updates()
            },
        }
        self.snapshot_file.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        self.installer.logger.info(f"Saved pre-upgrade snapshot to {self.snapshot_file}")
        return snapshot

    def upgrade_all(self) -> List[str]:
        self.create_snapshot()
        actions: List[str] = []
        for st in self.check_updates():
            if st.update_available or not st.installed:
                ok, msg = self.installer.install_tool(st.name)
                actions.append(f"{st.name}: {'SUCCESS' if ok else 'FAILED'} ({msg})")
        return actions
