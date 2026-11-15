"""
Requirement 1 & 6: Automated Cross-Platform Tool Installation & Package Manager Bridge.
Supports apt (Ubuntu/Debian), winget/choco (Windows), brew (macOS), and pip inside ~/.esim/env.
"""
import logging
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from .manifest import TOOL_REGISTRY, ToolSpec


class ToolInstallationManager:
    """Downloads, installs, and verifies external tools required by eSim."""

    def __init__(self, esim_home: Optional[Path] = None, dry_run: bool = False) -> None:
        self.esim_home = esim_home or Path.home() / ".esim"
        self.esim_home.mkdir(parents=True, exist_ok=True)
        self.dry_run = dry_run
        self.os_name = platform.system().lower()
        self.log_file = self.esim_home / "tool_manager.log"
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(f"esim_tool_manager_{id(self)}")
        logger.setLevel(logging.INFO)
        for h in list(logger.handlers):
            h.close()
            logger.removeHandler(h)
        fh = logging.FileHandler(self.log_file, encoding="utf-8", delay=True)
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        return logger

    def close(self) -> None:
        for h in list(self.logger.handlers):
            h.close()
            self.logger.removeHandler(h)

    def detect_package_manager(self) -> str:
        if self.os_name == "linux":
            for pm in ["apt-get", "dnf", "pacman"]:
                if shutil.which(pm):
                    return pm
        elif self.os_name == "windows":
            for pm in ["winget", "choco"]:
                if shutil.which(pm):
                    return pm
        elif self.os_name == "darwin":
            if shutil.which("brew"):
                return "brew"
        return "pip"

    def build_install_command(self, spec: ToolSpec, target_version: Optional[str] = None) -> List[str]:
        if spec.pip_package:
            pkg_arg = f"{spec.pip_package}=={target_version}" if target_version else spec.pip_package
            return [sys.executable, "-m", "pip", "install", "--upgrade", pkg_arg]

        pm = self.detect_package_manager()
        if pm == "apt-get" and spec.apt_package:
            pkg_arg = f"{spec.apt_package}={target_version}" if target_version else spec.apt_package
            return ["sudo", "apt-get", "install", "-y", pkg_arg] + spec.dependencies
        if pm == "winget" and spec.winget_id:
            cmd = ["winget", "install", "--id", spec.winget_id, "--silent", "--accept-package-agreements", "--accept-source-agreements"]
            if target_version:
                cmd.extend(["--version", target_version])
            return cmd
        if pm == "choco" and spec.choco_package:
            cmd = ["choco", "install", spec.choco_package, "-y"]
            if target_version:
                cmd.extend(["--version", target_version])
            return cmd
        if pm == "brew" and spec.brew_formula:
            return ["brew", "install", spec.brew_formula]

        return ["echo", f"Manual installation required for {spec.display_name} on {self.os_name}"]

    def install_tool(self, tool_name: str, target_version: Optional[str] = None) -> Tuple[bool, str]:
        if tool_name not in TOOL_REGISTRY:
            msg = f"Unknown tool '{tool_name}'. Available: {list(TOOL_REGISTRY.keys())}"
            self.logger.error(msg)
            return False, msg

        spec = TOOL_REGISTRY[tool_name]
        cmd = self.build_install_command(spec, target_version=target_version)
        cmd_str = " ".join(cmd)
        self.logger.info(f"Installing {spec.display_name} (command: {cmd_str})")

        if self.dry_run:
            return True, f"[DRY-RUN] Would execute: {cmd_str}"

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if proc.returncode == 0:
                self.logger.info(f"Successfully installed {spec.display_name}")
                return True, f"Installed {spec.display_name} via `{cmd_str}`"
            err = (proc.stderr or proc.stdout or "Unknown error").strip()
            self.logger.error(f"Failed to install {spec.display_name}: {err}")
            return False, err
        except Exception as exc:
            self.logger.error(f"Exception while installing {spec.display_name}: {exc}")
            return False, str(exc)
