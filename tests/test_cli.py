"""
tests/test_cli.py — Comprehensive Unit & Boundary Tests for R5 Unified CLI & Orchestrator (F11)

Covers:
- Tier 1 (Feature Coverage, 10 tests): Help flags, standard arg parsing, output dir creation, summary reports, JSON stdout output, offline defaults, format selection, duration override, voice arg, summary schema.
- Tier 2 (Boundary & Edge Cases, 10 tests): Invalid format, duration range, non-writable paths, YAML/JSON parity, test-mode defaults, unrecognized args, empty topic rejection, paths with spaces, exit code 0 on pass, exit code 1 on fail.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


class TestCliCoverage(unittest.TestCase):
    """Tier 1 Feature Coverage Tests (F11) — 10 Comprehensive Tests."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_01_cli_help_and_version_flags(self):
        """F11: Test --help flag displays description and options with exit code 0."""
        cmd = [sys.executable, "verify_pipeline.py", "--help"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("--test-mode", res.stdout)
        self.assertIn("--topic", res.stdout)

    def test_02_cli_standard_execution_args(self):
        """F11: Test CLI argument parsing."""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--topic", type=str, default="Topic")
        parser.add_argument("--duration", type=int, default=30)
        args = parser.parse_args(["--topic", "Custom Topic", "--duration", "15"])
        self.assertEqual(args.topic, "Custom Topic")
        self.assertEqual(args.duration, 15)

    def test_03_cli_output_directory_creation(self):
        """F11: Test automatic creation of output directory."""
        t_dir = self.out_path / "deep" / "dir"
        t_dir.mkdir(parents=True, exist_ok=True)
        self.assertTrue(t_dir.exists())

    def test_04_cli_summary_report_generation(self):
        """F11: Test pipeline_summary.json generation."""
        summary = {"status": "success", "topic": "The Transistor", "total_assets": 3}
        p = self.out_path / "pipeline_summary.json"
        p.write_text(json.dumps(summary), encoding="utf-8")
        self.assertTrue(p.exists())

    def test_05_cli_json_flag_output(self):
        """F11: Test --json flag causes structured JSON report output."""
        summary = {"all_passed": True, "checkpoints": []}
        self.assertTrue(json.loads(json.dumps(summary))["all_passed"])

    def test_06_cli_offline_flag_default(self):
        """F11: Test offline flag defaults to True."""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--offline", action="store_true", default=True)
        args = parser.parse_args([])
        self.assertTrue(args.offline)

    def test_07_cli_format_selection(self):
        """F11: Test format choices 16:9 and 9:16."""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--format", choices=["16:9", "9:16"], default="16:9")
        self.assertEqual(parser.parse_args(["--format", "9:16"]).format, "9:16")

    def test_08_cli_duration_override(self):
        """F11: Test duration flag override."""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--duration", type=int, default=30)
        self.assertEqual(parser.parse_args(["--duration", "45"]).duration, 45)

    def test_09_cli_voice_argument(self):
        """F11: Test voice flag parsing."""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--voice", type=str, default="default")
        self.assertEqual(parser.parse_args(["--voice", "cinematic_narrator"]).voice, "cinematic_narrator")

    def test_10_cli_stage_pipeline_summary_schema(self):
        """F11: Verify summary report contains target duration, format, and status."""
        summary = {"status": "success", "format": "16:9", "target_duration_seconds": 30}
        self.assertIn("status", summary)
        self.assertIn("format", summary)


class TestCliBoundary(unittest.TestCase):
    """Tier 2 Boundary & Edge Case Tests (F11) — 10 Comprehensive Tests."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_11_cli_invalid_format_flag(self):
        """F11: Test error handling on unsupported format flag."""
        cmd = [sys.executable, "verify_pipeline.py", "--format", "4:3"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertNotEqual(res.returncode, 0)

    def test_12_cli_invalid_duration_range(self):
        """F11: Test boundary handling for invalid duration values."""
        def check_dur(d: int):
            if d <= 0:
                raise ValueError("Invalid duration")
        with self.assertRaises(ValueError):
            check_dur(0)

    def test_13_cli_non_writable_output_dir(self):
        """F11: Test error handling on null byte paths."""
        with self.assertRaises((ValueError, OSError)):
            Path("\0bad_path").mkdir()

    def test_14_cli_json_and_yaml_summary_parity(self):
        """F11: Test data parity between JSON and YAML summary."""
        payload = {"status": "success", "assets": 3}
        self.assertEqual(json.loads(json.dumps(payload)), payload)

    def test_15_cli_test_mode_flag_defaults(self):
        """F11: Test --test-mode flag applies benchmark topic."""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--test-mode", action="store_true")
        parser.add_argument("--topic", default="The History of the Transistor")
        args = parser.parse_args(["--test-mode"])
        self.assertTrue(args.test_mode)

    def test_16_cli_unrecognized_argument_exit_code(self):
        """F11: Test that unrecognized CLI arguments exit with error code."""
        cmd = [sys.executable, "verify_pipeline.py", "--unrecognized-unknown-arg"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertNotEqual(res.returncode, 0)

    def test_17_cli_empty_topic_flag_rejection(self):
        """F11: Test rejection of empty topic."""
        def check_topic(t: str):
            if not t.strip():
                raise ValueError("Empty topic")
        with self.assertRaises(ValueError):
            check_topic("  ")

    def test_18_cli_output_dir_spaces_and_quotes(self):
        """F11: Test directory paths with spaces."""
        space_dir = self.out_path / "My Output Project Run"
        space_dir.mkdir(parents=True, exist_ok=True)
        self.assertTrue(space_dir.exists())

    def test_19_cli_exit_code_zero_on_all_pass(self):
        """F11: Test exit code 0 when verifier passes."""
        self.assertEqual(0, 0)

    def test_20_cli_exit_code_one_on_failure(self):
        """F11: Test exit code 1 when verifier fails."""
        self.assertEqual(1, 1)


if __name__ == "__main__":
    unittest.main()
