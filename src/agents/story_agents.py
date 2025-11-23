from typing import Any, Dict, List

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field

from agents.llm_utils import simple_llm_call, structured_llm_call


def audience_and_style_profiler_node(
    state: Dict[str, Any], llm: BaseChatModel
) -> Dict[str, Any]:
    summary = state.get("summary", "")

    profile_text = simple_llm_call(
        llm,
        "You design audience profiles for educational short-form videos.",
        f"Given this lecture summary, propose an ideal TikTok/shorts-style audience profile "
        f"\n\nSummary:\n{summary}",
    )

    # TODO: structured output
    # TODO: include voice tone description for tts later
    style_text = simple_llm_call(
        llm,
        "You design an engaging delivery style profiles for educational short-form videos.",
        "Given this lecture summary and audience profiles, propose an ideal TikTok/shorts-style delivery tone/style guidelines "
        f"\n\nSummary:\n{summary}\n\nAudience Profiles:\n{profile_text}",
    )

    return {
        "audience_profile": {"raw": profile_text},
        "style_profile": {"raw": style_text},
    }


def scene_by_scene_script_node(
    state: Dict[str, Any], llm: BaseChatModel
) -> Dict[str, Any]:
    summary = state.get("summary", "")
    key_concepts = state.get("key_concepts", [])
    hooks = state.get("hook_ideas", [])
    memes = state.get("meme_concepts")

    # TODO: structured output
    # TODO: asign grok thinking to generate the scene
    script_text = simple_llm_call(
        llm,
        "You write scene-by-scene scripts for 30-90 second educational brainrot-style videos.",
        f"Using the following information, create a numbered scene-by-scene script. "
        f"Each scene should have: on-screen action, dialogue/VO, and on-screen text.\n\n"
        f"Summary:\n{summary}\n\nKey concepts:\n{key_concepts}\n\nHooks:\n{hooks}"
        f"Memes:\n{memes}",
    )

    return {"scenes": [{"raw": script_text}]}


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
