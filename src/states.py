from typing import Any, Dict, List, TypedDict


class CorePersona(TypedDict, total=False):
    """Target audience persona details."""

    name: str
    age_range: str
    background: str
    skill_level: str
    goals: str
    pain_points: str


class ContentPreferences(TypedDict, total=False):
    """Content behavior and viewing preferences."""

    preferred_length: str
    consumption_habits: str
    favored_formats: str
    tone: str
    accessibility_needs: str


class VideoProductionStyle(TypedDict, total=False):
    """Video production and delivery guidelines."""

    hook_examples: List[str]
    visual_style: str
    on_screen_text: str
    audio_style: str
    pacing: str


class AudienceProfile(TypedDict, total=False):
    """Complete audience and style profile for video content."""

    core_persona: CorePersona
    content_preferences: ContentPreferences
    top_messages: List[str]
    production_style: VideoProductionStyle
    calls_to_action: List[str]
    hashtags: List[str]
    voice_tone_description: str


class StyleProfile(TypedDict, total=False):
    """Production style and voice tone for video delivery."""

    production_style: VideoProductionStyle
    voice_tone: str


class Scene(TypedDict, total=False):
    """Individual scene in the video script."""

    scene_number: int
    on_screen_action: str
    dialogue_vo: str
    on_screen_text: str


class SceneAssets(TypedDict, total=False):
    """Assets required for a single scene."""

    scene_name: str
    video_asset: List[str]
    bgm: List[str]
    sfx: List[str]


class VoiceTiming(TypedDict, total=False):
    """Voice-over timing information for a scene or segment."""

    scene_number: int
    start_time: float
    end_time: float
    duration: float
    text: str
    audio_file: str


class VideoTimeline(TypedDict, total=False):
    """Timeline structure for video editing."""

    total_duration: float
    scenes: List[Dict[str, Any]]
    transitions: List[Dict[str, Any]]
    overlay_tracks: List[Dict[str, Any]]


class ExportMetadata(TypedDict, total=False):
    """Metadata for exported video files."""

    filename: str
    duration: float
    resolution: str
    format: str
    file_size: int
    hashtags: List[str]
    description: str
    thumbnail_path: str


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
    audience_profile: AudienceProfile
    style_profile: StyleProfile
    hook_ideas: List[str]
    meme_concepts: List[str]
    scenes: List[Scene]  # Now structured with Scene TypedDict
    total_estimated_duration: str  # Added from SceneBySceneScript
    asset_plan: List[SceneAssets]  # Now structured with SceneAssets TypedDict
    trends_analysis: str
    slang_analysis: str

    # Production fields
    video_filenames: List[str]
    voice_timing: List[VoiceTiming]  # Now structured with VoiceTiming TypedDict
    video_timeline: VideoTimeline  # Now structured with VideoTimeline TypedDict
    qc_notes: List[str]
    export_metadata: ExportMetadata  # Now structured with ExportMetadata TypedDict
