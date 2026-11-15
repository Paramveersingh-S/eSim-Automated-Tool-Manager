"""
Requirement 4: Automated Dependency Checker & Diagnostics Doctor for eSim.
Verifies Python libraries, system shared libraries, compiler toolchains, and external EDA binaries.
"""
import importlib.metadata
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from .manifest import TOOL_REGISTRY, ToolSpec


@dataclass
class CheckResult:
    name: str
    kind: str  # "tool", "python_pkg", "system_lib"
    installed: bool
    detected_version: str
    required_version: str
    compatible: bool
    binary_path: str
    remediation: str


PYTHON_DEPENDENCIES: Dict[str, str] = {
    "PyQt5": ">=5.15.0",
    "matplotlib": ">=3.5.0",
    "psutil": ">=5.8.0",
    "watchdog": ">=2.1.0",
    "hdlparse": ">=1.0.0",
    "setuptools": ">=60.0.0",
}


def parse_version_tuple(v_str: str) -> Tuple[int, ...]:
    nums = re.findall(r"\d+", v_str or "")
    return tuple(int(x) for x in nums[:3]) if nums else (0, 0, 0)


def version_satisfies(detected: str, constraint: str) -> bool:
    if not detected or detected == "not-found":
        return False
    clean_req = re.sub(r"^[><=~!]+", "", constraint).strip()
    det_t = parse_version_tuple(detected)
    req_t = parse_version_tuple(clean_req)
    if constraint.startswith(">="):
        return det_t >= req_t
    if constraint.startswith("=="):
        return det_t == req_t
    return det_t >= req_t


class DependencyDoctor:
    """Runs comprehensive pre-flight and post-install diagnostics for eSim."""

    def __init__(self) -> None:
        self.os_name = platform.system().lower()

    def probe_tool(self, spec: ToolSpec) -> CheckResult:
        # 1. Check PATH first, then OS-specific default paths
        bin_path = shutil.which(spec.binary_name)
        if not bin_path:
            candidate = spec.default_paths.get(self.os_name, "")
            if candidate and os.path.exists(candidate):
                bin_path = candidate

        # Special directory check for SKY130 PDK
        if spec.name == "sky130_pdk":
            pdk_path = bin_path or spec.default_paths.get(self.os_name, "")
            if pdk_path and os.path.exists(pdk_path):
                return CheckResult(
                    name=spec.name,
                    kind="tool",
                    installed=True,
                    detected_version="1.0.0",
                    required_version=spec.required_version,
                    compatible=True,
                    binary_path=pdk_path,
                    remediation="OK",
                )
            return CheckResult(
                name=spec.name,
                kind="tool",
                installed=False,
                detected_version="not-found",
                required_version=spec.required_version,
                compatible=False,
                binary_path="",
                remediation="Run: esim-pkg install sky130_pdk",
            )

        if not bin_path:
            return CheckResult(
                name=spec.name,
                kind="tool",
                installed=False,
                detected_version="not-found",
                required_version=spec.required_version,
                compatible=False,
                binary_path="",
                remediation=f"Run: esim-pkg install {spec.name}",
            )

        detected_ver = "unknown"
        if spec.version_args:
            try:
                proc = subprocess.run(
                    [bin_path] + spec.version_args,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                out = (proc.stdout or "") + "\n" + (proc.stderr or "")
                m = re.search(spec.version_regex, out, re.IGNORECASE)
                if m:
                    detected_ver = m.group(1)
                else:
                    first_line = out.strip().splitlines()[0] if out.strip() else "1.0.0"
                    nums = re.search(r"(\d+\.\d+(?:\.\d+)?)", first_line)
                    detected_ver = nums.group(1) if nums else "1.0.0"
            except Exception:
                detected_ver = "1.0.0"

        compat = version_satisfies(detected_ver, spec.required_version)
        remed = "OK" if compat else f"Upgrade required ({detected_ver} < {spec.required_version}): esim-pkg update {spec.name}"
        return CheckResult(
            name=spec.name,
            kind="tool",
            installed=True,
            detected_version=detected_ver,
            required_version=spec.required_version,
            compatible=compat,
            binary_path=bin_path,
            remediation=remed,
        )

    def check_python_dependencies(self) -> List[CheckResult]:
        results: List[CheckResult] = []
        for pkg, req in PYTHON_DEPENDENCIES.items():
            try:
                ver = importlib.metadata.version(pkg)
                compat = version_satisfies(ver, req)
                results.append(
                    CheckResult(
                        name=pkg,
                        kind="python_pkg",
                        installed=True,
                        detected_version=ver,
                        required_version=req,
                        compatible=compat,
                        binary_path=sys.executable,
                        remediation="OK" if compat else f"pip install --upgrade '{pkg}{req}'",
                    )
                )
            except importlib.metadata.PackageNotFoundError:
                results.append(
                    CheckResult(
                        name=pkg,
                        kind="python_pkg",
                        installed=False,
                        detected_version="not-found",
                        required_version=req,
                        compatible=False,
                        binary_path="",
                        remediation=f"pip install '{pkg}{req}'",
                    )
                )
        return results

    def run_full_audit(self) -> Dict[str, List[CheckResult]]:
        tools = [self.probe_tool(spec) for spec in TOOL_REGISTRY.values()]
        py_pkgs = self.check_python_dependencies()
        return {"tools": tools, "python_packages": py_pkgs}
