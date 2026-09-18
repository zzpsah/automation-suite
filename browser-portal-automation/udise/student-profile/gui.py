from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "runner.py"
RUNTIME = HERE / "runtime"


class StudentProfileApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("UDISE+ Student Profile Automation")
        self.geometry("920x650")
        self.minsize(820, 560)

        self.session_var = tk.StringVar(value="udise-profile")
        self.student_var = tk.StringVar(value="TEST-STUDENT")
        self.status_var = tk.StringVar(value="Ready")
        self._build_ui()

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)

        title = ttk.Label(root, text="UDISE+ Student Profile Automation", font=("Segoe UI", 18, "bold"))
        title.pack(anchor="w")

        subtitle = ttk.Label(
            root,
            text="General Profile (GP) · Education Profile (EP) · Facility Profile (FP)",
        )
        subtitle.pack(anchor="w", pady=(2, 14))

        note = ttk.Label(
            root,
            text=(
                "Login/CAPTCHA/OTP manually complete karein. "
                "Current build read-only discovery + compare/preview ke liye hai."
            ),
            wraplength=850,
        )
        note.pack(anchor="w", pady=(0, 14))

        setup = ttk.LabelFrame(root, text="Connection", padding=12)
        setup.pack(fill="x")

        ttk.Label(setup, text="BrowserAct session").grid(row=0, column=0, sticky="w")
        ttk.Entry(setup, textvariable=self.session_var, width=28).grid(row=0, column=1, sticky="w", padx=(8, 16))
        ttk.Button(setup, text="1. Check Connection", command=self.doctor).grid(row=0, column=2, sticky="w")

        ttk.Label(setup, text="Student label").grid(row=1, column=0, sticky="w", pady=(10, 0))
        ttk.Entry(setup, textvariable=self.student_var, width=28).grid(row=1, column=1, sticky="w", padx=(8, 16), pady=(10, 0))
        ttk.Button(setup, text="2. Start GP/EP/FP Discovery", command=self.start_discovery).grid(
            row=1, column=2, sticky="w", pady=(10, 0)
        )

        actions = ttk.LabelFrame(root, text="Read-only tools", padding=12)
        actions.pack(fill="x", pady=(14, 0))

        ttk.Button(actions, text="Compare Portal vs Source", command=self.compare).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(actions, text="Create Preview", command=self.preview).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(actions, text="Open Runtime Folder", command=self.open_runtime).grid(row=0, column=2, padx=(0, 8))

        ttk.Button(actions, text="APPLY (disabled)", state="disabled").grid(row=1, column=0, pady=(10, 0), padx=(0, 8))
        ttk.Button(actions, text="SUBMIT (disabled)", state="disabled").grid(row=1, column=1, pady=(10, 0), padx=(0, 8))

        status_box = ttk.LabelFrame(root, text="Status / Output", padding=10)
        status_box.pack(fill="both", expand=True, pady=(14, 0))

        self.output = tk.Text(status_box, wrap="word", height=18, font=("Consolas", 10))
        self.output.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(status_box, orient="vertical", command=self.output.yview)
        scroll.pack(side="right", fill="y")
        self.output.configure(yscrollcommand=scroll.set)

        bottom = ttk.Frame(root)
        bottom.pack(fill="x", pady=(10, 0))
        ttk.Label(bottom, textvariable=self.status_var).pack(side="left")
        ttk.Button(bottom, text="Clear", command=lambda: self.output.delete("1.0", "end")).pack(side="right")

        self._log(
            "Use flow:\n"
            "1) BrowserAct-controlled Chrome me UDISE login karo.\n"
            "2) Check Connection.\n"
            "3) Student label do aur Start Discovery click karo.\n"
            "4) Ek PowerShell window khulega jahan current BrowserAct indexes enter karne honge.\n"
        )

    def _log(self, text: str) -> None:
        self.output.insert("end", text.rstrip() + "\n")
        self.output.see("end")

    def _thread_log(self, text: str) -> None:
        self.after(0, self._log, text)

    def _thread_status(self, text: str) -> None:
        self.after(0, self.status_var.set, text)

    def _python_cmd(self, *args: str) -> list[str]:
        return [sys.executable, str(RUNNER), *args]

    def _run_capture(self, args: list[str], label: str) -> None:
        def worker() -> None:
            self._thread_status(label)
            self._thread_log(f"> {' '.join(args)}")
            try:
                proc = subprocess.run(
                    args,
                    cwd=str(HERE),
                    capture_output=True,
                    text=True,
                    shell=False,
                    check=False,
                )
                if proc.stdout:
                    self._thread_log(proc.stdout)
                if proc.stderr:
                    self._thread_log(proc.stderr)
                self._thread_log(f"Exit code: {proc.returncode}")
            except Exception as exc:
                self._thread_log(f"ERROR: {exc}")
            finally:
                self._thread_status("Ready")

        threading.Thread(target=worker, daemon=True).start()

    def doctor(self) -> None:
        session = self.session_var.get().strip()
        if not session:
            messagebox.showerror("Missing session", "BrowserAct session name required.")
            return
        self._run_capture(
            self._python_cmd("doctor", "--session", session),
            "Checking BrowserAct session…",
        )

    def start_discovery(self) -> None:
        session = self.session_var.get().strip()
        student = self.student_var.get().strip()
        if not session or not student:
            messagebox.showerror("Missing value", "Session and student label are required.")
            return

        cmd = self._python_cmd(
            "discover-one",
            "--session",
            session,
            "--student-label",
            student,
        )

        if os.name == "nt":
            # Discovery is interactive, so open a real console window for index prompts.
            interactive = ["cmd.exe", "/k", subprocess.list2cmdline(cmd)]
            try:
                subprocess.Popen(interactive, cwd=str(HERE), shell=False)
                self._log("Interactive discovery PowerShell opened.")
                self._log("Us window me current BrowserAct state index enter karein.")
                self.status_var.set("Discovery running in PowerShell")
            except Exception as exc:
                messagebox.showerror("Could not start discovery", str(exc))
        else:
            try:
                subprocess.Popen(cmd, cwd=str(HERE))
                self._log("Interactive discovery started in a separate process.")
            except Exception as exc:
                messagebox.showerror("Could not start discovery", str(exc))

    def compare(self) -> None:
        portal = filedialog.askopenfilename(
            title="Select portal snapshot JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not portal:
            return
        source = filedialog.askopenfilename(
            title="Select approved source JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not source:
            return
        output = filedialog.asksaveasfilename(
            title="Save comparison JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile="comparison.private.json",
        )
        if not output:
            return
        self._run_capture(
            self._python_cmd(
                "compare",
                "--portal-snapshot",
                portal,
                "--source",
                source,
                "--output",
                output,
            ),
            "Comparing…",
        )

    def preview(self) -> None:
        comparison = filedialog.askopenfilename(
            title="Select comparison JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not comparison:
            return
        output = filedialog.asksaveasfilename(
            title="Save preview JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile="preview.private.json",
        )
        if not output:
            return
        self._run_capture(
            self._python_cmd(
                "preview",
                "--comparison",
                comparison,
                "--output",
                output,
            ),
            "Creating preview…",
        )

    def open_runtime(self) -> None:
        RUNTIME.mkdir(parents=True, exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(RUNTIME)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(RUNTIME)])
            else:
                subprocess.Popen(["xdg-open", str(RUNTIME)])
        except Exception as exc:
            messagebox.showerror("Could not open folder", str(exc))


if __name__ == "__main__":
    StudentProfileApp().mainloop()
