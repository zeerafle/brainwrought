from typing import Any, Dict

from langchain_openai import ChatOpenAI

from agents.llm_utils import simple_llm_call


def audience_and_style_profiler_node(
    state: Dict[str, Any], llm: ChatOpenAI
) -> Dict[str, Any]:
    ingestion = state.get("ingestion", {})
    story = state.get("story", {})
    summary = ingestion.get("summary", "")

    profile_text = simple_llm_call(
        llm,
        "You design audience and style profiles for educational short-form videos.",
        f"Given this lecture summary, propose an ideal TikTok/shorts-style audience profile "
        f"and tone/style guidelines.\n\nSummary:\n{summary}",
    )

    story["audience_profile"] = {"raw": profile_text}
    story["style_profile"] = {"raw": profile_text}
    state["story"] = story
    return state


def hook_and_meme_concept_node(
    state: Dict[str, Any], llm: ChatOpenAI
) -> Dict[str, Any]:
    story = state.get("story", {})
    audience_profile = story.get("audience_profile", {})
    style_profile = story.get("style_profile", {})
    ingestion = state.get("ingestion", {})
    summary = ingestion.get("summary", "")

    hooks_text = simple_llm_call(
        llm,
        "You write viral hooks and meme concepts for short-form educational content",
        f"Using this audience/style profile and lecture summary, propose 5 opening hook lines "
        f"and 5 meme / reference concepts. \n\nAudience profile: \n{audience_profile}\n\n"
        f"Style profile: \n{style_profile}\n\n"
        f"Summary:\n{summary}",
    )

    story["meme_concepts"] = story["hook_ideas"] = [
        line for line in hooks_text.split("\n") if line.strip()
    ]
    state["story"] = story
    return state


def scene_by_scene_script_node(
    state: Dict[str, Any], llm: ChatOpenAI
) -> Dict[str, Any]:
    ingestion = state.get("ingestion", {})
    story = state.get("story", {})
    summary = ingestion.get("summary", "")
    key_concepts = ingestion.get("key_concepts", [])
    hooks = story.get("hook_ideas", [])

    script_text = simple_llm_call(
        llm,
        "You write scene-by-scene scripts for 30-90 second educational brainrot-style videos.",
        f"Using the following information, create a numbered scene-by-scene script. "
        f"Each scene should have: on-screen action, dialogue/VO, and on-screen text.\n\n"
        f"Summary:\n{summary}\n\nKey concepts:\n{key_concepts}\n\nHooks:\n{hooks}",
    )

    story["scenes"] = [{"raw": script_text}]
    state["story"] = story
    return state


def asset_planner_node(state: Dict[str, Any], llm: ChatOpenAI) -> Dict[str, Any]:
    story = state.get("story", {})
    scenes = story.get("scenes", [])

    plan_text = simple_llm_call(
        llm,
        "You plan simple reusable assets (clips, BGM, SFX) for social videos.",
        f"Given this scene-by-scene script, list for each scene the suggested video assets, "
        f"BGM mood, and SFX.\n\nScenes:\n{scenes}",
    )

    story["asset_plan"] = [{"raw": plan_text}]
    state["story"] = story
    return state
