"""Harness 9 Schema Models & Production Contracts Package.

Maintains 100% backwards compatibility for existing pipeline models while
re-exporting all 17 Pydantic v2 production contracts for Milestone M1+.
"""

# ---------------------------------------------------------------------------
# Legacy Models (Backwards Compatibility)
# ---------------------------------------------------------------------------
from src.models.dossier import (
    ResearchDossier as LegacyResearchDossier,
    Claim,
    Source,
    TalkingPoint,
    Statistic,
    Summary,
    DossierMetadata,
)
from src.models.ledger import (
    AssetProvenanceLedger,
    MediaAsset,
    LicenseInfo as LegacyLicenseInfo,
    CreatorInfo,
    Dimensions as LegacyDimensions,
)
from src.models.script import (
    Script as LegacyScript,
    Storyboard,
    Scene,
    Beat,
)
from src.models.summary import (
    PipelineSummary,
    StageResult,
)

# ---------------------------------------------------------------------------
# 17 Pydantic v2 Production Contracts (Milestone M1)
# ---------------------------------------------------------------------------
from src.models.contracts import (
    CreatorProfile,
    ContentBrief,
    ResearchPlan,
    ResearchDossier,
    SourceRecord,
    ClaimRecord,
    TalkingPointRecord,
    StatisticRecord,
    EditorialAngle,
    EditorialScorecard,
    AngleScorecard,
    ContentOutline,
    OutlineAct,
    Script,
    ScriptBeat,
    ScriptScene,
    AssetRequirement,
    AssetRecord,
    Dimensions,
    LicenseInfo,
    EvaluationReport,
    EvaluationLayer,
    RenderArtifact,
    PublishPackage,
    AnalyticsSnapshot,
    LearningCandidate,
    H9BaseModel,
)

# ---------------------------------------------------------------------------
# Production IR AST Models & Compiler (Milestone M3)
# ---------------------------------------------------------------------------
from src.models.ir import (
    IRBlockType,
    IRAssetReference,
    IRSpeechBeat,
    IRNarrationBlock,
    IRAnimationTrack,
    IRVisualBlockNode,
    IRTransitionSpec,
    IRSceneNode,
    IRAudioTrack,
    IRMetadata,
    AudioNarration,
    ProductionIRDocument,
    compile_script_to_ir,
    HyperFramesCompiler,
)

__all__ = [
    # Production IR AST Models (Milestone M3)
    "IRBlockType",
    "IRAssetReference",
    "IRSpeechBeat",
    "IRNarrationBlock",
    "IRAnimationTrack",
    "IRVisualBlockNode",
    "IRTransitionSpec",
    "IRSceneNode",
    "IRAudioTrack",
    "IRMetadata",
    "AudioNarration",
    "ProductionIRDocument",
    "compile_script_to_ir",
    "HyperFramesCompiler",
    # 17 Pydantic v2 Production Contracts
    "CreatorProfile",
    "ContentBrief",
    "ResearchPlan",
    "ResearchDossier",
    "SourceRecord",
    "ClaimRecord",
    "TalkingPointRecord",
    "StatisticRecord",
    "EditorialAngle",
    "EditorialScorecard",
    "AngleScorecard",
    "ContentOutline",
    "OutlineAct",
    "Script",
    "ScriptBeat",
    "ScriptScene",
    "AssetRequirement",
    "AssetRecord",
    "Dimensions",
    "LicenseInfo",
    "EvaluationReport",
    "EvaluationLayer",
    "RenderArtifact",
    "PublishPackage",
    "AnalyticsSnapshot",
    "LearningCandidate",
    "H9BaseModel",
    # Legacy Dossier models
    "Claim",
    "Source",
    "TalkingPoint",
    "Statistic",
    "Summary",
    "DossierMetadata",
    "LegacyResearchDossier",
    # Legacy Ledger models
    "AssetProvenanceLedger",
    "MediaAsset",
    "CreatorInfo",
    "LegacyLicenseInfo",
    "LegacyDimensions",
    # Legacy Script models
    "Storyboard",
    "Scene",
    "Beat",
    "LegacyScript",
    # Summary models
    "PipelineSummary",
    "StageResult",
]
