"""Strict acceptance checks must fail closed on incomplete production evidence."""

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from verify_pipeline import PipelineVerifier


def _probe_result(payload, returncode=0, stderr=""):
    return subprocess.CompletedProcess(
        args=["ffprobe"],
        returncode=returncode,
        stdout=json.dumps(payload),
        stderr=stderr,
    )


def _valid_video_probe():
    return {
        "format": {"format_name": "mov,mp4,m4a,3gp,3g2,mj2", "duration": "15.0"},
        "streams": [
            {"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080},
            {"codec_type": "audio", "codec_name": "aac"},
        ],
    }


class TestStrictPipelineVerifier(unittest.TestCase):
    def test_research_requires_verified_claims_and_https_sources(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            dossier = {
                "topic": "Sample topic",
                "summary": {"headline": "Sample", "executive_summary": "Summary"},
                "talking_points": [{"title": "Point"}],
                "claims": [
                    {
                        "claim_id": f"claim_{i}",
                        "claim_text": f"Evidence-backed claim {i}",
                        "confidence_score": 0.3,
                        "verification_status": "VERIFIED",
                        "primary_source": {"title": "Source", "url": "https://example.org/source"},
                    }
                    for i in range(3)
                ],
            }
            (output_dir / "research_dossier.json").write_text(json.dumps(dossier), encoding="utf-8")

            verifier = PipelineVerifier(output_dir)
            verifier.verify_research_dossier()
            self.assertTrue(verifier.results[-1]["passed"])

            dossier["claims"][0]["verification_status"] = "UNVERIFIED"
            dossier["claims"][1]["primary_source"]["url"] = "http://example.org/source"
            dossier["claims"][2]["confidence_score"] = "unknown"
            (output_dir / "research_dossier.json").write_text(json.dumps(dossier), encoding="utf-8")
            verifier = PipelineVerifier(output_dir)
            verifier.verify_research_dossier()
            self.assertFalse(verifier.results[-1]["passed"])
            self.assertIn("not marked VERIFIED", verifier.results[-1]["details"])

    def test_asset_ledger_requires_frozen_in_project_asset_with_matching_hash(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            asset_path = output_dir / "assets" / "images" / "licensed.jpg"
            asset_path.parent.mkdir(parents=True)
            asset_bytes = b"licensed image fixture"
            asset_path.write_bytes(asset_bytes)
            ledger = {
                "assets": [
                    {
                        "local_path": "assets/images/licensed.jpg",
                        "file_sha256": hashlib.sha256(asset_bytes).hexdigest(),
                        "source_url": "https://commons.wikimedia.org/wiki/File:Example.jpg",
                        "verification_status": "FROZEN_LOCAL",
                        "creator": {"name": "Example Photographer"},
                        "license": {
                            "license_type": "CC BY 4.0",
                            "attribution_required": True,
                            "attribution_text": "Photo by Example Photographer",
                        },
                    }
                ]
            }
            (output_dir / "asset_ledger.json").write_text(json.dumps(ledger), encoding="utf-8")
            verifier = PipelineVerifier(output_dir)
            verifier.verify_asset_ledger()
            self.assertTrue(verifier.results[-1]["passed"])

            ledger["assets"][0]["local_path"] = "../outside.jpg"
            (output_dir / "asset_ledger.json").write_text(json.dumps(ledger), encoding="utf-8")
            verifier = PipelineVerifier(output_dir)
            verifier.verify_asset_ledger()
            self.assertFalse(verifier.results[-1]["passed"])
            self.assertIn("escapes the project directory", verifier.results[-1]["details"])

    def test_video_header_alone_does_not_pass_when_ffprobe_is_unavailable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            video_path = output_dir / "renders" / "final.mp4"
            video_path.parent.mkdir()
            video_path.write_bytes(b"\x00\x00\x00\x18ftypisom" + bytes(600))
            verifier = PipelineVerifier(output_dir)
            with mock.patch("verify_pipeline.subprocess.run", side_effect=FileNotFoundError("ffprobe")):
                verifier.verify_rendered_video()
            self.assertFalse(verifier.results[-1]["passed"])
            self.assertIn("ffprobe validation failed", verifier.results[-1]["details"])

    def test_video_requires_h264_aac_and_both_streams(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            video_path = output_dir / "renders" / "final.mp4"
            video_path.parent.mkdir()
            video_path.write_bytes(b"\x00\x00\x00\x18ftypisom" + bytes(600))

            verifier = PipelineVerifier(output_dir)
            with mock.patch("verify_pipeline.subprocess.run", return_value=_probe_result(_valid_video_probe())):
                verifier.verify_rendered_video()
            self.assertTrue(verifier.results[-1]["passed"])
            self.assertEqual(verifier.results[-1]["metadata"]["video_codec"], "h264")

            no_audio = _valid_video_probe()
            no_audio["streams"] = no_audio["streams"][:1]
            verifier = PipelineVerifier(output_dir)
            with mock.patch("verify_pipeline.subprocess.run", return_value=_probe_result(no_audio)):
                verifier.verify_rendered_video()
            self.assertFalse(verifier.results[-1]["passed"])

    def test_non_wav_audio_must_have_a_probed_audio_stream(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            audio_path = output_dir / "assets" / "audio" / "narration.mp3"
            audio_path.parent.mkdir(parents=True)
            audio_path.write_bytes(bytes(256))
            no_audio_stream = {"format": {"duration": "8.0"}, "streams": []}
            verifier = PipelineVerifier(output_dir)
            with mock.patch("verify_pipeline.subprocess.run", return_value=_probe_result(no_audio_stream)):
                verifier.verify_audio_narration()
            self.assertFalse(verifier.results[-1]["passed"])
            self.assertIn("no valid audio stream", verifier.results[-1]["details"])


if __name__ == "__main__":
    unittest.main()
