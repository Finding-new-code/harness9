"""Pipeline execution summary models for Stage 5 Orchestrator reporting."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import yaml

from src.utils.filesystem import atomic_write, ensure_dir


@dataclass
class StageResult:
    """Execution result and metrics for an individual pipeline stage."""
    stage_name: str
    success: bool
    execution_time_seconds: float
    artifacts: List[str] = field(default_factory=list)
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "stage_name": self.stage_name,
            "success": bool(self.success),
            "execution_time_seconds": float(self.execution_time_seconds),
            "artifacts": list(self.artifacts),
            "metrics": dict(self.metrics),
        }
        if self.error is not None:
            data["error"] = self.error
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StageResult":
        return cls(
            stage_name=str(data.get("stage_name", "")),
            success=bool(data.get("success", False)),
            execution_time_seconds=float(data.get("execution_time_seconds", 0.0)),
            artifacts=[str(a) for a in data.get("artifacts", [])],
            error=data.get("error"),
            metrics=dict(data.get("metrics") or {}),
        )


@dataclass
class PipelineSummary:
    """End-to-end pipeline run summary record."""
    run_id: str
    topic: str
    start_time: str
    end_time: str
    total_duration_seconds: float
    status: str = "SUCCESS"  # "SUCCESS", "FAILED", "PARTIAL"
    stages: List[StageResult] = field(default_factory=list)
    output_directory: str = ""
    final_video_path: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "topic": self.topic,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration_seconds": float(self.total_duration_seconds),
            "status": self.status,
            "output_directory": self.output_directory,
            "stages": [s.to_dict() for s in self.stages],
            "metrics": dict(self.metrics),
        }
        if self.final_video_path is not None:
            data["final_video_path"] = self.final_video_path
        return data

    def model_dump(self) -> Dict[str, Any]:
        return self.to_dict()

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)

    def __contains__(self, key: str) -> bool:
        return key in self.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineSummary":
        raw_stages = data.get("stages") or []
        stages = [StageResult.from_dict(s) for s in raw_stages if isinstance(s, dict)]
        return cls(
            schema_version=str(data.get("schema_version", "1.0.0")),
            run_id=str(data.get("run_id", "")),
            topic=str(data.get("topic", "")),
            start_time=str(data.get("start_time", "")),
            end_time=str(data.get("end_time", "")),
            total_duration_seconds=float(data.get("total_duration_seconds", 0.0)),
            status=str(data.get("status", "SUCCESS")),
            stages=stages,
            output_directory=str(data.get("output_directory", "")),
            final_video_path=data.get("final_video_path"),
            metrics=dict(data.get("metrics") or {}),
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "PipelineSummary":
        return cls.from_dict(json.loads(json_str))

    def to_yaml(self) -> str:
        return yaml.safe_dump(self.to_dict(), sort_keys=False, allow_unicode=True, default_flow_style=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "PipelineSummary":
        data = yaml.safe_load(yaml_str)
        if not isinstance(data, dict):
            raise ValueError("YAML root must be a dictionary")
        return cls.from_dict(data)

    def save(
        self,
        output_dir: Union[str, Path],
        base_name: str = "pipeline_summary",
    ) -> Tuple[Path, Path]:
        out_dir = ensure_dir(output_dir)
        json_path = out_dir / f"{base_name}.json"
        yaml_path = out_dir / f"{base_name}.yaml"

        atomic_write(json_path, self.to_json(indent=2), mode="w")
        atomic_write(yaml_path, self.to_yaml(), mode="w")

        return json_path, yaml_path

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> "PipelineSummary":
        p = Path(file_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Pipeline summary file not found: {p}")
        text = p.read_text(encoding="utf-8")
        if p.suffix.lower() in [".yaml", ".yml"]:
            return cls.from_yaml(text)
        return cls.from_json(text)
