# Milestone 2 Empirical Challenge Report (Challenger 2)

**Target**: Milestone 2 — Asset Discovery, Rights Ledger & Local Freezing (R2)  
**Evaluator**: Challenger 2 (Empirical Challenger)  
**Date**: 2026-08-31  
**Verdict**: **`REQUEST_CHANGES`**  
**Overall Risk Assessment**: **HIGH**

---

## 1. Executive Summary

An exhaustive empirical challenge was conducted against `src/assets/ledger.py`, `src/assets/pipeline.py`, `src/assets/freezer.py`, `src/assets/procedural.py`, and `src/models/ledger.py`. A dedicated 15-test adversarial test harness (`tests/test_m2_challenger2_stress.py`) was constructed and executed alongside the full test suite.

### Key Verification Verdicts:
1. **SHA-256 Byte-Level Exactness**: **PASS**. 100% of frozen assets on disk match ledger `file_sha256` and exact `file_size_bytes`. Tamper detection and chunk boundary hashing (0B to 1MB) verified.
2. **License Metadata Completeness**: **CONDITIONAL PASS / BUG IDENTIFIED**. Under offline/procedural generation, all required fields (`license_type`, `attribution_text`, `source_url`, `creator`) are populated. However, an adversarial failure scenario revealed **rights provenance contamination** during online candidate download failures.
3. **Dual JSON/YAML Ledger Roundtripping Parity**: **PASS**. Full bidirectional serialization and deserialization parity confirmed between Python dataclasses, `.json`, and `.yaml` formats with type and unicode preservation.
4. **Procedural Vector Generator XML Well-Formedness**: **FAIL (CRITICAL BUG)**. All procedural SVG graphics generate malformed XML due to unescaped ampersands in category tags.

Due to the critical XML malformedness in procedural graphics and the rights provenance contamination during candidate download failure, the verdict is **REQUEST_CHANGES**.

---

## 2. Confirmed Empirical Findings

### Finding 1: Malformed XML in Procedural SVG Generation (CRITICAL)
- **File & Line**: `src/assets/procedural.py:106, 171` and `THEMES` dictionary (lines 30, 40, 50, 60, 70).
- **Observation**:
  `ProceduralSVGGenerator.THEMES` defines category `tag` strings with raw unescaped ampersands:
  ```python
  "circuits": {"tag": "SEMICONDUCTOR & SOLID-STATE"},
  "computing": {"tag": "PARALLEL COMPUTING & ARCHITECTURE"},
  "aerospace": {"tag": "AEROSPACE & TELEMETRY"},
  "science": {"tag": "QUANTUM PHYSICS & EXPLORATION"},
  "general": {"tag": "TECHNOLOGY & INNOVATION"},
  ```
  In `generate_topic_svg()`, line 106 defines `tag = palette["tag"]` without `html.escape()`. It is interpolated directly into SVG XML on line 171:
  `<text ...>{tag}</text>`.
- **Verbatim Error**:
  ```text
  xml.etree.ElementTree.ParseError: not well-formed (invalid token): line 39, column 152
  ```
- **Blast Radius**: 100% of generated topic background SVGs across all 5 visual themes fail XML parsing. Headless browser frame capture and SVG image renderers will fail to parse the vector badge.
- **Recommended Mitigation**:
  In `src/assets/procedural.py:106`, escape the tag string:
  ```python
  safe_tag = html.escape(palette.get("tag", "TECHNOLOGY & INNOVATION"))
  ```
  and interpolate `safe_tag` on line 171.

---

### Finding 2: Rights Provenance Contamination on Candidate Download Failure (HIGH)
- **File & Line**: `src/assets/pipeline.py:156-214` and `src/assets/freezer.py:253-265`.
- **Observation**:
  When an online candidate asset is discovered during Stage 2, `pipeline.py` executes:
  ```python
  frozen_path, sha256, size, mime, status = self.freezer.freeze_asset(
      source=candidate.source_url,
      output_dir=target_dir,
      slug=slug,
      procedural_fallback=procedural_svg,
  )
  ```
  If `download_stream` fails (e.g. timeout, 404, 503), `freeze_asset` intercepts the exception internally, writes the local procedural fallback SVG to disk, and returns `status = "FALLBACK_GENERATED"`.
  However, `pipeline.py` continues inside its `try:` block and records the **candidate's** metadata in the ledger:
  ```python
  creator=CreatorInfo(name=candidate.creator_name, profile_url=candidate.creator_profile_url),
  license_info=LicenseInfo(
      license_type=candidate.license_type,
      attribution_text=candidate.attribution_text,
      ...
  )
  ```
  Meanwhile, `pipeline.py`'s `except Exception as e:` block on line 188 (which sets `creator="Harness 9 Procedural Asset Engine"` and `license_type="CC0-1.0 (Public Domain)"`) is **dead code** and never reached.
