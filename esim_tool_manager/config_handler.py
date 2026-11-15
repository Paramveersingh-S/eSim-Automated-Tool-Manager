"""
Requirement 3: Automated Configuration & Environment Path Handler for eSim.
Manages ~/.esim/config.ini, KiCad 6.0/8.0/9.0 sym-lib-table, and environment variables.
"""
import configparser
import os
import platform
from pathlib import Path
from typing import Dict, Optional
from .dependency_checker import DependencyDoctor
from .manifest import TOOL_REGISTRY


ESIM_CUSTOM_SYMBOLS = [
    ("eSim_Sources", "eSim_Sources.kicad_sym", "eSim Custom Voltage/Current Sources"),
    ("eSim_Devices", "eSim_Devices.kicad_sym", "eSim Semiconductor & Behavioral Devices"),
    ("eSim_Plot", "eSim_Plot.kicad_sym", "eSim Interactive Waveform Plot Markers"),
    ("eSim_Subckt", "eSim_Subckt.kicad_sym", "eSim Hierarchical Subcircuit Blocks"),
    ("eSim_Hybrid", "eSim_Hybrid.kicad_sym", "eSim NGHDL / NgVeri Digital-Analog Blocks"),
    ("sky130_fd_pr", "sky130_fd_pr.kicad_sym", "SkyWater 130nm CMOS PDK Primitives"),
]


class ESimConfigHandler:
    """Automates ~/.esim/config.ini generation, tool path binding, and KiCad symbol tables."""

    def __init__(self, esim_config_dir: Optional[Path] = None, esim_source_root: Optional[Path] = None) -> None:
        self.config_dir = esim_config_dir or (Path.home() / ".esim")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.config_dir / "config.ini"
        self.esim_source_root = esim_source_root or Path("/opt/eSim")
        self.doctor = DependencyDoctor()

    def generate_config_ini(self, custom_overrides: Optional[Dict[str, str]] = None) -> Path:
        cfg = configparser.ConfigParser(interpolation=None)
        cfg.optionxform = str  # preserve exact key case expected by eSim Application.py

        cfg["eSim"] = {
            "eSim_HOME": str(self.esim_source_root),
            "LICENSE": "%(eSim_HOME)s/LICENSE",
            "KicadLib": "%(eSim_HOME)s/library/kicadLibrary.tar.xz",
            "IMAGES": "%(eSim_HOME)s/images",
            "VERSION": "%(eSim_HOME)s/VERSION",
            "MODELICA_MAP_JSON": "%(eSim_HOME)s/library/ngspicetoModelica/Mapping.json",
        }

        cfg["ToolPaths"] = {}
        for name, spec in TOOL_REGISTRY.items():
            probe = self.doctor.probe_tool(spec)
            key = spec.config_key or f"{name.upper()}_PATH"
            cfg["ToolPaths"][key] = probe.binary_path or spec.default_paths.get(platform.system().lower(), "")

        if custom_overrides:
            for k, v in custom_overrides.items():
                cfg["ToolPaths"][k] = v

        with open(self.config_path, "w", encoding="utf-8") as f:
            cfg.write(f)
        return self.config_path

    def sync_kicad_sym_lib_table(self, kicad_config_root: Optional[Path] = None) -> list[Path]:
        if kicad_config_root is None:
            if platform.system().lower() == "windows":
                kicad_config_root = Path(os.environ.get("APPDATA", str(Path.home()))) / "kicad"
            else:
                kicad_config_root = Path.home() / ".config" / "kicad"

        symbol_dir = "/usr/share/kicad/symbols" if platform.system().lower() != "windows" else "${KICAD8_SYMBOL_DIR}"
        written_files: list[Path] = []

        for ver in ["6.0", "8.0", "9.0"]:
            ver_dir = kicad_config_root / ver
            ver_dir.mkdir(parents=True, exist_ok=True)
            table_file = ver_dir / "sym-lib-table"

            lines = ["(sym_lib_table", "  (version 7)"]
            for lib_name, file_name, descr in ESIM_CUSTOM_SYMBOLS:
                uri = f"{symbol_dir}/{file_name}"
                lines.append(
                    f'  (lib (name "{lib_name}")(type "KiCad")(uri "{uri}")(options "")(descr "{descr}"))'
                )
            lines.append(")")
            table_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
            written_files.append(table_file)

        return written_files
