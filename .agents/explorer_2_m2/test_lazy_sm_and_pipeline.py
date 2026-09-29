import sys, traceback
from pathlib import Path
import importlib.abc, importlib.util

REPO_ROOT = Path(__file__).resolve().parents[2]
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
        
        # Make Pipeline lazy
        code = code.replace(
            "from src.orchestrator.pipeline import Pipeline",
            "# from src.orchestrator.pipeline import Pipeline"
        )
        
        # Make state_machine lazy
        target_sm_import = "from src.orchestrator.state_machine import (\\n    ProductionState,\\n    ProductionStateMachine,\\n)"
        code = code.replace(
            "from src.orchestrator.state_machine import (\n    ProductionState,\n    ProductionStateMachine,\n)",
            "# from src.orchestrator.state_machine import ProductionState, ProductionStateMachine"
        )
        
        # Add lazy imports inside run_full_production
        target_run_prod = "        sm = ProductionStateMachine(run_id=brief.project_id)"
        lazy_sm_and_pipeline = """        from src.orchestrator.state_machine import (
            ProductionState,
            ProductionStateMachine,
        )
        from src.orchestrator.pipeline import Pipeline
        sm = ProductionStateMachine(run_id=brief.project_id)"""
        code = code.replace(target_run_prod, lazy_sm_and_pipeline)

        compiled = compile(code, self.filename, "exec")
        exec(compiled, module.__dict__)

sys.meta_path.insert(0, PatchedContentFinder())

# Test imports
modules_to_test = [
    "src.research",
    "src.scriptwriting",
    "src.hyperframes",
    "src.editorial",
    "src.orchestrator",
    "src.orchestrator.state_machine",
    "src.orchestrator.pipeline",
]

for mod in modules_to_test:
    try:
        __import__(mod)
        print(f"SUCCESS: {mod}")
    except Exception as e:
        print(f"FAILED: {mod} -> {e}")
