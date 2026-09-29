"""Test if making ResearchEngine and EditorialEngine lazy in content.py fixes src.editorial and src.research."""
import importlib.abc
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_EXE = REPO_ROOT / ".venv" / "Scripts" / "python.exe"

test_code = """
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
        
        # 1. Pipeline lazy import
        code = code.replace("from src.orchestrator.pipeline import Pipeline", "# from src.orchestrator.pipeline import Pipeline")
        code = code.replace("pipeline = Pipeline(", "from src.orchestrator.pipeline import Pipeline\\n            pipeline = Pipeline(")
        
        # 2. ResearchEngine lazy import
        code = code.replace("from src.research.engine import ResearchEngine", "# from src.research.engine import ResearchEngine")
        code = code.replace("engine = ResearchEngine()", "from src.research.engine import ResearchEngine\\n        engine = ResearchEngine()")
        
        # 3. EditorialEngine lazy import
        code = code.replace("from src.editorial import EditorialEngine", "# from src.editorial import EditorialEngine")
        code = code.replace("editorial = EditorialEngine()", "from src.editorial import EditorialEngine\\n        editorial = EditorialEngine()")

        compiled = compile(code, self.filename, "exec")
        exec(compiled, module.__dict__)

sys.meta_path.insert(0, PatchedContentFinder())
import {target_mod}
print("SUCCESS")
"""

target_mods = [
    "src.editorial",
    "src.editorial.angle_generator",
    "src.research",
    "src.research.engine",
    "src.orchestrator.pipeline",
    "src.orchestrator.state_machine",
]

for mod in target_mods:
    script = test_code.format(repo_root=str(REPO_ROOT), target_mod=mod)
    res = subprocess.run([str(PYTHON_EXE), "-c", script], cwd=str(REPO_ROOT), capture_output=True, text=True)
    if res.returncode == 0 and "SUCCESS" in res.stdout:
        print(f"PASS: {mod}")
    else:
        err = res.stderr.strip().splitlines()[-1] if res.stderr else "Unknown error"
        print(f"FAIL: {mod} -> {err}")
