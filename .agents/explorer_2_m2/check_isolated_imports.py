"""Check isolated imports for all modules in src/ and tests/."""
import importlib
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

def find_modules():
    modules = []
    src_dir = REPO_ROOT / "src"
    for p in src_dir.rglob("*.py"):
        if p.name == "__init__.py":
            rel = p.parent.relative_to(REPO_ROOT)
        else:
            rel = p.relative_to(REPO_ROOT)
        mod_parts = list(rel.parts)
        if mod_parts[-1].endswith(".py"):
            mod_parts[-1] = mod_parts[-1][:-3]
        mod_name = ".".join(mod_parts)
        modules.append(mod_name)
    return sorted(set(modules))

def test_module_import(mod_name):
    code = f"import {mod_name}; print('OK')"
    res = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    return res.returncode == 0, res.stderr.strip()

def main():
    modules = find_modules()
    print(f"Total modules to test: {len(modules)}")
    failed = []
    circular = []
    
    for mod in modules:
        success, err = test_module_import(mod)
        if not success:
            failed.append((mod, err))
            if "circular import" in err or "partially initialized" in err:
                circular.append((mod, err))
                print(f"[CIRCULAR] {mod}")
            else:
                print(f"[FAIL] {mod}: {err.splitlines()[-1] if err else 'unknown'}")
        else:
            print(f"[OK] {mod}")

    print("\n" + "="*60)
    print(f"SUMMARY: {len(modules)} modules tested. {len(failed)} failed ({len(circular)} circular).")
    for mod, err in circular:
        print(f"Circular: {mod}\n  {err.splitlines()[-1]}")
    for mod, err in failed:
        if (mod, err) not in circular:
            print(f"Other fail: {mod}\n  {err.splitlines()[-1]}")

if __name__ == "__main__":
    main()
