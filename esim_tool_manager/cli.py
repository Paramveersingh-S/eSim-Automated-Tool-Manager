"""
Requirement 5: User-Friendly Command-Line & Graphical Interface for eSim Tool Manager.
Supports: status, doctor, install, update, configure, logs, and gui.
"""
import argparse
import json
import sys
from pathlib import Path
from .config_handler import ESimConfigHandler
from .dependency_checker import DependencyDoctor
from .installer import ToolInstallationManager
from .manifest import TOOL_REGISTRY
from .updater import ToolUpdateManager


def format_table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [len(h) for h in headers]
    for r in rows:
        for i, cell in enumerate(r):
            widths[i] = max(widths[i], len(str(cell)))
    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    hdr = "| " + " | ".join(headers[i].ljust(widths[i]) for i in range(len(headers))) + " |"
    body = [
        "| " + " | ".join(str(r[i]).ljust(widths[i]) for i in range(len(headers))) + " |"
        for r in rows
    ]
    return "\n".join([sep, hdr, sep] + body + [sep])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="esim-pkg",
        description="Automated Tool, Dependency & Configuration Manager for FOSSEE eSim EDA Suite",
    )
    parser.add_argument("--dry-run", action="store_true", help="Simulate package operations without modifying system")
    parser.add_argument("--config-dir", type=Path, default=Path.home() / ".esim", help="Path to eSim configuration directory")

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="Show installed eSim external tools, versions, and update availability")
    sub.add_parser("doctor", help="Run full dependency check across external EDA binaries and Python packages")

    p_inst = sub.add_parser("install", help="Install one or all external tools required by eSim")
    p_inst.add_argument("tool", choices=list(TOOL_REGISTRY.keys()) + ["all"], help="Tool name or 'all'")
    p_inst.add_argument("--version", default=None, help="Optional version pin")

    p_upd = sub.add_parser("update", help="Check and apply updates for installed tools")
    p_upd.add_argument("--apply", action="store_true", help="Apply available updates after creating rollback snapshot")

    sub.add_parser("configure", help="Generate ~/.esim/config.ini and synchronize KiCad 6.0/8.0/9.0 sym-lib-table")
    sub.add_parser("logs", help="View recent action logs from ~/.esim/tool_manager.log")
    sub.add_parser("gui", help="Launch graphical desktop interface for eSim Tool Manager")

    args = parser.parse_args(argv)
    doctor = DependencyDoctor()
    installer = ToolInstallationManager(esim_home=args.config_dir, dry_run=args.dry_run)
    updater = ToolUpdateManager(installer=installer, doctor=doctor)
    cfg_handler = ESimConfigHandler(esim_config_dir=args.config_dir)

    if args.command == "status":
        audit = doctor.run_full_audit()
        updates = {u.name: u for u in updater.check_updates()}
        rows = []
        for t in audit["tools"]:
            u = updates[t.name]
            status_str = "INSTALLED" if t.installed else "MISSING"
            upd_str = f"YES (-> {u.latest_version})" if u.update_available else "Up-to-date"
            rows.append([t.name, status_str, t.detected_version, t.required_version, upd_str, t.binary_path or "-"])
        print("\n=== FOSSEE eSim External EDA Tool Status ===")
        print(format_table(["Tool", "State", "Detected", "Required", "Update?", "Binary Path"], rows))
        return 0

    if args.command == "doctor":
        audit = doctor.run_full_audit()
        rows = []
        for item in audit["tools"] + audit["python_packages"]:
            rows.append([
                item.name,
                item.kind,
                "PASS" if item.compatible else "WARN/FAIL",
                item.detected_version,
                item.required_version,
                item.remediation,
            ])
        print("\n=== FOSSEE eSim Dependency Doctor Diagnostic Report ===")
        print(format_table(["Component", "Type", "Health", "Detected", "Constraint", "Remediation"], rows))
        return 0

    if args.command == "install":
        targets = list(TOOL_REGISTRY.keys()) if args.tool == "all" else [args.tool]
        for t in targets:
            ok, msg = installer.install_tool(t, target_version=args.version)
            print(f"[{'OK' if ok else 'ERR'}] {t}: {msg}")
        installer.close()
        return 0

    if args.command == "update":
        statuses = updater.check_updates()
        rows = [[s.name, s.installed_version, s.latest_version, "YES" if s.update_available else "NO"] for s in statuses]
        print(format_table(["Tool", "Installed", "Upstream Latest", "Update Available"], rows))
        if args.apply:
            for res in updater.upgrade_all():
                print(" ->", res)
        installer.close()
        return 0

    if args.command == "configure":
        ini_path = cfg_handler.generate_config_ini()
        sym_paths = cfg_handler.sync_kicad_sym_lib_table(kicad_config_root=args.config_dir / "kicad_config")
        print(f"[OK] Generated eSim config: {ini_path}")
        for p in sym_paths:
            print(f"[OK] Synchronized KiCad symbol table: {p}")
        return 0

    if args.command == "logs":
        if installer.log_file.exists():
            print(installer.log_file.read_text(encoding="utf-8"))
        else:
            print("No actions logged yet.")
        return 0

    if args.command == "gui":
        from .gui import launch_gui
        launch_gui(args.config_dir)
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
