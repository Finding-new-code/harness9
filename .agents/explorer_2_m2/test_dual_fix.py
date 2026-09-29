"""Test all 72 modules under src/ with both content.py and adapter.py fixes active."""
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_EXE = REPO_ROOT / ".venv" / "Scripts" / "python.exe"

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

runner_code_template = """
import sys, importlib.abc, importlib.util
from pathlib import Path
REPO_ROOT = Path(r"{repo_root}")
sys.path.insert(0, str(REPO_ROOT))

class DualPatchedFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname == "src.h9_runtime.content":
            origin = REPO_ROOT / "src" / "h9_runtime" / "content.py"
            return importlib.util.spec_from_file_location(
                fullname, origin, loader=PatchedContentLoader(str(origin))
            )
        elif fullname == "adapters.hyperframes.adapter":
            origin = REPO_ROOT / "adapters" / "hyperframes" / "adapter.py"
            return importlib.util.spec_from_file_location(
                fullname, origin, loader=PatchedAdapterLoader(str(origin))
            )
        return None

class PatchedContentLoader(importlib.abc.Loader):
    def __init__(self, filename): self.filename = filename
    def create_module(self, spec): return None
    def exec_module(self, module):
        with open(self.filename, "r", encoding="utf-8") as f: code = f.read()
        
        # 1. Pipeline lazy import
        code = code.replace(
            "from src.orchestrator.pipeline import Pipeline",
            "# from src.orchestrator.pipeline import Pipeline"
        )
        
        # 2. state_machine lazy import
        code = code.replace(
            "from src.orchestrator.state_machine import (\\n    ProductionState,\\n    ProductionStateMachine,\\n)",
            "# from src.orchestrator.state_machine import ProductionState, ProductionStateMachine"
        )
        
        # 3. ResearchEngine lazy import
        code = code.replace(
            "from src.research.engine import ResearchEngine",
            "# from src.research.engine import ResearchEngine"
        )
        code = code.replace(
            "        engine = ResearchEngine()",
            "        from src.research.engine import ResearchEngine\\n        engine = ResearchEngine()"
        )

        # 4. EditorialEngine lazy import
        code = code.replace(
            "from src.editorial import EditorialEngine",
            "# from src.editorial import EditorialEngine"
        )
        code = code.replace(
            "        editorial = EditorialEngine()",
            "        from src.editorial import EditorialEngine\\n        editorial = EditorialEngine()"
        )

        # Add lazy imports inside run_full_production
        target_run_prod = "        sm = ProductionStateMachine(run_id=brief.project_id)"
        lazy_sm_and_pipeline = \"\"\"        from src.orchestrator.state_machine import (
            ProductionState,
            ProductionStateMachine,
        )
        from src.orchestrator.pipeline import Pipeline
        sm = ProductionStateMachine(run_id=brief.project_id)\"\"\"
        code = code.replace(target_run_prod, lazy_sm_and_pipeline)

        compiled = compile(code, self.filename, "exec")
        exec(compiled, module.__dict__)

class PatchedAdapterLoader(importlib.abc.Loader):
    def __init__(self, filename): self.filename = filename
    def create_module(self, spec): return None
    def exec_module(self, module):
        with open(self.filename, "r", encoding="utf-8") as f: code = f.read()
        
        # Make HyperFramesGenerator lazy
        code = code.replace(
            "from src.hyperframes.generator import HyperFramesGenerator",
            "# from src.hyperframes.generator import HyperFramesGenerator"
        )
        code = code.replace(
            "        base_generator = HyperFramesGenerator(format_aspect=format_aspect)",
            "        from src.hyperframes.generator import HyperFramesGenerator\\n        base_generator = HyperFramesGenerator(format_aspect=format_aspect)"
        )

        compiled = compile(code, self.filename, "exec")
        exec(compiled, module.__dict__)

sys.meta_path.insert(0, DualPatchedFinder())
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
print(f"DUAL FIX RESULT: Total={len(modules)}, Passed={len(passed)}, Failed={len(failed)}", flush=True)
for mod, err in failed:
    print(f"  FAILED: {mod} -> {err}", flush=True)
