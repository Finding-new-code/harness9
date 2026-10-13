#!/usr/bin/env python3
"""Run the production pipeline and verify the artifacts it actually created.

Use ``run_harness9.py`` to generate a video directly, or this command to run
the production pipeline and then evaluate its output. Validation never creates
replacement research, media, or renders when a pipeline stage fails.
"""

import argparse
import hashlib
import json
import math
import os
import re
import struct
import subprocess
import sys
import time
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlsplit

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


# ---------------------------------------------------------------------------
# Production Pipeline Runner
# ---------------------------------------------------------------------------

def run_pipeline_flow(
    topic: str,
    output_dir: Path,
    offline: bool = True,
    format_aspect: str = "16:9",
    duration: int = 30,
    voice: str = "default",
    online_assets: bool = False,
    model_assisted_scripts: bool = False,
    render_backend: Optional[str] = None,
) -> bool:
    """
    Execute the production pipeline. Errors propagate; this wrapper does not
    synthesize substitute research or artifacts when the production path fails.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    from src.orchestrator.pipeline import Pipeline

    pipeline = Pipeline(
        topic=topic,
        output_dir=str(output_dir),
        offline=offline,
        format=format_aspect,
        duration=duration,
        voice=voice,
        online_assets=online_assets,
        model_assisted_scripts=model_assisted_scripts,
        render_backend=render_backend,
    )
    if not pipeline.run():
        return False
    summary_path = output_dir / "pipeline_summary.json"
    if not summary_path.is_file():
        return False
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    return summary.get("status") == "SUCCESS"


# Verification Engine & Assertions
# ---------------------------------------------------------------------------

class PipelineVerifier:
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.results: List[Dict[str, Any]] = []

    def record_check(self, checkpoint_id: str, title: str, passed: bool, details: str = "", metadata: Optional[Dict[str, Any]] = None):
        self.results.append({
            "id": checkpoint_id,
            "title": title,
            "passed": passed,
            "details": details,
            "metadata": metadata or {},
        })

    def verify_all(self) -> Tuple[bool, List[Dict[str, Any]]]:
        """Runs all verification checks on the output directory."""
        self.verify_research_dossier()
        self.verify_asset_ledger()
        self.verify_audio_narration()
        self.verify_hyperframes_project()
        self.verify_hyperframes_composition()
        self.verify_rendered_video()
        
        all_passed = all(r["passed"] for r in self.results)
        return all_passed, self.results

    def verify_research_dossier(self):
        """Validates research_dossier.json / .yaml schema and contents."""
        json_path = self.output_dir / "research_dossier.json"
        yaml_path = self.output_dir / "research_dossier.yaml"
        
        if not json_path.exists() and not yaml_path.exists():
            self.record_check("CP_DOSSIER_EXISTS", "Research Dossier Existence", False, f"Missing {json_path} and {yaml_path}")
            return

        data: Optional[Dict[str, Any]] = None
        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                self.record_check("CP_DOSSIER_PARSE", "Research Dossier JSON Parsing", False, str(e))
                return
        elif yaml_path.exists() and yaml:
            try:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
            except Exception as e:
                self.record_check("CP_DOSSIER_PARSE", "Research Dossier YAML Parsing", False, str(e))
                return

        if not isinstance(data, dict):
            self.record_check("CP_DOSSIER_SHAPE", "Research Dossier Shape", False, "Dossier root is not an object")
            return

        # Check required fields
        required_keys = ["topic", "summary", "claims", "talking_points"]
        missing_keys = [k for k in required_keys if k not in data]
        if missing_keys:
            self.record_check("CP_DOSSIER_SCHEMA", "Research Dossier Required Fields", False, f"Missing keys: {missing_keys}")
            return
        if not isinstance(data.get("topic"), str) or not data["topic"].strip():
            self.record_check("CP_DOSSIER_TOPIC", "Research Dossier Topic", False, "Topic must be a non-empty string")
            return
        if not isinstance(data.get("summary"), dict) or not data["summary"]:
            self.record_check("CP_DOSSIER_SUMMARY", "Research Dossier Summary", False, "Summary must be a non-empty object")
            return
        if not isinstance(data.get("talking_points"), list) or not data["talking_points"]:
            self.record_check("CP_DOSSIER_TALKING_POINTS", "Research Talking Points", False, "Talking points must be a non-empty list")
            return

        # Check >= 3 claims with confidence scores and sources
        claims = data.get("claims", [])
        if not isinstance(claims, list) or len(claims) < 3:
            self.record_check("CP_DOSSIER_CLAIMS_COUNT", "Research Claims Count (>= 3)", False, f"Found {len(claims) if isinstance(claims, list) else 0} claims (required >= 3)")
            return

        invalid_claims = []
        for i, c in enumerate(claims):
            if not isinstance(c, dict):
                invalid_claims.append(f"Claim {i} is not a dict")
                continue
            claim_text = c.get("claim_text") or c.get("text")
            confidence = c.get("confidence_score", c.get("confidence"))
            source = c.get("primary_source") or c.get("source") or c.get("sources")
            
            if not claim_text:
                invalid_claims.append(f"Claim {i} missing text")
            try:
                confidence_value = float(confidence)
            except (TypeError, ValueError):
                confidence_value = float("nan")
            if not math.isfinite(confidence_value) or not (0.0 <= confidence_value <= 1.0):
                invalid_claims.append(f"Claim {i} invalid confidence score: {confidence}")
            if not source:
                invalid_claims.append(f"Claim {i} missing source citation")
            elif isinstance(source, dict):
                source_url = source.get("url")
                parsed_url = urlsplit(source_url) if isinstance(source_url, str) else None
                if not parsed_url or parsed_url.scheme != "https" or not parsed_url.netloc:
                    invalid_claims.append(f"Claim {i} has no valid HTTPS source URL")
            elif isinstance(source, list):
                has_https_source = any(
                    isinstance(item, dict)
                    and isinstance(item.get("url"), str)
                    and urlsplit(item["url"]).scheme == "https"
                    and bool(urlsplit(item["url"]).netloc)
                    for item in source
                )
                if not has_https_source:
                    invalid_claims.append(f"Claim {i} has no valid HTTPS source URL")
            elif isinstance(source, str):
                parsed_url = urlsplit(source)
                if parsed_url.scheme != "https" or not parsed_url.netloc:
                    invalid_claims.append(f"Claim {i} has no valid HTTPS source URL")
            if c.get("verification_status") != "VERIFIED":
                invalid_claims.append(f"Claim {i} is not marked VERIFIED")

        if invalid_claims:
            self.record_check("CP_DOSSIER_CLAIMS_VALIDITY", "Research Claims Validity", False, "; ".join(invalid_claims[:3]))
        else:
            self.record_check("CP_DOSSIER_VALID", "Research Dossier Verification", True, f"Verified {len(claims)} claims with citations & confidence scores", {"claims_count": len(claims)})

    def verify_asset_ledger(self):
        """Validates asset_ledger.json / .yaml and frozen local assets."""
        json_path = self.output_dir / "asset_ledger.json"
        yaml_path = self.output_dir / "asset_ledger.yaml"

        if not json_path.exists() and not yaml_path.exists():
            self.record_check("CP_LEDGER_EXISTS", "Asset Ledger Existence", False, "Neither asset_ledger.json nor asset_ledger.yaml found")
            return

        data: Optional[Dict[str, Any]] = None
        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                self.record_check("CP_LEDGER_PARSE", "Asset Ledger JSON Parse", False, str(e))
                return
        elif yaml_path.exists() and yaml:
            try:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
            except Exception as e:
                self.record_check("CP_LEDGER_PARSE", "Asset Ledger YAML Parse", False, str(e))
                return

        if not isinstance(data, dict):
            self.record_check("CP_LEDGER_SHAPE", "Asset Ledger Shape", False, "Ledger root is not a dictionary")
            return

        assets = data.get("assets", [])
        if not isinstance(assets, list) or len(assets) < 1:
            self.record_check("CP_LEDGER_ASSET_COUNT", "Asset Ledger Non-Empty", False, "Zero asset records found")
            return

        invalid_assets = []
        for i, a in enumerate(assets):
            if not isinstance(a, dict):
                invalid_assets.append(f"Asset {i} not a dict")
                continue
            local_path_str = a.get("local_path")
            license_data = a.get("license")
            license_val = (
                license_data.get("license_type") if isinstance(license_data, dict)
                else a.get("license_type") or license_data
            )
            source_url = a.get("source_url") or a.get("source")
            creator_data = a.get("creator")
            creator = (
                creator_data.get("name") if isinstance(creator_data, dict)
                else a.get("author") or a.get("attribution")
            )
            sha256 = a.get("file_sha256") or a.get("sha256")

            if not isinstance(local_path_str, str) or not local_path_str.strip():
                invalid_assets.append(f"Asset {i} missing local_path")
                continue
            if not license_val:
                invalid_assets.append(f"Asset {i} missing license metadata")
            if not source_url:
                invalid_assets.append(f"Asset {i} missing source URL")
            if not creator:
                invalid_assets.append(f"Asset {i} missing creator/attribution")
            parsed_source = urlsplit(source_url) if isinstance(source_url, str) else None
            if not parsed_source or parsed_source.scheme != "https" or not parsed_source.netloc:
                invalid_assets.append(f"Asset {i} has no valid HTTPS source URL")
            if not isinstance(sha256, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", sha256):
                invalid_assets.append(f"Asset {i} has no valid SHA-256 checksum")
            if a.get("verification_status") != "FROZEN_LOCAL":
                invalid_assets.append(f"Asset {i} is not marked FROZEN_LOCAL")
            if isinstance(license_data, dict) and license_data.get("attribution_required") and not license_data.get("attribution_text"):
                invalid_assets.append(f"Asset {i} requires attribution text")

            # Check that local asset file actually exists and SHA matches
            relative_path = Path(local_path_str)
            if relative_path.is_absolute():
                invalid_assets.append(f"Asset {i} path must be relative to the project: {local_path_str}")
                continue
            local_file = (self.output_dir / relative_path).resolve()
            try:
                local_file.relative_to(self.output_dir.resolve())
            except ValueError:
                invalid_assets.append(f"Asset {i} path escapes the project directory: {local_path_str}")
                continue
            if not local_file.exists():
                invalid_assets.append(f"Asset {i} file missing on disk: {local_path_str}")
            elif isinstance(sha256, str) and re.fullmatch(r"[0-9a-fA-F]{64}", sha256):
                actual_sha = hashlib.sha256(local_file.read_bytes()).hexdigest()
                if actual_sha.lower() != sha256.lower():
                    invalid_assets.append(f"Asset {i} SHA256 mismatch (expected {sha256[:8]}, got {actual_sha[:8]})")

        if invalid_assets:
            self.record_check("CP_LEDGER_VALIDITY", "Asset Ledger Provenance & Integrity", False, "; ".join(invalid_assets[:3]))
        else:
            self.record_check("CP_LEDGER_VALID", "Asset Ledger Verification", True, f"Verified {len(assets)} frozen assets with licenses, URLs, and checksums", {"asset_count": len(assets)})

    def verify_audio_narration(self):
        """Validates audio narration file existence, header, and duration."""
        candidate_paths = [
            self.output_dir / "assets" / "audio" / "narration.wav",
            self.output_dir / "assets" / "narration.wav",
            self.output_dir / "assets" / "audio" / "narration.mp3",
            self.output_dir / "narration.wav",
        ]
        audio_path = next((p for p in candidate_paths if p.exists()), None)

        if not audio_path:
            self.record_check("CP_AUDIO_EXISTS", "Audio Narration File Existence", False, "narration.wav not found in assets/audio/")
            return

        size = audio_path.stat().st_size
        if size < 100:
            self.record_check("CP_AUDIO_SIZE", "Audio Narration Non-Empty", False, f"Audio file is too small ({size} bytes)")
            return

        # Parse WAVs directly; all other accepted formats must be checked by
        # ffprobe so a non-empty but undecodable file cannot pass.
        if audio_path.suffix.lower() == ".wav":
            try:
                with wave.open(str(audio_path), "rb") as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    duration = frames / float(rate)
                    if duration < 1.0 or rate <= 0 or wf.getnchannels() <= 0:
                        self.record_check("CP_AUDIO_DURATION", "Audio Duration Valid", False, f"Audio duration too short ({duration:.2f}s)")
                        return
                    self.record_check("CP_AUDIO_VALID", "Audio Narration Verification", True, f"Valid WAV audio ({duration:.2f}s, {rate}Hz, {size} bytes)", {"duration_sec": duration, "sample_rate": rate})
                    return
            except Exception as e:
                self.record_check("CP_AUDIO_HEADER", "Audio WAV Header Parse", False, f"WAV parse error: {e}")
                return

        try:
            proc = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type", "-of", "json", str(audio_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )
            probe_data = json.loads(proc.stdout) if proc.returncode == 0 else {}
            streams = probe_data.get("streams", [])
            duration = float(probe_data.get("format", {}).get("duration", 0.0))
            if not any(stream.get("codec_type") == "audio" for stream in streams) or not math.isfinite(duration) or duration < 1.0:
                raise ValueError("ffprobe found no valid audio stream of at least one second")
        except Exception as exc:
            self.record_check("CP_AUDIO_PROBE", "Audio Stream Verification", False, f"Could not verify audio with ffprobe: {exc}")
            return
        self.record_check("CP_AUDIO_VALID", "Audio Narration Verification", True, f"Valid audio stream ({duration:.2f}s, {size} bytes)", {"duration_sec": duration})

    def verify_hyperframes_project(self):
        """Validates existence and structure of HyperFrames project markdown files."""
        required_files = ["BRIEF.md", "DESIGN.md", "SCRIPT.md", "STORYBOARD.md", "index.html", "styles.css", "main.js"]
        missing = [f for f in required_files if not (self.output_dir / f).exists()]

        if missing:
            self.record_check("CP_PROJECT_FILES", "HyperFrames Project Files", False, f"Missing files: {missing}")
            return

        # Inspect DESIGN.md for Brand, Colors, Typography, Motion
        design_text = (self.output_dir / "DESIGN.md").read_text(encoding="utf-8")
        required_design_sections = ["Brand", "Colors", "Typography", "Motion"]
        missing_sections = [s for s in required_design_sections if s.lower() not in design_text.lower()]

        if missing_sections:
            self.record_check("CP_DESIGN_GATE", "HyperFrames DESIGN.md Specification Gate", False, f"DESIGN.md missing sections: {missing_sections}")
            return

        self.record_check("CP_PROJECT_FILES", "HyperFrames Project Files", True, "All 5 core HyperFrames project documents present and well-formed")

    def verify_hyperframes_composition(self):
        """Validates index.html and styles.css for HyperFrames compliance."""
        index_path = self.output_dir / "index.html"
        if not index_path.exists():
            self.record_check("CP_COMP_EXISTS", "Composition index.html", False, "Missing index.html")
            return

        html = index_path.read_text(encoding="utf-8")
        
        # 1. Check data-composition-id="root"
        if 'data-composition-id="root"' not in html and "data-composition-id='root'" not in html:
            self.record_check("CP_COMP_ROOT_ID", "Root Composition ID", False, "Missing data-composition-id='root' attribute")
            return

        # 2. Check absence of remote http:// or https:// media links
        # Match src="http...", href="http...", url(http...) but allow cdnjs/unpkg for gsap scripts or standard namespaces
        media_http_matches = re.findall(r'(?:src|href|url)\s*=\s*["\'](https?://(?!cdnjs\.cloudflare\.com|unpkg\.com|www\.w3\.org)[^"\']+\.(?:png|jpg|jpeg|svg|webp|mp4|webm|wav|mp3))["\']', html, re.IGNORECASE)
        if media_http_matches:
            self.record_check("CP_COMP_HERMETIC_ASSETS", "Zero Remote Media Assets", False, f"Found remote media URLs in HTML: {media_http_matches[:3]}")
            return

        # 3. Check all local asset references point to existing files
        local_asset_refs = re.findall(r'(?:src|href)=["\'](assets/[^"\']+)["\']', html)
        broken_refs = []
        for ref in local_asset_refs:
            ref_path = self.output_dir / ref
            if not ref_path.exists():
                broken_refs.append(ref)

        if broken_refs:
            self.record_check("CP_COMP_LOCAL_ASSETS", "Local Asset Integrity", False, f"Broken local asset paths: {broken_refs}")
            return

        # 4. Check finite repeat math (no repeat: -1)
        js_files = [self.output_dir / "main.js", index_path]
        infinite_repeat_found = False
        for p in js_files:
            if p.exists():
                text = p.read_text(encoding="utf-8")
                # Remove JS comments before checking
                code_no_comments = re.sub(r'//.*', '', text)
                if re.search(r'repeat\s*:\s*-1\b', code_no_comments):
                    infinite_repeat_found = True
                    break

        if infinite_repeat_found:
            self.record_check("CP_COMP_FINITE_REPEAT", "Finite Animation Repeat Rule", False, "Found 'repeat: -1' in animation script (violates HyperFrames finite math rule)")
            return

        self.record_check("CP_COMP_VALID", "HyperFrames Composition Validation", True, "Composition passes all syntax, local asset, and timeline rules")

    def verify_rendered_video(self):
        """Validates existence, non-emptiness, and MP4 container structure of renders/final.mp4."""
        candidate_paths = [self.output_dir / "renders" / "final.mp4", self.output_dir / "final.mp4"]
        video_path = next((p for p in candidate_paths if p.exists()), None)

        if not video_path:
            self.record_check("CP_VIDEO_EXISTS", "Rendered Video File Existence", False, "renders/final.mp4 not found")
            return

        size = video_path.stat().st_size
        if size < 512:
            self.record_check("CP_VIDEO_SIZE", "Rendered Video Non-Empty", False, f"Video file is too small ({size} bytes)")
            return

        # Check MP4 header signature (ftyp box)
        with open(video_path, "rb") as f:
            header = f.read(32)
            if b"ftyp" not in header and b"\x1a\x45\xdf\xa3" not in header:  # ftyp for MP4 or WebM signature
                self.record_check("CP_VIDEO_CONTAINER", "Valid Video Container Header", False, "Missing MP4 'ftyp' or WebM signature")
                return

        # ffprobe is required: a plausible file header does not prove that a
        # usable MP4 with audio and video streams was rendered.
        try:
            cmd = [
                "ffprobe", "-v", "error", "-show_entries",
                "format=format_name,duration:stream=codec_type,codec_name,width,height",
                "-of", "json", str(video_path),
            ]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
            if proc.returncode != 0:
                raise ValueError(proc.stderr.strip() or f"ffprobe exited {proc.returncode}")
            probe_data = json.loads(proc.stdout)
            streams = probe_data.get("streams", [])
            video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
            audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
            duration = float(probe_data.get("format", {}).get("duration", 0.0))
            format_name = probe_data.get("format", {}).get("format_name", "")
            if not video_stream or not audio_stream:
                raise ValueError("MP4 must contain both video and audio streams")
            if video_stream.get("codec_name") != "h264" or audio_stream.get("codec_name") != "aac":
                raise ValueError("MP4 must use H.264 video and AAC audio")
            if "mp4" not in format_name.split(",") or not math.isfinite(duration) or duration <= 0:
                raise ValueError(f"invalid MP4 format or duration: format={format_name!r}, duration={duration}")
        except Exception as exc:
            self.record_check("CP_VIDEO_VALID", "Rendered MP4 Broadcast Verification", False, f"ffprobe validation failed: {exc}")
            return

        self.record_check(
            "CP_VIDEO_VALID",
            "Rendered MP4 Broadcast Verification",
            True,
            f"Playable H.264/AAC MP4 verified ({video_stream.get('width')}x{video_stream.get('height')}, {duration:.2f}s, {size} bytes)",
            {
                "video_codec": video_stream.get("codec_name"),
                "audio_codec": audio_stream.get("codec_name"),
                "width": video_stream.get("width"),
                "height": video_stream.get("height"),
                "duration_sec": duration,
            },
        )


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Harness 9 End-to-End Automated Pipeline & Acceptance Verification Harness",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--topic", type=str, default="The History of the Transistor", help="Topic brief for video generation")
    parser.add_argument("--output-dir", type=str, default="output/test_verification_run", help="Target project output directory")
    parser.add_argument(
        "--offline",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use curated offline research (default); --no-offline enables live research",
    )
    parser.add_argument("--format", type=str, choices=["16:9", "9:16"], default="16:9", help="Video aspect ratio format")
    parser.add_argument("--duration", type=int, default=30, help="Target duration in seconds")
    parser.add_argument("--voice", type=str, default="default", help="Voice preference")
    parser.add_argument("--online-assets", action="store_true", help="Use live asset discovery with curated offline research")
    parser.add_argument("--model-script", action="store_true", help="Use the configured Hermes model for source-grounded narration")
    parser.add_argument("--render-backend", choices=["chrome", "stub"], default=None, help="Renderer backend; beta verification should use chrome")
    parser.add_argument("--json", action="store_true", help="Output verification summary in JSON format")

    args = parser.parse_args()
    if args.model_script and args.offline and not args.online_assets:
        parser.error("--model-script requires --no-offline or --online-assets")
    out_dir = Path(args.output_dir)

    print("=" * 72)
    print(" HARNESS 9: PIPELINE EXECUTION & ACCEPTANCE VERIFICATION HARNESS")
    print("=" * 72)
    print(f" Topic:       {args.topic}")
    print(f" Output Dir:  {out_dir.resolve()}")
    print(f" Mode:        {'Offline research' if args.offline else 'Live research'}")
    print(f" Format:      {args.format} ({args.duration}s)")
    print("-" * 72)

    start_time = time.time()

    # Step 1: Execute Pipeline Flow
    print("\n[Stage 1/2] Executing End-to-End Video Generation Pipeline...")
    pipeline_success = run_pipeline_flow(
        topic=args.topic,
        output_dir=out_dir,
        offline=args.offline,
        format_aspect=args.format,
        duration=args.duration,
        voice=args.voice,
        online_assets=args.online_assets,
        model_assisted_scripts=args.model_script,
        render_backend=args.render_backend,
    )
    elapsed_pipeline = time.time() - start_time
    print(f"  --> Pipeline execution finished in {elapsed_pipeline:.2f}s (Success: {pipeline_success})\n")

    # Step 2: Run Acceptance Verifier
    print("[Stage 2/2] Running Acceptance Verification Checkpoints...")
    if pipeline_success:
        verifier = PipelineVerifier(out_dir)
        all_passed, checks = verifier.verify_all()
    else:
        all_passed = False
        checks = [{
            "title": "Production pipeline",
            "passed": False,
            "details": "Pipeline failed; stale or partial output was not accepted for verification.",
        }]
    total_elapsed = time.time() - start_time

    # Output Summary Table
    print("\n" + "=" * 72)
    print(" ACCEPTANCE VERIFICATION SUMMARY REPORT")
    print("=" * 72)
    
    for c in checks:
        status_tag = "[PASS]" if c["passed"] else "[FAIL]"
        print(f" {status_tag} {c['title']:<45} {c['details']}")

    print("-" * 72)
    print(f" Overall Status:    {'ALL CHECKPOINTS PASSED' if all_passed else 'VERIFICATION FAILED'}")
    print(f" Total Checkpoints: {len(checks)} (Passed: {sum(1 for c in checks if c['passed'])}, Failed: {sum(1 for c in checks if not c['passed'])})")
    print(f" Total Runtime:     {total_elapsed:.2f}s")
    print("=" * 72 + "\n")

    if args.json:
        summary_out = {
            "all_passed": pipeline_success and all_passed,
            "topic": args.topic,
            "output_dir": str(out_dir),
            "runtime_seconds": total_elapsed,
            "checkpoints": checks,
        }
        print(json.dumps(summary_out, indent=2))

    sys.exit(0 if pipeline_success and all_passed else 1)


if __name__ == "__main__":
    main()
