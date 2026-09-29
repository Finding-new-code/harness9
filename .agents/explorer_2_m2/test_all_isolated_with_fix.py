"""Test all 72 modules under src/ with the content.py fix active."""
import importlib.abc
import importlib.util
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

class PatchedContentFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname == "src.h9_runtime.content":
            origin = REPO_ROOT / "src" / "h9_runtime" / "content.py"
            return importlib.util.spec_from_file_location(
                fullname,
                origin,
                loader=PatchedContentLoader(str(origin)),
            )
        return None

class PatchedContentLoader(importlib.abc.Loader):
    def __init__(self, filename):
        self.filename = filename

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        with open(self.filename, "r", encoding="utf-8") as f:
            code = f.read()

        target_top_import = "from src.orchestrator.pipeline import Pipeline"
        code = code.replace(target_top_import, "# " + target_top_import)

        target_pipeline_call = "            # Execute pipeline\n            pipeline = Pipeline("
        lazy_replacement = "            # Execute pipeline (lazy import to break circular dependency)\n            from src.orchestrator.pipeline import Pipeline\n            pipeline = Pipeline("
        code = code.replace(target_pipeline_call, lazy_replacement)

        compiled = compile(code, self.filename, "exec")
        exec(compiled, module.__dict__)

sys.meta_path.insert(0, PatchedContentFinder())

# Collect all modules
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

# In order to test isolated imports with the in-process finder,
# we need a subprocess that includes this finder, OR we test each in a fresh runner.
# Let's test by running python with -c that installs the finder and imports each module.
import subprocess

PYTHON_EXE = REPO_ROOT / ".venv" / "Scripts" / "python.exe"

runner_code_template = """
import sys, importlib.abc, importlib.util
from pathlib import Path
REPO_ROOT = Path(r"{repo_root}")
sys.path.insert(0, str(REPO_ROOT))

class PatchedContentFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname == "src.h9_runtime.content":
            origin = REPO_ROOT / "src" / "h9_runtime" / "content.py"
            return importlib.util.spec_from_file_location(
                fullname, origin, loader=PatchedContentLoader(str(origin))
            )
        return None

class PatchedContentLoader(importlib.abc.Loader):
    def __init__(self, filename): self.filename = filename
    def create_module(self, spec): return None
    def exec_module(self, module):
        with open(self.filename, "r", encoding="utf-8") as f: code = f.read()
        target_top_import = "from src.orchestrator.pipeline import Pipeline"
        code = code.replace(target_top_import, "# " + target_top_import)
        target_pipeline_call = "            # Execute pipeline\\n            pipeline = Pipeline("
        lazy_replacement = "            # Execute pipeline (lazy import to break circular dependency)\\n            from src.orchestrator.pipeline import Pipeline\\n            pipeline = Pipeline("
        code = code.replace(target_pipeline_call, lazy_replacement)
        compiled = compile(code, self.filename, "exec")
        exec(compiled, module.__dict__)

sys.meta_path.insert(0, PatchedContentFinder())
import {target_mod}
print("SUCCESS")
"""

passed = []
failed = []

for mod in modules:
    script = runner_code_template.format(repo_root=str(REPO_ROOT), target_mod=mod)
    res = subprocess.run([str(PYTHON_EXE), "-c", script], cwd=str(REPO_ROOT), capture_output=True, text=True)
    if res.returncode == 0 and "SUCCESS" in res.stdout:
        passed.append(mod)
        print(f"PASS: {mod}", flush=True)
    else:
        err = res.stderr.strip().splitlines()[-1] if res.stderr else "Unknown error"
        failed.append((mod, err))
        print(f"FAIL: {mod} -> {err}", flush=True)

print(f"\n=======================================================", flush=True)
print(f"RESULT WITH FIX: Total={len(modules)}, Passed={len(passed)}, Failed={len(failed)}", flush=True)
for mod, err in failed:
    print(f"  FAILED: {mod} -> {err}", flush=True)
