from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


class BrowserActError(RuntimeError):
    pass


@dataclass
class BrowserActResult:
    command: list[str]
    stdout: str
    stderr: str
    returncode: int

    def require_ok(self) -> "BrowserActResult":
        if self.returncode != 0:
            raise BrowserActError(
                f"BrowserAct command failed ({self.returncode}): {' '.join(self.command)}\n"
                f"{self.stderr.strip()}"
            )
        return self


class BrowserAct:
    """Minimal safe wrapper around the BrowserAct CLI.

    Uses argv execution with shell=False. It never accepts or stores passwords,
    cookies, tokens, OTPs, or CAPTCHA values.
    """

    def __init__(self, session: str, executable: str = "browser-act") -> None:
        self.session = session
        self.executable = executable

    def _run(self, args: Sequence[str], timeout: int = 60) -> BrowserActResult:
        cmd = [self.executable, "--session", self.session, *args]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=False,
            timeout=timeout,
            check=False,
        )
        return BrowserActResult(
            command=cmd,
            stdout=proc.stdout,
            stderr=proc.stderr,
            returncode=proc.returncode,
        ).require_ok()

    def version(self) -> str:
        proc = subprocess.run(
            [self.executable, "--version"],
            capture_output=True,
            text=True,
            shell=False,
            timeout=30,
            check=False,
        )
        if proc.returncode != 0:
            raise BrowserActError(proc.stderr.strip() or "browser-act is unavailable")
        return proc.stdout.strip()

    def state(self) -> str:
        return self._run(["state"]).stdout

    def markdown(self) -> str:
        return self._run(["get", "markdown"]).stdout

    def wait_stable(self) -> str:
        return self._run(["wait", "stable"]).stdout

    def click(self, state_index: int) -> str:
        if state_index < 0:
            raise ValueError("state_index must be >= 0")
        return self._run(["click", str(state_index)]).stdout

    def screenshot(self, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        self._run(["screenshot", str(destination)])

    def capture(self) -> dict[str, str]:
        """Capture fresh state and rendered Markdown for evidence."""
        return {
            "state": self.state(),
            "markdown": self.markdown(),
        }

    def debug_json(self) -> str:
        return json.dumps(
            {"session": self.session, "executable": self.executable},
            indent=2,
        )
