# eSim Automated Tool Manager (`esim-tool-manager`)

**FOSSEE Winter Internship 2026 — Screening Task 5 Submission**  
**Candidate:** Paramveer Singh (Roll No: `LCO23586`, B.E. Electronics & Communication Engineering)  
**Institution:** Chandigarh College of Engineering and Technology (CCET), Panjab University, Chandigarh  
**Student Email:** `lco23586@ccetac.in` | **HOD Email:** `dssaini@ccet.ac.in`  

---

## 1. Overview & Architecture

`esim-tool-manager` (`esim-pkg`) is a cross-platform Python tool manager designed for the **FOSSEE eSim EDA Suite**. It automates the discovery, installation, semantic version verification, atomic updating with rollback snapshots, dependency health checking, and configuration synchronization (`~/.esim/config.ini` and KiCad `sym-lib-table`) for all external tools integrated with eSim:
- **Ngspice** (Analog & mixed-signal SPICE simulator)
- **KiCad EDA** (Schematic capture & PCB design, v6.0 / v8.0 / v9.0+)
- **GHDL + LLVM** (VHDL simulator for NGHDL mixed-mode co-simulation)
- **Verilator** (Verilog/SystemVerilog compiler for NgVeri)
- **Makerchip & SandPiper SaaS** (TL-Verilog integration)
- **SkyWater SKY130 PDK** (`sky130_fd_pr` 130nm CMOS primitives)

### Requirements Coverage Matrix (All 6 Requirements Implemented)

| Requirement | Module | Status | Implementation Highlights |
| :--- | :--- | :--- | :--- |
| **1. Tool Installation Management** | `esim_tool_manager/installer.py` | **Completed** | Automated OS detection, version-pinned installation, dry-run validation, and structured action logging. |
| **2. Update & Upgrade System** | `esim_tool_manager/updater.py` | **Completed** | Upstream version catalog + live PyPI JSON queries, semantic version comparison, and pre-upgrade JSON rollback snapshots (`version_snapshots.json`). |
| **3. Configuration Handling** | `esim_tool_manager/config_handler.py` | **Completed** | Generates `~/.esim/config.ini` with `[eSim]` and `[ToolPaths]` sections and synchronizes custom eSim symbol tables (`sym-lib-table`) across KiCad `6.0`, `8.0`, and `9.0`. |
| **4. Dependency Checker** | `esim_tool_manager/dependency_checker.py` | **Completed** | Pre-flight `DependencyDoctor` verifying external binaries, version constraints, and Python packages (`PyQt5`, `matplotlib`, `psutil`, `watchdog`, `hdlparse`) with actionable remediation commands. |
| **5. User Interface (CLI + GUI)** | `esim_tool_manager/cli.py`, `gui.py` | **Completed** | Full CLI (`status`, `doctor`, `install`, `update`, `configure`, `logs`) + Desktop Tkinter/ttk GUI dashboard (`gui`) and persistent audit log (`~/.esim/tool_manager.log`). |
| **6. Package Manager Integration** | `esim_tool_manager/installer.py` | **Completed** | Native dispatch for `apt-get` (Ubuntu/Debian), `winget` & `choco` (Windows), `brew` (macOS), and isolated `pip` environments. |

---

## 2. Instructions for Execution

### 2.1 Installation (Zero External Third-Party Dependencies Required for Core CLI)

```bash
git clone https://github.com/Paramveersingh-S/eSim-Automated-Tool-Manager.git
cd eSim-Automated-Tool-Manager
pip install -e .
```

### 2.2 Running the CLI Commands

```bash
# 1. Inspect installed tools, detected versions, and update availability
python -m esim_tool_manager.cli status

# 2. Run the Dependency Doctor across EDA tools and Python packages
python -m esim_tool_manager.cli doctor

# 3. Generate ~/.esim/config.ini and synchronize KiCad 6.0/8.0/9.0 sym-lib-table
python -m esim_tool_manager.cli configure

# 4. Install a specific tool or all tools (supports --dry-run and --version)
python -m esim_tool_manager.cli --dry-run install all
python -m esim_tool_manager.cli --dry-run install kicad --version 8.0.8

# 5. Check for upstream updates and create a rollback snapshot
python -m esim_tool_manager.cli --dry-run update --apply

# 6. View the action audit log
python -m esim_tool_manager.cli logs

# 7. Launch the Desktop GUI
python -m esim_tool_manager.cli gui
```

### 2.3 Running the Automated Unit Test Suite

```bash
python -m unittest discover -s tests -v
```