- **Consequence**: The on-disk file is a local synthetic SVG, but the ledger claims it is a third-party photo created by an external photographer under an external license (e.g. CC BY-SA 4.0 or Pexels).
- **Blast Radius**: Legal and provenance contamination in the generated asset ledger whenever network downloads fail.
- **Recommended Mitigation**:
  In `src/assets/pipeline.py:156`: Either do not pass `procedural_fallback` to `freeze_asset` so that download exceptions trigger the existing `except Exception:` fallback handler, OR inspect `if status == "FALLBACK_GENERATED":` in `pipeline.py` and record CC0 procedural metadata.

---

### Finding 3: `validate_ledger()` Skips Disk Validation When `project_dir` Argument Is None (MEDIUM)
- **File & Line**: `src/assets/ledger.py:196`.
- **Observation**:
  `AssetLedgerManager.__init__(output_dir=...)` stores `self.output_dir`.
  In `validate_ledger()`:
  Line 167: `base_dir = Path(project_dir or self.output_dir or Path.cwd()).resolve()`
  Line 196: `if a.local_path and project_dir:`
  When calling `mgr.validate_ledger()` without passing `project_dir` explicitly, line 196 evaluates to `False`, skipping all on-disk file existence and SHA-256 validation checks even when `self.output_dir` was configured.
- **Blast Radius**: Incomplete ledger validation in consumers relying on `mgr.validate_ledger()`.
- **Recommended Mitigation**:
  Change line 196 to: `if a.local_path and (project_dir or self.output_dir):`.

---

## 3. Detailed Empirical Verification Results

### 3.1 SHA-256 Byte-Level Exactness & Integrity
- **Test Suite**: `TestSHA256ByteExactnessAndIntegrity` in `tests/test_m2_challenger2_stress.py`.
- **Results**:
  - `test_pipeline_frozen_assets_sha256_exactness_100_percent`: **PASSED**. Generated assets for multiple topics (Transistors, GPUs, Apollo Computer); verified 100% exact match between disk SHA-256 and ledger `file_sha256`, as well as byte lengths.
  - `test_chunk_boundary_hashing_exactness`: **PASSED**. Tested payload sizes across chunk boundaries: 0B, 1B, 100B, 65535B, 65536B (exact 64KB buffer), 65537B, 131072B (128KB), 1048576B (1MB). All matched standard `hashlib.sha256`.
  - `test_tamper_detection_scenarios`: **PASSED**. Flipped single byte, truncated 1 byte, appended garbage, and deleted files. In 100% of cases, `validate_ledger()` reported SHA-256 mismatch or missing file errors.

### 3.2 License Metadata Completeness
- **Test Suite**: `TestLicenseMetadataCompleteness` in `tests/test_m2_challenger2_stress.py`.
- **Results**:
  - `test_all_assets_have_complete_license_metadata`: **PASSED**. Asserted that 100% of assets generated have non-empty `license_type`, `attribution_text`, `source_url`, and `creator.name`.
  - `test_online_candidate_and_fallback_license_completeness`: **PASSED**. Verified metadata completeness under mock network conditions.
  - `test_validate_ledger_detects_incomplete_metadata`: **PASSED**. Verified that `validate_ledger()` detects missing creator, missing license_type, and missing source_url.

