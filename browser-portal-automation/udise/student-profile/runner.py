from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from browseract_adapter import BrowserAct, BrowserActError
from compare import compare_profiles
from discovery import discover_one


HERE = Path(__file__).resolve().parent
DEFAULT_RUNTIME = HERE / "runtime"


def cmd_doctor(args: argparse.Namespace) -> int:
    exe = shutil.which(args.executable)
    if not exe:
        print(f"ERROR: {args.executable!r} not found in PATH.", file=sys.stderr)
        return 2
    browser = BrowserAct(session=args.session, executable=args.executable)
    try:
        print(f"BrowserAct: {browser.version()}")
        state = browser.state()
    except BrowserActError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print("Session is reachable.")
    print(state)
    return 0


def cmd_discover_one(args: argparse.Namespace) -> int:
    browser = BrowserAct(session=args.session, executable=args.executable)
    try:
        discover_one(
            browser=browser,
            student_label=args.student_label,
            runtime_dir=Path(args.runtime_dir),
        )
    except KeyboardInterrupt:
        print("\nStopped safely. Existing checkpoint/evidence was preserved.")
        return 130
    except (BrowserActError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


def _load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def cmd_compare(args: argparse.Namespace) -> int:
    portal = _load_json(args.portal_snapshot)
    source = _load_json(args.source)
    results = compare_profiles(portal, source, source_system=args.source_system)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(results)} field comparisons to {out}")
    return 0


def cmd_preview(args: argparse.Namespace) -> int:
    comparisons = _load_json(args.comparison)
    proposed = [
        row for row in comparisons
        if row.get("status") in {"MISSING_IN_PORTAL", "MINOR_VARIATION", "VALUE_DIFFERENT"}
        and row.get("proposed_value") not in (None, "")
    ]
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "mode": "PREVIEW",
        "apply_allowed": False,
        "submit_allowed": False,
        "proposed_changes": proposed,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Preview only: {len(proposed)} proposed changes written to {out}")
    print("No portal fields were modified.")
    return 0


def cmd_blocked_write(args: argparse.Namespace) -> int:
    print(
        f"{args.command.upper()} is intentionally disabled in this first-phase implementation. "
        "Use SCAN / COMPARE / PREVIEW only. A future write path must add explicit per-field "
        "approval plus a separate SUBMIT authorization gate.",
        file=sys.stderr,
    )
    return 3


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="UDISE+ individual Student GP/EP/FP automation (read-only first)."
    )
    sub = p.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="Verify BrowserAct and authenticated session reachability.")
    doctor.add_argument("--session", required=True)
    doctor.add_argument("--executable", default="browser-act")
    doctor.set_defaults(func=cmd_doctor)

    discover = sub.add_parser("discover-one", help="Guided read-only discovery for one test student.")
    discover.add_argument("--session", required=True)
    discover.add_argument("--student-label", required=True)
    discover.add_argument("--runtime-dir", default=str(DEFAULT_RUNTIME))
    discover.add_argument("--executable", default="browser-act")
    discover.set_defaults(func=cmd_discover_one)

    compare = sub.add_parser("compare", help="Compare a portal snapshot with an approved source JSON.")
    compare.add_argument("--portal-snapshot", required=True)
    compare.add_argument("--source", required=True)
    compare.add_argument("--source-system", default="approved_source")
    compare.add_argument("--output", required=True)
    compare.set_defaults(func=cmd_compare)

    preview = sub.add_parser("preview", help="Create a no-write proposed-change preview.")
    preview.add_argument("--comparison", required=True)
    preview.add_argument("--output", required=True)
    preview.set_defaults(func=cmd_preview)

    for name in ("apply", "submit"):
        blocked = sub.add_parser(name, help=f"{name.upper()} is blocked in first phase.")
        blocked.set_defaults(func=cmd_blocked_write)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
