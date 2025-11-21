from typing import Any, Dict

from langchain_openai import ChatOpenAI

from .llm_utils import simple_llm_call


def voice_and_timing_node(state: Dict[str, Any], llm: ChatOpenAI) -> Dict[str, Any]:
    story = state.get("story", {})
    production = state.get("production", {})
    scenes = story.get("scenes", [])

    vt_text = simple_llm_call(
        llm,
        "You derive voice-over lines and approximate timings for each scene.",
        f"For each scene below, assign VO lines and duration in seconds.\n\nScenes:\n{scenes}",
    )

    production["voice_timing"] = [{"raw": vt_text}]
    state["production"] = production
    return state


def video_editor_renderer_node(
    state: Dict[str, Any],
    llm: ChatOpenAI,
) -> Dict[str, Any]:
    story = state.get("story", {})
    production = state.get("production", {})
    scenes = story.get("scenes", [])
    asset_plan = story.get("asset_plan", [])
    voice_timing = production.get("voice_timing", [])

    timeline_text = simple_llm_call(
        llm,
        "You act as a non-technical video editor describing a clear edit timeline.",
        "Create a JSON-like timeline that maps scenes, assets, and voice timing for a "
        "simple linear edit.\n\n"
        f"Scenes:\n{scenes}\n\nAssets:\n{asset_plan}\n\nVoice/timing:\n{voice_timing}",
    )

    production["video_timeline"] = {"raw": timeline_text}
    state["production"] = production
    return state


def qc_and_safety_node(state: Dict[str, Any], llm: ChatOpenAI) -> Dict[str, Any]:
    production = state.get("production", {})
    timeline = production.get("video_timeline", {})

    qc_text = simple_llm_call(
        llm,
        "You check for factual accuracy and safety issues in educational videos.",
        f"Review this planned video timeline and list potential issues or fact checks.\n\n{timeline}",
    )

    production["qc_notes"] = [qc_text]
    state["production"] = production
    return state


def deliver_export_node(state: Dict[str, Any], llm: ChatOpenAI) -> Dict[str, Any]:
    production = state.get("production", {})
    timeline = production.get("video_timeline", {})
    qc_notes = production.get("qc_notes", [])

    export_text = simple_llm_call(
        llm,
        "You prepare metadata for LMS/calendar export.",
        f"Given this timeline and QC notes, create:\n"
        f"- a title\n- short description\n- tags\n- estimated length\n"
        f"- suggested LMS module name\n- suggested publish date offset.\n\n"
        f"Timeline:\n{timeline}\n\nQC:\n{qc_notes}",
    )

    production["export_metadata"] = {"raw": export_text}
    state["production"] = production
    return state
