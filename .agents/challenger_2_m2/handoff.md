# Handoff Report — Challenger 2 (Milestone 2: Asset Discovery, Rights Ledger & Local Freezing)

## 1. Observation
1. **Exact File Paths & Code Lines**:
   - `src/assets/procedural.py:106, 171` and `THEMES` definitions (lines 30, 40, 50, 60, 70): Category tags containing raw ampersands (`&`) interpolated unescaped into `<text ...>{tag}</text>`.
   - `src/assets/pipeline.py:156-214` and `src/assets/freezer.py:253-265`: When online candidate download fails, `freezer.freeze_asset` masks the exception, writes a procedural SVG to disk, and returns `status="FALLBACK_GENERATED"`. `pipeline.py` records candidate's metadata (`creator_name`, `license_type`, `attribution_text`) instead of procedural CC0 metadata, while `pipeline.py`'s `except Exception:` block is dead code.
   - `src/assets/ledger.py:196`: `if a.local_path and project_dir:` skips disk checks if `project_dir` parameter is `None` even if `self.output_dir` is configured on `AssetLedgerManager`.
2. **Verbatim Error**:
   Running `python -m unittest tests/test_adversarial_assets.py`:
   ```text
   xml.etree.ElementTree.ParseError: not well-formed (invalid token): line 39, column 152
   FAIL: test_all_themes_xml_validity (test_adversarial_assets.TestAdversarialProceduralSVG.test_all_themes_xml_validity)
   ```
3. **Tool Commands & Test Outputs**:
   - `python -m unittest tests/test_assets.py` (28/28 passed in 3.56s).
   - `python -m unittest tests/test_m2_challenger2_stress.py` (15/15 passed in 4.75s).

## 2. Logic Chain
1. *From Observation 1*: `procedural.py` interpolates unescaped strings with `&` into SVG XML. In XML specifications, `&` is a reserved delimiter for entity references; raw `&` causes standard XML parsers to abort with `ParseError`.
2. *From Observation 1*: When online asset downloads fail, the local file on disk is an auto-generated SVG vector card. Because `pipeline.py` records the candidate's metadata upon receiving `FALLBACK_GENERATED`, the ledger erroneously asserts that a third-party photo was frozen and attributes synthetic graphics to human photographers under external licenses (e.g. CC BY-SA 4.0). This directly violates provenance traceability.
3. *From Observation 1*: In `ledger.py`, line 196 guards on `project_dir` instead of `(project_dir or self.output_dir)`, disabling on-disk SHA-256 and existence verification when calling `mgr.validate_ledger()` without explicit parameter.
4. *Conclusion*: While core SHA-256 byte-exactness and JSON/YAML roundtripping are fully compliant, these two critical/high severity flaws require remediation before milestone sign-off.

## 3. Caveats
- Online asset discovery tests used mocked network responses and error simulations. Live network responses from Wikimedia, Pexels, and NASA will depend on internet availability and external API uptime.
- High-concurrency download streaming was not tested as the pipeline currently executes asset freezing sequentially.

## 4. Conclusion
- **Verdict**: **`REQUEST_CHANGES`**
- **Actionable Remediation**:
  1. In `src/assets/procedural.py`, apply `html.escape()` to `palette["tag"]` before template interpolation.
  2. In `src/assets/pipeline.py`, ensure that when `status == "FALLBACK_GENERATED"` or when candidate download fails, the asset is recorded with `Harness 9 Procedural Asset Engine` creator and `CC0-1.0 (Public Domain)` license metadata.
  3. In `src/assets/ledger.py:196`, update the guard to `if a.local_path and (project_dir or self.output_dir):`.

## 5. Verification Method
1. Run Challenger 2 adversarial stress harness:
   `python -m unittest tests/test_m2_challenger2_stress.py`
2. Run full asset test suite:
   `python -m unittest tests/test_assets.py`
3. Verify XML well-formedness of procedural SVGs:
   `python -c "from src.assets.procedural import ProceduralSVGGenerator; import xml.etree.ElementTree as ET; gen = ProceduralSVGGenerator(); ET.fromstring(gen.generate_topic_svg('The History of the Transistor'))"`
4. Invalidation condition: If any test in `tests/test_m2_challenger2_stress.py` fails or if `ET.fromstring(...)` raises `ParseError`, the build remains invalid.
