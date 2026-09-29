"""Test isolated imports of all modules with the content.py fix active."""
import importlib.abc
import importlib.util
import os
import subprocess
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

# Test importing src.orchestrator modules
orchestrator_mods = [
    "src.orchestrator",
    "src.orchestrator.cli",
    "src.orchestrator.pipeline",
    "src.orchestrator.state_machine",
]

print("=== Testing src.orchestrator modules with content.py fix ===")
for mod in orchestrator_mods:
    try:
        __import__(mod)
        print(f"PASS: {mod}")
    except Exception as e:
        print(f"FAIL: {mod} -> {e}")
