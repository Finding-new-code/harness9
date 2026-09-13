import sys
import os
import unittest
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

# Also ensure .venv/Scripts is in os.environ["PATH"]
venv_scripts = str(root_dir / ".venv" / "Scripts")
if venv_scripts not in os.environ.get("PATH", ""):
    os.environ["PATH"] = venv_scripts + os.pathsep + os.environ.get("PATH", "")

print("Python executable:", sys.executable, flush=True)

# 1. Test protocol imports and conformance
from src.h9_runtime import (
    AgentRuntime, DefaultAgentRuntime,
    SkillRuntime, DefaultSkillRuntime,
    ToolRuntime, DefaultToolRuntime,
    ModelRuntime, DefaultModelRuntime,
    MemoryRuntime, DefaultMemoryRuntime,
    ExecutionRuntime, DefaultExecutionRuntime,
    ContentRuntime, DefaultContentRuntime,
)

print("Checking protocol conformance...", flush=True)
assert isinstance(DefaultAgentRuntime(), AgentRuntime), "AgentRuntime failed"
assert isinstance(DefaultSkillRuntime(), SkillRuntime), "SkillRuntime failed"
assert isinstance(DefaultToolRuntime(), ToolRuntime), "ToolRuntime failed"
assert isinstance(DefaultModelRuntime(), ModelRuntime), "ModelRuntime failed"
assert isinstance(DefaultMemoryRuntime(), MemoryRuntime), "MemoryRuntime failed"
assert isinstance(DefaultExecutionRuntime(), ExecutionRuntime), "ExecutionRuntime failed"
assert isinstance(DefaultContentRuntime(), ContentRuntime), "ContentRuntime failed"
print("All 7 runtime protocols passed isinstance checks!", flush=True)

# 2. Run TestH9Runtime tests
from tests.test_h9_runtime import TestH9Runtime
suite = unittest.TestLoader().loadTestsFromTestCase(TestH9Runtime)
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
print("TEST RESULT: wasSuccessful =", result.wasSuccessful(), "runs =", result.testsRun, "failures =", len(result.failures), "errors =", len(result.errors), flush=True)
if not result.wasSuccessful():
    sys.exit(1)
print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!", flush=True)
