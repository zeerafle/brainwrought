"""Pydantic models for story and script generation."""

from typing import List

from pydantic import BaseModel, Field


class CorePersona(BaseModel):
    """Target audience persona details."""

    name: str = Field(description="Example persona name")
    age_range: list[int] = Field(
        description="Age range, in a form of list of 2 integer referring range. Ex: [18, 35]"
    )
    background: str = Field(description="Educational and professional background")
    skill_level: str = Field(description="Current skill level and knowledge")
    goals: str = Field(description="What they want to achieve")
    pain_points: str = Field(description="Challenges and frustrations they face")


class ContentPreferences(BaseModel):
    """Content behavior and viewing preferences."""

    preferred_length: str = Field(description="Ideal video length range")
    consumption_habits: str = Field(description="How and when they watch videos")
    favored_formats: str = Field(description="Preferred content formats and structures")
    tone: str = Field(description="Desired tone and energy level")
    accessibility_needs: str = Field(description="Accessibility requirements")


class VideoProductionStyle(BaseModel):
    """Video production and delivery guidelines."""

    hook_examples: List[str] = Field(description="Example hooks for first 2-3 seconds")
    visual_style: str = Field(description="Visual composition and layout guidelines")
    on_screen_text: str = Field(description="How to use captions and text overlays")
    audio_style: str = Field(
        description="Music, voiceover, and SFX guidelines. Ex: dynamic, soothing, authoritative"
    )
    pacing: str = Field(
        description="Timing, speaking rate, and beat structure. Ex: fast, slow"
    )


class AudienceAndStyleProfile(BaseModel):
    """Complete audience and style profile for video content."""

    core_persona: CorePersona = Field(description="Target audience persona")
    content_preferences: ContentPreferences = Field(
        description="Content behavior and preferences"
    )
    top_messages: List[str] = Field(description="Key messages to emphasize (3-5 items)")
    production_style: VideoProductionStyle = Field(
        description="Video production specifics"
    )
    calls_to_action: List[str] = Field(description="Primary and secondary CTAs")
    hashtags: List[str] = Field(description="Recommended hashtags for social media")
    voice_tone_description: str = Field(description="A short voice tone description.")


class Scene(BaseModel):
    """Individual scene in a video script."""

    scene_number: int = Field(description="Sequential scene number (1, 2, 3, etc.)")
    on_screen_action: str = Field(
        description="Detailed description of visual elements, animations, transitions, memes, and on-screen composition. "
        "Include camera movements, visual effects, meme placements (e.g., 'Drake Hotline Bling meme', 'Surprised Pikachu'), "
        "split-screen layouts, infographics, terminal windows, etc."
    )
    dialogue_vo: str = Field(
        description="Complete voice-over or dialogue script for the scene. "
        "This is what the narrator will say. Keep it punchy and fast-paced for brainrot style."
    )
    on_screen_text: str = Field(
        description="All text overlays, captions, code snippets, terminal commands, meme labels, and tips that appear on screen. "
        "Can include multiple elements like main captions, code blocks (with proper formatting), "
        "meme text labels, small tips/notes. Use clear formatting with line breaks (\\n) where needed."
    )


class SceneBySceneScript(BaseModel):
    """Complete scene-by-scene script for a video."""

    scenes: List[Scene] = Field(
        description="Complete list of scenes for the 30-90 second video. "
        "Typically 10-15 scenes for optimal pacing and information density."
    )
    total_estimated_duration: str = Field(
        description="Estimated total video duration (e.g., '45 seconds', '1 minute')"
    )


class SFXAsset(BaseModel):
    """Sound effect asset with timing."""

    description: str = Field(description="Description or filename of the SFX")
    timestamp_offset: float = Field(
        description="Offset in seconds from the start of the scene"
    )


class Assets(BaseModel):
    """Assets required for a scene."""

    scene_name: str = Field(description="Name of the scene")
    video_asset: List[str] = Field(description="List of video assets for the scene")
    bgm: List[str] = Field(description="List of background music for the scene")
    sfx: List[SFXAsset] = Field(description="List of sound effects for the scene")


class Scenes(BaseModel):
    """Collection of scene assets."""

    scenes: List[Assets] = Field(description="List of scenes assets")
