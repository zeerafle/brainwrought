"""Node functions for story and script generation."""

from typing import Any, Dict

from langchain_core.language_models import BaseChatModel
from utils.llm_utils import structured_llm_call

from models.story_models import (
    AudienceAndStyleProfile,
    SceneBySceneScript,
    Scenes,
)


def audience_and_style_profiler_node(
    state: Dict[str, Any], llm: BaseChatModel
) -> Dict[str, Any]:
    """
    Create comprehensive audience profile and delivery style guidelines.

    Args:
        state: Pipeline state containing summary.
        llm: Language model for profile generation.

    Returns:
        Dict with audience_profile, style_profile, and a new session_id.
    """
    import uuid
    import os

    summary = state.get("summary", "")

    # Generate session_id if not present, or use env var for testing
    session_id = state.get("session_id") or os.getenv("TEST_SESSION_ID") or str(uuid.uuid4())

    profile = structured_llm_call(
        llm,
        "You are an expert at designing comprehensive audience profiles and delivery style guidelines for educational short-form videos (TikTok/YouTube Shorts). "
        "Create detailed, actionable profiles that combine audience demographics, content preferences, production style, and voice tone guidance.",
        f"Given this lecture summary, create a complete audience and style profile for a TikTok/YouTube Shorts educational video series. "
        f"Include: core persona, content preferences, key messages, production style (hooks, visuals, pacing), CTAs, hashtags, and detailed voice tone description for TTS.\n\n"
        f"Summary:\n{summary}",
        AudienceAndStyleProfile,
    )

    return {
        "session_id": session_id,
        "audience_profile": profile.model_dump(),
        "style_profile": {
            "production_style": profile.production_style.model_dump(),
            "voice_tone": profile.voice_tone_description,
        },
    }


def scene_by_scene_script_node(
    state: Dict[str, Any], llm: BaseChatModel
) -> Dict[str, Any]:
    """
    Generate detailed scene-by-scene script for brainrot-style educational video.

    Args:
        state: Pipeline state with summary, key_concepts, hook_ideas, and meme_concepts.
        llm: Language model for script generation.

    Returns:
        Dict with scenes list and total_estimated_duration.
    """
    summary = state.get("summary", "")
    key_concepts = state.get("key_concepts", [])
    hooks = state.get("hook_ideas", [])
    memes = state.get("meme_concepts")

    script = structured_llm_call(
        llm,
        "You write scene-by-scene scripts for 30-90 second educational brainrot-style videos. "
        "Each scene must have: on-screen action (visuals, memes, animations), dialogue/VO (narrator script), "
        "and on-screen text (captions, code, tips). Make it fast-paced, engaging, and meme-heavy. "
        "Include popular meme formats like Drake Hotline Bling, Distracted Boyfriend, Surprised Pikachu, Expanding Brain, etc. "
        "For technical content, show terminal commands, code snippets, and practical examples.",
        f"Using the following information, create a complete numbered scene-by-scene script for a brainrot-style educational video. "
        f"Each scene should have: scene_number, on_screen_action, dialogue_vo, and on_screen_text.\n\n"
        f"Summary:\n{summary}\n\n"
        f"Key concepts:\n{key_concepts}\n\n"
        f"Hooks:\n{hooks}\n\n"
        f"Memes:\n{memes}\n\n"
        f"Make sure to:\n"
        f"- Start with a strong hook (first 2-3 seconds)\n"
        f"- Include relevant memes throughout\n"
        f"- Show practical examples and code where appropriate\n"
        f"- End with a clear call-to-action\n"
        f"- Keep the pace fast and engaging\n"
        f"- Structure on-screen text with clear formatting (use \\n for line breaks, proper spacing for code blocks)",
        SceneBySceneScript,
    )

    return {
        "scenes": [scene.model_dump() for scene in script.scenes],
        "total_estimated_duration": script.total_estimated_duration,
    }


def asset_planner_node(state: Dict[str, Any], llm: BaseChatModel) -> Dict[str, Any]:
    """
    Plan assets (video clips, BGM, SFX) for each scene.

    Args:
        state: Pipeline state containing scenes.
        llm: Language model for asset planning.

    Returns:
        Dict with asset_plan.
    """
    import os
    from pathlib import Path

    scenes = state.get("scenes", [])

    # Get list of available SFX
    sfx_dir = Path("assets/stock/sfx")
    available_sfx = []
    if sfx_dir.exists():
        available_sfx = [f.name for f in sfx_dir.glob("*.mp3")]

    plan = structured_llm_call(
        llm,
        "You plan simple reusable assets (clips, BGM, SFX) for social videos.",
        f"Given this scene-by-scene script, list for each scene the suggested video assets, "
        f"BGM mood, and SFX.\n\n"
        f"Available SFX files (prefer these if suitable):\n{', '.join(available_sfx)}\n\n"
        f"For SFX, provide a description (or filename if available) and a timestamp_offset (seconds from start of scene).\n"
        f"If a suitable SFX is not in the list, describe the sound you want (e.g. 'futuristic whoosh', 'digital glitch').\n\n"
        f"Scenes:\n{scenes}",
        Scenes,
    )

    return {"asset_plan": plan}
