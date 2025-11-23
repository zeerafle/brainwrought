from typing import Any, Dict, List

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field

from agents.llm_utils import structured_llm_call


class CorePersona(BaseModel):
    name: str = Field(description="Example persona name")
    age_range: str = Field(description="Age range (e.g., '18-35')")
    background: str = Field(description="Educational and professional background")
    skill_level: str = Field(description="Current skill level and knowledge")
    goals: str = Field(description="What they want to achieve")
    pain_points: str = Field(description="Challenges and frustrations they face")


class ContentPreferences(BaseModel):
    preferred_length: str = Field(description="Ideal video length range")
    consumption_habits: str = Field(description="How and when they watch videos")
    favored_formats: str = Field(description="Preferred content formats and structures")
    tone: str = Field(description="Desired tone and energy level")
    accessibility_needs: str = Field(description="Accessibility requirements")


class VideoProductionStyle(BaseModel):
    hook_examples: List[str] = Field(description="Example hooks for first 2-3 seconds")
    visual_style: str = Field(description="Visual composition and layout guidelines")
    on_screen_text: str = Field(description="How to use captions and text overlays")
    audio_style: str = Field(description="Music, voiceover, and SFX guidelines")
    pacing: str = Field(description="Timing, speaking rate, and beat structure")


class AudienceAndStyleProfile(BaseModel):
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
    voice_tone_description: str = Field(
        description="Detailed voice/narrator tone for TTS and delivery"
    )


def audience_and_style_profiler_node(
    state: Dict[str, Any], llm: BaseChatModel
) -> Dict[str, Any]:
    summary = state.get("summary", "")

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
        "audience_profile": profile.model_dump(),
        "style_profile": {
            "production_style": profile.production_style.model_dump(),
            "voice_tone": profile.voice_tone_description,
        },
    }


class Scene(BaseModel):
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
    scenes: List[Scene] = Field(
        description="Complete list of scenes for the 30-90 second video. "
        "Typically 10-15 scenes for optimal pacing and information density."
    )
    total_estimated_duration: str = Field(
        description="Estimated total video duration (e.g., '45 seconds', '1 minute')"
    )


def scene_by_scene_script_node(
    state: Dict[str, Any], llm: BaseChatModel
) -> Dict[str, Any]:
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


class Assets(BaseModel):
    scene_name: str = Field(description="Name of the scene")
    video_asset: List[str] = Field(description="List of video assets for the scene")
    bgm: List[str] = Field(description="List of background music for the scene")
    sfx: List[str] = Field(description="List of sound effects for the scene")


class Scenes(BaseModel):
    scenes: List[Assets] = Field(description="List of scenes assets")


def asset_planner_node(state: Dict[str, Any], llm: BaseChatModel) -> Dict[str, Any]:
    scenes = state.get("scenes", [])

    plan = structured_llm_call(
        llm,
        "You plan simple reusable assets (clips, BGM, SFX) for social videos.",
        f"Given this scene-by-scene script, list for each scene the suggested video assets, "
        f"BGM mood, and SFX.\n\nScenes:\n{scenes}",
        Scenes,
    )

    return {"asset_plan": plan}
