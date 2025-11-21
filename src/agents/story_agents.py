from typing import Any, Dict

from langchain_openai import ChatOpenAI

from agents.llm_utils import simple_llm_call


def audience_and_style_profiler_node(
    state: Dict[str, Any], llm: ChatOpenAI
) -> Dict[str, Any]:
    summary = state.get("summary", "")

    profile_text = simple_llm_call(
        llm,
        "You design audience profiles for educational short-form videos.",
        f"Given this lecture summary, propose an ideal TikTok/shorts-style audience profile "
        f"and tone/style guidelines.\n\nSummary:\n{summary}",
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


# TODO: move to its own agent
# integrate with Bluesky, Tiktok MCP
# analyze the most viral education video for the hooks
# get the most current meme/brainrot trend
# insert it into concept
def hook_and_meme_concept_node(
    state: Dict[str, Any], llm: ChatOpenAI
) -> Dict[str, Any]:
    audience_profile = state.get("audience_profile", {})
    style_profile = state.get("style_profile", {})
    summary = state.get("summary", "")

    # TODO: structured output
    # TODO: assign Grok to look for hooks and meme concepts
    # TODO: split and parallelize this
    hooks_text = simple_llm_call(
        llm,
        "You write viral hooks and meme concepts for short-form educational content",
        f"Using this audience/style profile and lecture summary, propose 5 opening hook lines "
        f"and 5 meme / reference concepts. \n\nAudience profile: \n{audience_profile}\n\n"
        f"Style profile: \n{style_profile}\n\n"
        f"Summary:\n{summary}",
    )

    hooks_ideas = [line for line in hooks_text.split("\n") if line.strip()]
    return {"meme_concepts": hooks_ideas, "hook_ideas": hooks_ideas}


def scene_by_scene_script_node(
    state: Dict[str, Any], llm: ChatOpenAI
) -> Dict[str, Any]:
    summary = state.get("summary", "")
    key_concepts = state.get("key_concepts", [])
    hooks = state.get("hook_ideas", [])

    # TODO: structured output
    # TODO: asign grok thinking to generate the scene
    script_text = simple_llm_call(
        llm,
        "You write scene-by-scene scripts for 30-90 second educational brainrot-style videos.",
        f"Using the following information, create a numbered scene-by-scene script. "
        f"Each scene should have: on-screen action, dialogue/VO, and on-screen text.\n\n"
        f"Summary:\n{summary}\n\nKey concepts:\n{key_concepts}\n\nHooks:\n{hooks}",
    )

    return {"scenes": [{"raw": script_text}]}


# TODO: find a way to get assets
def asset_planner_node(state: Dict[str, Any], llm: ChatOpenAI) -> Dict[str, Any]:
    scenes = state.get("scenes", [])

    plan_text = simple_llm_call(
        llm,
        "You plan simple reusable assets (clips, BGM, SFX) for social videos.",
        f"Given this scene-by-scene script, list for each scene the suggested video assets, "
        f"BGM mood, and SFX.\n\nScenes:\n{scenes}",
    )

    return {"asset_plan": [{"raw": plan_text}]}
