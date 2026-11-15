"""
Graphical User Interface (Tkinter / ttk) for the eSim Automated Tool Manager.
Allows one-click tool inspection, installation, updates, configuration sync, and live action logs.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from .config_handler import ESimConfigHandler
from .dependency_checker import DependencyDoctor
from .installer import ToolInstallationManager
from .updater import ToolUpdateManager


def launch_gui(config_dir: Path | None = None) -> None:
    cfg_dir = config_dir or (Path.home() / ".esim")
    doctor = DependencyDoctor()
    installer = ToolInstallationManager(esim_home=cfg_dir, dry_run=True)
    updater = ToolUpdateManager(installer=installer, doctor=doctor)
    cfg_handler = ESimConfigHandler(esim_config_dir=cfg_dir)

    root = tk.Tk()
    root.title("FOSSEE eSim Automated Tool & Dependency Manager v1.2")
    root.geometry("920x580")

    header = ttk.Label(
        root,
        text="FOSSEE eSim Automated Tool Manager — External EDA & Dependency Control Center",
        font=("Segoe UI", 12, "bold"),
    )
    header.pack(pady=8)

    cols = ("Tool", "Installed", "Detected Version", "Required", "Latest Upstream", "Binary Path")
    tree = ttk.Treeview(root, columns=cols, show="headings", height=10)
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=140)
    tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

    log_box = tk.Text(root, height=10, bg="#111827", fg="#e5e7eb", font=("Consolas", 9))
    log_box.pack(fill=tk.BOTH, expand=False, padx=12, pady=6)

    def refresh() -> None:
        for row in tree.get_children():
            tree.delete(row)
        audit = doctor.run_full_audit()
        updates = {u.name: u for u in updater.check_updates()}
        for t in audit["tools"]:
            u = updates[t.name]
            tree.insert(
                "",
                tk.END,
                values=(t.name, "YES" if t.installed else "NO", t.detected_version, t.required_version, u.latest_version, t.binary_path or "Not Found"),
            )
        if installer.log_file.exists():
            log_box.delete("1.0", tk.END)
            log_box.insert(tk.END, installer.log_file.read_text(encoding="utf-8"))

    btn_frame = ttk.Frame(root)
    btn_frame.pack(pady=6)
    ttk.Button(btn_frame, text="Refresh Status", command=refresh).pack(side=tk.LEFT, padx=6)
    ttk.Button(
        btn_frame,
        text="Sync ~/.esim/config.ini & KiCad Symbols",
        command=lambda: (cfg_handler.generate_config_ini(), refresh(), messagebox.showinfo("eSim Config", "Synchronized ~/.esim/config.ini")),
    ).pack(side=tk.LEFT, padx=6)

    refresh()
    root.mainloop()
