from typing import Any, Dict, List, TypedDict


class IngestionState(TypedDict, total=False):
    raw_text: str  # Add this field
    pdf_path: str
    pages: List[str]
    toc: List[Dict[str, Any]]
    key_concepts: List[str]
    summary: str
    quiz_items: List[Dict[str, Any]]


class StoryStudioState(TypedDict, total=False):
    # Inputs from ingestion
    key_concepts: List[str]
    summary: str
    quiz_items: List[Dict[str, Any]]
    audience_profile: Dict[str, Any]
    style_profile: Dict[str, Any]
    hook_ideas: List[str]
    meme_concepts: List[str]
    scenes: List[Dict[str, Any]]  # scene-by-scene scripts
    asset_plan: List[Dict[str, Any]]  # clips, BGM, SFX references


class ProductionState(TypedDict, total=False):
    scenes: List[Dict[str, Any]]
    asset_plan: List[Dict[str, Any]]
    voice_timing: List[Dict[str, Any]]
    video_timeline: Dict[str, Any]
    qc_notes: List[str]
    export_metadata: Dict[str, Any]


class PipelineState(TypedDict, total=False):
    """
    Top-level state passed through the entire pipeline.
    Flattened structure allows parallel nodes to update different keys without conflicts.
    """

    # Ingestion fields
    raw_text: str
    pdf_path: str
    pages: List[str]
    toc: List[Dict[str, Any]]
    key_concepts: List[str]
    summary: str
    quiz_items: List[Dict[str, Any]]
    language: str

    # Story Studio fields
    audience_profile: Dict[str, Any]
    style_profile: Dict[str, Any]
    hook_ideas: List[str]
    meme_concepts: List[str]
    scenes: List[Dict[str, Any]]
    asset_plan: List[Dict[str, Any]]

    # Production fields
    voice_timing: List[Dict[str, Any]]
    video_timeline: Dict[str, Any]
    qc_notes: List[str]
    export_metadata: Dict[str, Any]
