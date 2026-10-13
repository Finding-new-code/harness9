"""Production-path regression tests for Harness 9 pipeline boundaries."""

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from src.orchestrator.pipeline import Pipeline
from src.research.engine import ResearchEngine
from verify_pipeline import main as verify_main, run_pipeline_flow


class TestProductionPipelineBoundaries(unittest.TestCase):
    def test_curated_offline_topic_returns_the_bundled_source_backed_dossier(self):
        dossier = ResearchEngine().synthesize_research(
            "How GPUs Work: Parallel Computing", offline=True
        )

        self.assertEqual(dossier.metadata.mode, "curated_preset")
        self.assertGreater(len(dossier.claims), 0)
        for claim in dossier.claims:
            self.assertEqual(claim.verification_status, "VERIFIED")
            self.assertTrue(claim.primary_source.url.startswith("https://"))

    def test_unknown_offline_topic_stops_before_creating_research_artifacts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "run"
            pipeline = Pipeline(
                topic="CRISPR Gene Editing",
                output_dir=output_dir,
                offline=True,
                duration=15,
            )

            self.assertFalse(pipeline.run())
            summary = json.loads((output_dir / "pipeline_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["status"], "FAILED")
            self.assertEqual(summary["stages"][0]["stage_name"], "research")
            self.assertFalse((output_dir / "research_dossier.json").exists())
            self.assertFalse((output_dir / "SCRIPT.md").exists())

    def test_pipeline_wrapper_propagates_errors_without_synthetic_fallback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "run"
            with mock.patch.object(Pipeline, "run", side_effect=RuntimeError("production failure")):
                with self.assertRaisesRegex(RuntimeError, "production failure"):
                    run_pipeline_flow("How GPUs Work", output_dir, offline=True, duration=15)
            self.assertFalse((output_dir / "research_dossier.json").exists())
            self.assertFalse((output_dir / "renders" / "final.mp4").exists())

    def test_pipeline_wrapper_does_not_promote_partial_runs_to_success(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "partial-run"

            def write_partial_summary(pipeline):
                pipeline.output_dir.mkdir(parents=True, exist_ok=True)
                (pipeline.output_dir / "pipeline_summary.json").write_text(
                    json.dumps({"status": "PARTIAL"}), encoding="utf-8"
                )
                return True

            with mock.patch.object(Pipeline, "run", write_partial_summary):
                self.assertFalse(run_pipeline_flow("How GPUs Work", output_dir, offline=True, duration=15))

    def test_verifier_does_not_accept_existing_artifacts_after_pipeline_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "old-run"
            output_dir.mkdir()
            (output_dir / "renders").mkdir()
            (output_dir / "renders" / "final.mp4").write_bytes(b"stale artifact")
            with mock.patch.object(sys, "argv", ["verify_pipeline.py", "--output-dir", str(output_dir)]):
                with mock.patch("verify_pipeline.run_pipeline_flow", return_value=False):
                    with mock.patch("verify_pipeline.PipelineVerifier.verify_all") as verify:
                        with self.assertRaises(SystemExit) as result:
                            verify_main()
            self.assertEqual(result.exception.code, 1)
            verify.assert_not_called()

    def test_verifier_no_offline_flag_selects_live_research(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "live-run"
            with mock.patch.object(
                sys,
                "argv",
                ["verify_pipeline.py", "--no-offline", "--output-dir", str(output_dir)],
            ):
                with mock.patch("verify_pipeline.run_pipeline_flow", return_value=False) as run_flow:
                    with self.assertRaises(SystemExit) as result:
                        verify_main()
            self.assertEqual(result.exception.code, 1)
            self.assertFalse(run_flow.call_args.kwargs["offline"])

    def test_verifier_forwards_online_assets_and_model_script_options(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "model-run"
            with mock.patch.object(
                sys,
                "argv",
                [
                    "verify_pipeline.py",
                    "--online-assets",
                    "--model-script",
                    "--output-dir",
                    str(output_dir),
                ],
            ):
                with mock.patch("verify_pipeline.run_pipeline_flow", return_value=False) as run_flow:
                    with self.assertRaises(SystemExit) as result:
                        verify_main()
            self.assertEqual(result.exception.code, 1)
            self.assertTrue(run_flow.call_args.kwargs["online_assets"])
            self.assertTrue(run_flow.call_args.kwargs["model_assisted_scripts"])

    def test_verifier_rejects_model_script_without_live_inputs(self):
        with mock.patch.object(
            sys,
            "argv",
            ["verify_pipeline.py", "--model-script"],
        ):
            with self.assertRaises(SystemExit) as result:
                verify_main()
        self.assertEqual(result.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
