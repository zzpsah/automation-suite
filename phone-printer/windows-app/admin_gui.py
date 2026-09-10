import argparse
import os
import queue
import socket
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
import traceback
import webbrowser

from PIL import Image, ImageDraw
import pystray
import uvicorn

import print_server as hub


class PhonePrinterAdmin:
    def __init__(self, root, background=False):
        self.root = root
        self.root.title("Phone Printer Hub")
        self.root.geometry("980x700")
        self.root.minsize(860, 600)
        self.log_queue = queue.Queue()
        self.last_jobs = {}
        self.server = None
        self.server_thread = None
        self.tray_icon = None
        self.background = background

        self._build_ui()
        hub.init_db()
        self._start_server()
        self._start_tray()
        self._refresh_all()

        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        if background:
            self.root.after(300, self.hide_window)

    def log(self, text):
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log_queue.put(f"[{stamp}] {text}")

    def _build_ui(self):
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="Phone Printer Hub", font=("Segoe UI", 18, "bold")).pack(side="left")
        self.server_badge = ttk.Label(top, text="Starting…")
        self.server_badge.pack(side="right")

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.dashboard = ttk.Frame(self.tabs, padding=12)
        self.printers_tab = ttk.Frame(self.tabs, padding=12)
        self.queue_tab = ttk.Frame(self.tabs, padding=12)
        self.logs_tab = ttk.Frame(self.tabs, padding=12)

        self.tabs.add(self.dashboard, text="Dashboard")
        self.tabs.add(self.printers_tab, text="Printers")
        self.tabs.add(self.queue_tab, text="Print Queue")
        self.tabs.add(self.logs_tab, text="Logs")

        self._build_dashboard()
        self._build_printers()
        self._build_queue()
        self._build_logs()

    def _build_dashboard(self):
        info = ttk.LabelFrame(self.dashboard, text="Server", padding=12)
        info.pack(fill="x", pady=(0, 12))
        self.ip_var = tk.StringVar(value="-")
        self.url_var = tk.StringVar(value="-")
        self.host_var = tk.StringVar(value=socket.gethostname())
        ttk.Label(info, text="Computer:").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        ttk.Label(info, textvariable=self.host_var).grid(row=0, column=1, sticky="w", padx=4, pady=4)
        ttk.Label(info, text="Local IP:").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        ttk.Label(info, textvariable=self.ip_var).grid(row=1, column=1, sticky="w", padx=4, pady=4)
        ttk.Label(info, text="Print URL:").grid(row=2, column=0, sticky="w", padx=4, pady=4)
        ttk.Label(info, textvariable=self.url_var).grid(row=2, column=1, sticky="w", padx=4, pady=4)
        ttk.Button(info, text="Open Browser Print Page", command=self.open_print_page).grid(row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=8)
        ttk.Label(info, text="Connect this PC to your phone's own hotspot, then open the Print URL above from the phone.", wraplength=760, justify="left", foreground="#555").grid(row=4, column=0, columnspan=2, sticky="w", padx=4, pady=(0, 4))

        startup = ttk.LabelFrame(self.dashboard, text="Background / Startup", padding=12)
        startup.pack(fill="x", pady=(0, 12))
        self.startup_var = tk.BooleanVar(value=hub.startup_installed())
        ttk.Checkbutton(startup, text="Start Phone Printer Hub automatically when I sign in", variable=self.startup_var, command=self.toggle_startup).pack(anchor="w")
        ttk.Label(startup, text="Closing this window keeps the print service running in the system tray.").pack(anchor="w", pady=(8, 0))

        actions = ttk.LabelFrame(self.dashboard, text="Actions", padding=12)
        actions.pack(fill="x")
        ttk.Button(actions, text="Refresh Everything", command=self.refresh_now).pack(side="left", padx=4)
        ttk.Button(actions, text="Show Logs", command=lambda: self.tabs.select(self.logs_tab)).pack(side="left", padx=4)
        ttk.Button(actions, text="Exit Print Hub", command=self.exit_app).pack(side="right", padx=4)

    def _build_printers(self):
        bar = ttk.Frame(self.printers_tab)
        bar.pack(fill="x", pady=(0, 8))
        ttk.Button(bar, text="Refresh Printers", command=self.refresh_printers).pack(side="left")
        self.printer_count_var = tk.StringVar(value="0 printers")
        ttk.Label(bar, textvariable=self.printer_count_var).pack(side="right")

        self.printer_tree = ttk.Treeview(self.printers_tab, columns=("status", "code"), show="headings", height=18)
        self.printer_tree.heading("status", text="Status")
        self.printer_tree.heading("code", text="Windows status code")
        self.printer_tree.column("status", width=180)
        self.printer_tree.column("code", width=180)
        self.printer_tree.pack(fill="both", expand=True)

    def _build_queue(self):
        bar = ttk.Frame(self.queue_tab)
        bar.pack(fill="x", pady=(0, 8))
        ttk.Button(bar, text="Refresh Queue", command=self.refresh_jobs).pack(side="left")
        ttk.Label(bar, text="Queue/history refreshes automatically.").pack(side="right")

        cols = ("id", "file", "printer", "source", "status", "settings", "time", "error")
        self.job_tree = ttk.Treeview(self.queue_tab, columns=cols, show="headings", height=20)
        headings = {
            "id": "Job ID", "file": "File", "printer": "Printer", "source": "Source",
            "status": "Status", "settings": "Options", "time": "Submitted", "error": "Error"
        }
        widths = {"id": 95, "file": 155, "printer": 150, "source": 100, "status": 80, "settings": 190, "time": 145, "error": 220}
        for c in cols:
            self.job_tree.heading(c, text=headings[c])
            self.job_tree.column(c, width=widths[c], minwidth=60)
        xscroll = ttk.Scrollbar(self.queue_tab, orient="horizontal", command=self.job_tree.xview)
        self.job_tree.configure(xscrollcommand=xscroll.set)
        self.job_tree.pack(fill="both", expand=True)
        xscroll.pack(fill="x")

    def _build_logs(self):
        bar = ttk.Frame(self.logs_tab)
        bar.pack(fill="x", pady=(0, 8))
        ttk.Button(bar, text="Clear Log View", command=self.clear_logs).pack(side="left")
        ttk.Button(bar, text="Refresh Status", command=self.refresh_now).pack(side="left", padx=6)
        self.log_text = tk.Text(self.logs_tab, wrap="none", font=("Consolas", 10), state="disabled")
        self.log_text.pack(fill="both", expand=True)

    def _start_server(self):
        def runner():
            try:
                self.log(f"Starting print server on 0.0.0.0:{hub.APP_PORT}")
                config = uvicorn.Config(hub.app, host="0.0.0.0", port=hub.APP_PORT, log_level="warning", log_config=None)
                self.server = uvicorn.Server(config)
                self.server.run()
            except Exception:
                self.log("SERVER ERROR:\n" + traceback.format_exc())
        self.server_thread = threading.Thread(target=runner, daemon=True)
        self.server_thread.start()

    def _start_tray(self):
        image = Image.new("RGB", (64, 64), "white")
        draw = ImageDraw.Draw(image)
        draw.rectangle((10, 20, 54, 46), outline="black", width=4)
        draw.rectangle((18, 8, 46, 28), outline="black", width=4)
        draw.rectangle((18, 40, 46, 56), outline="black", width=4)

        def show(icon, item):
            self.root.after(0, self.show_window)

        def quit_app(icon, item):
            self.root.after(0, self.exit_app)

        menu = pystray.Menu(
            pystray.MenuItem("Open Phone Printer Hub", show, default=True),
            pystray.MenuItem("Exit", quit_app),
        )
        self.tray_icon = pystray.Icon("PhonePrinterHub", image, "Phone Printer Hub", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def hide_window(self):
        self.root.withdraw()
        self.log("Admin window hidden; print service continues in background")

    def exit_app(self):
        if messagebox.askyesno("Exit Phone Printer Hub", "Stop the print service and exit?"):
            self.log("Stopping Phone Printer Hub")
            if self.server:
                self.server.should_exit = True
            if self.tray_icon:
                try:
                    self.tray_icon.stop()
                except Exception:
                    pass
            self.root.destroy()

    def open_print_page(self):
        webbrowser.open(f"http://127.0.0.1:{hub.APP_PORT}")
        self.log("Opened local browser print page")

    def toggle_startup(self):
        try:
            if self.startup_var.get():
                hub.install_startup()
                self.log("Enabled start-at-login background mode")
            else:
                hub.remove_startup()
                self.log("Disabled start-at-login")
        except Exception as exc:
            self.log(f"STARTUP ERROR: {exc}")
            messagebox.showerror("Startup", str(exc))

    def refresh_printers(self):
        try:
            names = hub.installed_printers()
            for item in self.printer_tree.get_children():
                self.printer_tree.delete(item)
            for name in names:
                detail = hub.printer_status(name)
                status = "Online / Ready" if detail.get("online") else detail.get("error", "Attention required")
                self.printer_tree.insert("", "end", text=name, values=(status, detail.get("status_code", "-")))
                # Treeview with show=headings has no visible tree text; prepend name into status via tags is awkward.
                self.printer_tree.set(self.printer_tree.get_children()[-1], "status", f"{name} — {status}")
            self.printer_count_var.set(f"{len(names)} printer(s)")
        except Exception as exc:
            self.log(f"PRINTER REFRESH ERROR: {exc}")

    def refresh_jobs(self):
        try:
            jobs = hub.get_jobs(100)
            for item in self.job_tree.get_children():
                self.job_tree.delete(item)
            current = {}
            for j in jobs:
                settings = f"{j['copies']}x | {'Color' if j['color'] else 'B/W'} | {j['duplex']} | {j['orientation']} | {j['paper_size']}"
                self.job_tree.insert("", "end", values=(j["id"], j["file_name"], j["printer"], j.get("source") or "-", j["status"], settings, j["created_at"], j.get("error") or ""))
                current[j["id"]] = j["status"]
                old = self.last_jobs.get(j["id"])
                if old is None:
                    self.log(f"Job {j['id']} queued/seen: {j['file_name']} → {j['printer']} [{j['status']}]")
                elif old != j["status"]:
                    extra = f" | error: {j.get('error')}" if j.get("error") else ""
                    self.log(f"Job {j['id']} status: {old} → {j['status']}{extra}")
            self.last_jobs = current
        except Exception as exc:
            self.log(f"QUEUE REFRESH ERROR: {exc}")

    def clear_logs(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _drain_logs(self):
        changed = False
        self.log_text.configure(state="normal")
        while True:
            try:
                line = self.log_queue.get_nowait()
            except queue.Empty:
                break
            self.log_text.insert("end", line + "\n")
            changed = True
        if changed:
            self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def refresh_now(self):
        ip = hub.local_ip()
        self.ip_var.set(ip)
        self.url_var.set(f"http://{ip}:{hub.APP_PORT}")
        if hub.server_running():
            self.server_badge.config(text=f"Server running • {ip}:{hub.APP_PORT}", foreground="#1a7f1a")
        else:
            self.server_badge.config(text="Server NOT running — check Logs tab", foreground="#c0392b")
        self.refresh_printers()
        self.refresh_jobs()
        self._drain_logs()

    def _refresh_all(self):
        self.refresh_now()
        self.root.after(2000, self._refresh_all)


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--background", action="store_true")
    args, _ = parser.parse_known_args()

    root = tk.Tk()
    app = PhonePrinterAdmin(root, background=args.background)
    app.log("Phone Printer Hub admin GUI started")
    root.mainloop()


if __name__ == "__main__":
    main()
