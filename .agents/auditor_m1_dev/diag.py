import sys
import os
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

print("Testing imports...", flush=True)

try:
    print("a. importing pydantic...", flush=True)
    import pydantic
    print("b. importing src.models.contracts...", flush=True)
    import src.models.contracts
    print("c. importing src.orchestrator.state_machine...", flush=True)
    import src.orchestrator.state_machine
    print("d. importing src.research.engine...", flush=True)
    import src.research.engine
    print("e. importing src.editorial...", flush=True)
    import src.editorial
    print("f. importing src.orchestrator.pipeline...", flush=True)
    import src.orchestrator.pipeline
    print("g. importing src.h9_runtime.types...", flush=True)
    import src.h9_runtime.types
    print("ALL PASSED!", flush=True)
except Exception as e:
    print("FAILED with exception:", e, flush=True)
