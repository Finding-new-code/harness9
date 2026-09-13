# Milestone M1 Adversarial Verification Report: Production Contracts & Schemas

**Author:** `challenger_m1_2` (Empirical Challenger / Critic & Specialist)  
**Date:** 2026-08-31  
**Milestone:** M1 (State Machine, Production Contracts & Hermes Adapter)  
**Target File:** `src/models/contracts.py` (All 17 Pydantic v2 Production Schemas)  
**Verdict:** **`REQUEST_CHANGES`**

---

## 1. Observation

Adversarial stress-testing was executed against all 17 Pydantic schemas in `src/models/contracts.py` via `tests/test_contracts_adversarial.py` (18 comprehensive test cases across malformed inputs, boundaries, regex validation, extra fields, round-trip serialization, and legacy compatibility).

While baseline validation and dictionary conversions succeed for most standard inputs, empirical testing revealed **two critical bugs**:

### Finding 1: `RecursionError` in `EditorialScorecard` composite score computation
- **Target File**: `src/models/contracts.py:274-301`
- **Mechanism**: `H9BaseModel` sets `validate_assignment=True` in its `model_config` (`src/models/contracts.py:47`). In `EditorialScorecard`, the post-validator `calculate_composite_score` checks:
  ```python
  @model_validator(mode="after")
  def calculate_composite_score(self) -> "EditorialScorecard":
      """Compute weighted composite score if not set."""
      if self.composite_score == 0.0:
          weights = { ... }
          score = ( ... )
          self.composite_score = round(max(0.0, min(1.0, score)), 4)
      return self
  ```
- **Error Observed**: When an `EditorialScorecard` is instantiated with dimensions that evaluate to `0.0` (e.g. `audience_relevance=0.0, ..., saturation_risk=1.0`), `score` evaluates to `0.0`. The assignment `self.composite_score = 0.0` triggers Pydantic v2's `validate_assignment` hook (`__pydantic_validator__.validate_assignment`), which re-runs `calculate_composite_score`. Because `self.composite_score == 0.0` remains true, it re-assigns `self.composite_score = 0.0`, resulting in an infinite recursion loop:
  ```
  File "src/models/contracts.py", line 300, in calculate_composite_score
    self.composite_score = round(max(0.0, min(1.0, score)), 4)
  File "pydantic/main.py", line 1046, in __setattr__
    setattr_handler(self, name, value)
  File "pydantic/main.py", line 112, in <lambda>
    'validate_assignment': lambda model, name, val: model.__pydantic_validator__.validate_assignment(model, name, val)
  ...
  RecursionError: maximum recursion depth exceeded
  ```
- **Reproducing Test**: `tests/test_contracts_adversarial.py::TestContractsAdversarial::test_06_reproduce_scorecard_zero_recursion_bug`

### Finding 2: `RepresenterError` on `EvaluationReport.to_yaml()` and `.save()` when using `EvaluationLayer` Enum
- **Target File**: `src/models/contracts.py:69-76`, `src/models/contracts.py:457-468`
- **Mechanism**: `EvaluationReport` defines `layer: Union[EvaluationLayer, str]`.
  `H9BaseModel.to_dict()` is implemented as:
  ```python
  def to_dict(self) -> Dict[str, Any]:
      """Convert model to standard Python dictionary."""
      return self.model_dump(mode="python")
  ```
  And `H9BaseModel.to_yaml()` is implemented as:
  ```python
  def to_yaml(self) -> str:
      """Serialize model to YAML formatted string."""
      return yaml.safe_dump(
          self.to_dict(),
          sort_keys=False,
          allow_unicode=True,
          default_flow_style=False,
      )
  ```
  Because `self.model_dump(mode="python")` preserves Python `Enum` objects (`<EvaluationLayer.RESEARCH: 'layer_1_research'>`), passing this dictionary to `yaml.safe_dump` causes PyYAML's `SafeDumper` to fail:
  ```
  yaml.representer.RepresenterError: ('cannot represent an object', <EvaluationLayer.RESEARCH: 'layer_1_research'>)
  ```
