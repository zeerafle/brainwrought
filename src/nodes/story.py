"""Node functions for story and script generation."""

from typing import Any, Dict

from langchain_core.language_models import BaseChatModel

from config import get_openai_llm
from models.story_models import (
    AudienceAndStyleProfile,
    SceneBySceneScript,
    Scenes,
)
from utils.llm_utils import structured_llm_call


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
    import os
    import uuid

    summary = state.get("summary", "")
    language = state.get("language", "")

    # Generate session_id if not present, or use env var for testing
    session_id = (
        state.get("session_id") or os.getenv("TEST_SESSION_ID") or str(uuid.uuid4())
    )

    profile = structured_llm_call(
        llm,
        "You are an expert at designing comprehensive audience profiles and delivery style guidelines for educational short-form videos (TikTok/YouTube Shorts). "
        "Create detailed, actionable profiles that combine audience demographics, content preferences, production style, and voice tone guidance.",
        f"Given this lecture summary, create a complete audience and style profile for a TikTok/YouTube Shorts educational video series. "
        f"Include: core persona, content preferences, key messages, production style (hooks, visuals, pacing), CTAs, hashtags, and short voice tone description for TTS.\n\n"
        f"Summary:\n{summary}"
        f"Note: For calls_to_action, use source language: {language}",
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
    memes = state.get("meme_concepts", [])
    language = state.get("language", "")

    script = structured_llm_call(
        llm,
        "You write scene-by-scene scripts for 30-90 second educational brainrot-style videos. "
        f"Write it in source language: {language}"
        "Each scene must have: on-screen action (visuals, memes, animations), dialogue/VO (narrator script), "
        "and on-screen text (captions, code, tips). Make it fast-paced, engaging, and meme-heavy. "
        "For technical content, show terminal commands, code snippets, and practical examples.",
        f"Using the following information, create a complete numbered scene-by-scene script for a brainrot-style educational video. "
        f"Each scene should have: scene_number, on_screen_action, and dialogue_vo.\n\n"
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
        f"- Structure on-screen text with clear formatting (use \\n for line breaks, proper spacing for code blocks)"
        f"- Keep it in the source language: {language}",
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
    from pathlib import Path

    llm = get_openai_llm("gpt-5.1")
    scenes = state.get("scenes", [])

    # Get list of available SFX
    sfx_dir = Path("assets/stock/sfx")
    available_sfx = []
    if sfx_dir.exists():
        available_sfx = [f.name for f in sfx_dir.glob("*.mp3")]

    plan = structured_llm_call(
        llm,
        "You plan simple reusable assets (clips, BGM, SFX) for social videos.",
        f"Given this scene-by-scene script, "
        "generate for each scene the following: "
        "- suggested video assets (each scene can only have one assets, and its either video or meme, describe it accordingly),\n"
        "  - always prefer memes first. If memes, explain the meme reference/name and additional text\n"
        "  - if video generate a stock-videos-like video description. The more elaborate the better. focus on detailed, chronological descriptions of actions and scenes. Include specific movements, appearances, camera angles, and environmental details - all in a single flowing paragraph. Start directly with the action, and keep descriptions literal and precise.\n"
        "- BGM mood,\n"
        "- and SFX.\n\n"
        f"Available SFX files (prefer this as much as possible, use whatever possible):\n{'\n'.join(available_sfx)}\n\n"
        f"For SFX, provide a description (or filename if available) and a timestamp_offset (seconds from start of scene).\n"
        f"Read carefully, if a suitable SFX is not in the list, describe the sound you want (e.g. 'futuristic whoosh', 'digital glitch').\n\n"
        f"Scenes:\n{scenes}",
        Scenes,
    )

    return {"asset_plan": plan}
