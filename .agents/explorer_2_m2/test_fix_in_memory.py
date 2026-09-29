"""Test the circular import fix in memory using importlib hooks."""
import importlib.abc
import importlib.util
import os
import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

class PatchedContentFinder(importlib.abc.MetaPathFinder):
    """Custom finder that intercepts src.h9_runtime.content and applies the fix in memory."""
    
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
        return None  # default module creation

    def exec_module(self, module):
        with open(self.filename, "r", encoding="utf-8") as f:
            code = f.read()

        # Check line 37
        target_top_import = "from src.orchestrator.pipeline import Pipeline"
        if target_top_import not in code:
            raise RuntimeError("Could not find target top import in content.py")

        # Comment out the top-level import
        code = code.replace(target_top_import, "# " + target_top_import)

        # Ensure lazy import inside run_full_production
        # Line 345 is: pipeline = Pipeline(
        target_pipeline_call = "            # Execute pipeline\n            pipeline = Pipeline("
        lazy_replacement = "            # Execute pipeline (lazy import to break circular dependency)\n            from src.orchestrator.pipeline import Pipeline\n            pipeline = Pipeline("
        if target_pipeline_call not in code:
            raise RuntimeError("Could not find target pipeline call in run_full_production")
        code = code.replace(target_pipeline_call, lazy_replacement)

        compiled = compile(code, self.filename, "exec")
        exec(compiled, module.__dict__)

# Install the finder at the very beginning of sys.meta_path
sys.meta_path.insert(0, PatchedContentFinder())

print("Testing isolated import of src.orchestrator.state_machine...")
from src.orchestrator.state_machine import ProductionState, ProductionStateMachine
print(f"Successfully imported state_machine! Initial state: {ProductionState.CREATED}")

print("\nTesting isolated import of src.orchestrator.pipeline...")
from src.orchestrator.pipeline import Pipeline
print(f"Successfully imported Pipeline! Class: {Pipeline}")

print("\nRunning test_state_machine suite with patched in-memory content.py...")
loader = unittest.TestLoader()
suite = loader.discover(start_dir=str(REPO_ROOT / "tests"), pattern="test_state_machine.py")
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
print(f"\nTest results: ran={result.testsRun}, errors={len(result.errors)}, failures={len(result.failures)}")

if not result.wasSuccessful():
    sys.exit(1)
print("ALL TESTS PASSED IN ISOLATION!")
