"""
Declarative Tool & Dependency Registry for eSim EDA Suite.
Covers Ngspice, KiCad, GHDL, Verilator, Makerchip, SandPiper SaaS, SKY130 PDK, and OpenModelica.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ToolSpec:
    name: str
    display_name: str
    category: str
    required_version: str
    binary_name: str
    version_args: List[str]
    version_regex: str
    apt_package: Optional[str] = None
    winget_id: Optional[str] = None
    choco_package: Optional[str] = None
    brew_formula: Optional[str] = None
    pip_package: Optional[str] = None
    config_key: Optional[str] = None
    default_paths: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    description: str = ""


TOOL_REGISTRY: Dict[str, ToolSpec] = {
    "ngspice": ToolSpec(
        name="ngspice",
        display_name="Ngspice Mixed-Level Circuit Simulator",
        category="Analog / Mixed-Signal Simulation",
        required_version=">=36.0",
        binary_name="ngspice",
        version_args=["--version"],
        version_regex=r"ngspice-(\d+(?:\.\d+)?)",
        apt_package="ngspice",
        winget_id="Ngspice.Ngspice",
        choco_package="ngspice",
        brew_formula="ngspice",
        config_key="NGSPICE_PATH",
        default_paths={
            "linux": "/usr/bin/ngspice",
            "windows": r"C:\Program Files\Spice64\bin\ngspice.exe",
            "darwin": "/opt/homebrew/bin/ngspice",
        },
        dependencies=["libreadline-dev", "libncurses-dev", "libxaw7-dev", "libfftw3-dev"],
        description="Open-source SPICE simulator for analog and mixed-signal circuit analysis in eSim.",
    ),
    "kicad": ToolSpec(
        name="kicad",
        display_name="KiCad EDA Schematic & PCB Suite",
        category="Schematic Capture & PCB Layout",
        required_version=">=6.0.0",
        binary_name="kicad-cli",
        version_args=["--version"],
        version_regex=r"(\d+\.\d+(?:\.\d+)?)",
        apt_package="kicad",
        winget_id="KiCad.KiCad",
        choco_package="kicad",
        brew_formula="kicad",
        config_key="KICAD_PATH",
        default_paths={
            "linux": "/usr/bin/kicad",
            "windows": r"C:\Program Files\KiCad\10.99\bin\kicad-cli.exe",
            "darwin": "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
        },
        dependencies=["kicad-symbols", "kicad-footprints", "kicad-templates"],
        description="Schematic capture (Eeschema) and multi-layer PCB layout engine integrated with eSim.",
    ),
    "ghdl": ToolSpec(
        name="ghdl",
        display_name="GHDL VHDL Simulator (LLVM Backend)",
        category="Digital / VHDL Co-Simulation (NGHDL)",
        required_version=">=2.0.0",
        binary_name="ghdl",
        version_args=["--version"],
        version_regex=r"GHDL\s+(\d+\.\d+(?:\.\d+)?)",
        apt_package="ghdl-llvm",
        choco_package="ghdl",
        brew_formula="ghdl",
        config_key="GHDL_PATH",
        default_paths={
            "linux": "/usr/bin/ghdl",
            "windows": r"C:\GHDL\bin\ghdl.exe",
            "darwin": "/opt/homebrew/bin/ghdl",
        },
        dependencies=["llvm-18", "llvm-18-dev", "clang", "zlib1g-dev"],
        description="Open-source analyzer, compiler, and simulator for VHDL used by eSim NGHDL.",
    ),
    "verilator": ToolSpec(
        name="verilator",
        display_name="Verilator Verilog/SystemVerilog Compiler",
        category="Digital / Verilog Co-Simulation (NgVeri)",
        required_version=">=4.200",
        binary_name="verilator",
        version_args=["--version"],
        version_regex=r"Verilator\s+(\d+\.\d+)",
        apt_package="verilator",
        choco_package="verilator",
        brew_formula="verilator",
        config_key="VERILATOR_PATH",
        default_paths={
            "linux": "/usr/bin/verilator",
            "windows": r"C:\msys64\mingw64\bin\verilator.exe",
            "darwin": "/opt/homebrew/bin/verilator",
        },
        dependencies=["flex", "bison", "build-essential", "libfl-dev"],
        description="High-performance Verilog/SystemVerilog cycle-accurate simulator powering eSim NgVeri.",
    ),
    "makerchip": ToolSpec(
        name="makerchip",
        display_name="Makerchip IDE & SandPiper TL-Verilog",
        category="TL-Verilog & NgVeri Integration",
        required_version=">=1.0.0",
        binary_name="makerchip",
        version_args=["--version"],
        version_regex=r"(\d+\.\d+(?:\.\d+)?)",
        pip_package="makerchip-app",
        config_key="MAKERCHIP_PATH",
        dependencies=["sandpiper-saas", "hdlparse", "watchdog"],
        description="Transaction-Level Verilog (TL-Verilog) integration and cloud/local compiler for NgVeri.",
    ),
    "sky130_pdk": ToolSpec(
        name="sky130_pdk",
        display_name="SkyWater SKY130 Open Source PDK",
        category="IC / CMOS Process Design Kit",
        required_version=">=1.0.0",
        binary_name="sky130_fd_pr",
        version_args=[],
        version_regex=r"(\d+\.\d+)",
        config_key="SKY130_PDK_PATH",
        default_paths={
            "linux": "/usr/share/local/sky130_fd_pr",
            "windows": r"C:\eSim\library\sky130_fd_pr",
            "darwin": "/usr/local/share/sky130_fd_pr",
        },
        dependencies=[],
        description="Google + SkyWater 130nm CMOS Process Design Kit primitive models for eSim.",
    ),
}