### 3.3 Dual JSON / YAML Ledger Roundtripping Parity
- **Test Suite**: `TestLedgerSerializationRoundtripping` in `tests/test_m2_challenger2_stress.py`.
- **Results**:
  - `test_json_roundtrip_parity`: **PASSED**. `Model -> JSON -> Model` yielded identical dictionary dump and byte counts.
  - `test_yaml_roundtrip_parity`: **PASSED**. `Model -> YAML -> Model` yielded identical dictionary dump and schema values.
  - `test_cross_format_json_yaml_parity`: **PASSED**. Loading from `asset_ledger.json` vs `asset_ledger.yaml` produced 100% equivalent dataclass structures.
  - `test_dict_interface_parity`: **PASSED**. Verified `__getitem__`, `get`, `__contains__`, and `model_dump()` parity.

### 3.4 Adversarial Edge Cases & Scaling
- **Test Suite**: `TestAdversarialAndEdgeScenarios` in `tests/test_m2_challenger2_stress.py`.
- **Results**:
  - `test_high_volume_assets_stress_test`: **PASSED**. Scaled to 50 concurrent visual queries without memory leak, schema violation, or file collision.
  - `test_path_traversal_and_malicious_topic_sanitization`: **PASSED**. Malicious topic strings containing `../../../etc/passwd`, `C:\Windows\System32`, and shell escapes were safely sanitized into local `assets/images/` paths.
  - `test_duplicate_asset_id_replacement_and_summary_recount`: **PASSED**. Verified that adding an asset with an existing `asset_id` replaces the item and accurately recalculates `total_assets` and `license_summary`.
  - `test_corrupt_json_and_yaml_load_errors`: **PASSED**. Verified `json.JSONDecodeError`, `ValueError`, and `FileNotFoundError` handling.

---

## 4. Test Execution Summary

| Test Case | Module | Status | Execution Time |
|---|---|---|---|
| `test_pipeline_frozen_assets_sha256_exactness_100_percent` | `test_m2_challenger2_stress` | PASS | 0.82s |
| `test_chunk_boundary_hashing_exactness` | `test_m2_challenger2_stress` | PASS | 0.05s |
| `test_tamper_detection_scenarios` | `test_m2_challenger2_stress` | PASS | 0.04s |
| `test_all_assets_have_complete_license_metadata` | `test_m2_challenger2_stress` | PASS | 0.45s |
| `test_online_candidate_and_fallback_license_completeness` | `test_m2_challenger2_stress` | PASS | 0.65s |
| `test_validate_ledger_detects_incomplete_metadata` | `test_m2_challenger2_stress` | PASS | 0.02s |
| `test_json_roundtrip_parity` | `test_m2_challenger2_stress` | PASS | 0.03s |
| `test_yaml_roundtrip_parity` | `test_m2_challenger2_stress` | PASS | 0.04s |
| `test_cross_format_json_yaml_parity` | `test_m2_challenger2_stress` | PASS | 0.05s |
| `test_dict_interface_parity` | `test_m2_challenger2_stress` | PASS | 0.01s |
| `test_high_volume_assets_stress_test` | `test_m2_challenger2_stress` | PASS | 1.85s |
| `test_path_traversal_and_malicious_topic_sanitization` | `test_m2_challenger2_stress` | PASS | 0.12s |
| `test_duplicate_asset_id_replacement_and_summary_recount` | `test_m2_challenger2_stress` | PASS | 0.02s |
| `test_corrupt_json_and_yaml_load_errors` | `test_m2_challenger2_stress` | PASS | 0.02s |
| `test_network_fallback_provenance_recording_audit` | `test_m2_challenger2_stress` | PASS | 0.58s |

**Total Suite Execution**: 15 / 15 Passed in `tests/test_m2_challenger2_stress.py` (4.75s).

---

## 5. Verdict & Required Fixes

**Verdict**: **`REQUEST_CHANGES`**

Before Milestone 2 can be finalized for downstream integration in Milestone 3 & Milestone 4:
1. **Fix XML Malformedness in Procedural SVGs**: Ensure all tag labels in `ProceduralSVGGenerator.THEMES` are properly escaped via `html.escape()` before being injected into SVG XML.
2. **Fix Provenance Attribution on Network Fallback**: Ensure that when online downloading fails and a procedural fallback SVG is generated, the asset ledger assigns `Harness 9 Procedural Asset Engine` and `CC0-1.0 (Public Domain)` rather than the external candidate's metadata.
3. **Fix `validate_ledger()` Path Guard**: Ensure on-disk checks are executed when either `project_dir` or `self.output_dir` is present.