- **Impact**: Any subsystem calling `report.to_yaml()` or `report.save(out_dir, "eval_report")` on an `EvaluationReport` initialized with `layer=EvaluationLayer.RESEARCH` will crash with an unhandled exception.
- **Reproducing Test**: `tests/test_contracts_adversarial.py::TestContractsAdversarial::test_10_reproduce_evaluation_report_yaml_enum_bug`

---

## 2. Logic Chain

1. **State Machine & Contract Verification**: The 17 Pydantic schemas in `src/models/contracts.py` serve as the universal data contract across all pipeline subsystems (research, editorial, scriptwriting, voice, composition, rendering, and evaluation).
2. **Infinite Recursion Risk**: In automated editorial workflows, low-scoring candidate angles can legitimately receive 0 scores across dimensions during filtering. When `calculate_composite_score` encounters a calculated score of `0.0`, assigning to `self.composite_score` under `validate_assignment=True` exhausts Python's recursion limit and terminates the process instead of returning a valid 0-score model.
3. **YAML Serialization Invariant**: Every contract inheriting from `H9BaseModel` must support dual JSON and YAML persistence via `.save()` and `.to_yaml()`. Because `to_dict()` outputs Python `Enum` instances rather than JSON/YAML primitives, `EvaluationReport` fails the contract serialization guarantee.
4. **Actionable Remediation**:
   - For `EditorialScorecard`: Assign using `object.__setattr__(self, "composite_score", ...)` or `self.__dict__["composite_score"] = ...` to bypass `validate_assignment` recursion, or compute in a `mode="before"` validator or default factory.
   - For `H9BaseModel.to_yaml()`: Use `self.model_dump(mode="json")` or convert Enum instances to primitive values before passing to `yaml.safe_dump`.

---

## 3. Caveats

- **Legacy Model Backward Compatibility**: Legacy models (`LegacyResearchDossier`, `Claim`, `Source`, `LegacyScript`, `Storyboard`, `Beat`, etc.) were independently tested and confirmed to be fully intact and functional when imported from `src.models`.
- **Other 15 Schemas**: The remaining 15 schemas (`CreatorProfile`, `ContentBrief`, `ResearchPlan`, `ResearchDossier`, `SourceRecord`, `ClaimRecord`, `TalkingPointRecord`, `StatisticRecord`, `OutlineAct`, `ContentOutline`, `ScriptBeat`, `ScriptScene`, `Script`, `AssetRequirement`, `AssetRecord`, `RenderArtifact`, `PublishPackage`, `AnalyticsSnapshot`, `LearningCandidate`) passed all regex, boundary, missing field, extra field, and round-trip tests.

---

## 4. Conclusion

**Verdict: `REQUEST_CHANGES`**

Milestone M1 cannot be approved until the two defects in `src/models/contracts.py` are resolved:
1. Fix `calculate_composite_score` in `EditorialScorecard` to prevent `RecursionError` when `validate_assignment=True`.
2. Fix `to_yaml()` / `to_dict()` in `H9BaseModel` to ensure Enum values (e.g. `EvaluationLayer`) serialize cleanly without `yaml.representer.RepresenterError`.

---

## 5. Verification Method

To independently reproduce both defects and verify all 18 adversarial tests:

```bash
# Execute adversarial test suite
.venv\Scripts\python.exe -m unittest tests/test_contracts_adversarial.py

# Execute specific reproduction test for EditorialScorecard RecursionError
.venv\Scripts\python.exe -m unittest tests.test_contracts_adversarial.TestContractsAdversarial.test_06_reproduce_scorecard_zero_recursion_bug

# Execute specific reproduction test for EvaluationReport YAML Enum error
.venv\Scripts\python.exe -m unittest tests.test_contracts_adversarial.TestContractsAdversarial.test_10_reproduce_evaluation_report_yaml_enum_bug
```
