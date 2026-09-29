"""Test isolated import of every module under src/."""
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_EXE = REPO_ROOT / ".venv" / "Scripts" / "python.exe"

def main():
    src_dir = REPO_ROOT / "src"
    py_files = sorted(src_dir.rglob("*.py"))
    
    modules = []
    for p in py_files:
        rel = p.relative_to(REPO_ROOT)
        parts = list(rel.parts)
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1][:-3]
        mod = ".".join(parts)
        if mod not in modules:
            modules.append(mod)

    print(f"Discovered {len(modules)} unique modules in src/", flush=True)

    circular = []
    failed = []
    passed = []

    for idx, mod in enumerate(modules, 1):
        cmd = [str(PYTHON_EXE), "-c", f"import {mod}"]
        res = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
        if res.returncode == 0:
            passed.append(mod)
            print(f"[{idx}/{len(modules)}] PASS: {mod}", flush=True)
        else:
            err = res.stderr.strip()
            last_line = err.splitlines()[-1] if err else "Unknown error"
            if "circular import" in err or "partially initialized" in err:
                circular.append((mod, last_line, err))
                print(f"[{idx}/{len(modules)}] CIRCULAR: {mod} -> {last_line}", flush=True)
            else:
                failed.append((mod, last_line, err))
                print(f"[{idx}/{len(modules)}] FAIL: {mod} -> {last_line}", flush=True)

    print("\n" + "="*70, flush=True)
    print(f"SUMMARY: Total={len(modules)}, Passed={len(passed)}, Circular={len(circular)}, Failed={len(failed)}", flush=True)
    print("\nCircular Import Modules:", flush=True)
    for mod, last, full in circular:
        print(f"  - {mod}: {last}", flush=True)
    print("\nFailed Modules:", flush=True)
    for mod, last, full in failed:
        print(f"  - {mod}: {last}", flush=True)

if __name__ == "__main__":
    main()
