from typing import Any, Dict

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from config import get_llm
from graphs.hook_meme import build_hook_and_meme_graph
from nodes.story import (
    asset_planner_node,
    audience_and_style_profiler_node,
    scene_by_scene_script_node,
)
from states import PipelineState


def build_story_studio_graph(llm: BaseChatModel | None = None):
    llm = llm or get_llm()

    hook_and_meme_concept_graph = build_hook_and_meme_graph(llm)

    async def audience_and_style_profiler(state: Dict[str, Any]):
        return audience_and_style_profiler_node(state, llm)

    async def run_hook_and_meme(state: Dict[str, Any]):
        return await hook_and_meme_concept_graph.ainvoke(state)

    async def scene_by_scene_script(state: Dict[str, Any]) -> Dict[str, Any]:
        return scene_by_scene_script_node(state, llm)

    async def asset_planner(state: Dict[str, Any]) -> Dict[str, Any]:
        return asset_planner_node(state, llm)

    graph = StateGraph(PipelineState)
    graph.add_node("audience_and_style_profiler", audience_and_style_profiler)
    graph.add_node("hook_and_meme_concept", run_hook_and_meme)
    graph.add_node("scene_by_scene_script", scene_by_scene_script)
    graph.add_node("asset_planner", asset_planner)

    graph.add_edge(START, "audience_and_style_profiler")
    graph.add_edge("audience_and_style_profiler", "hook_and_meme_concept")
    graph.add_edge("hook_and_meme_concept", "scene_by_scene_script")
    graph.add_edge("scene_by_scene_script", "asset_planner")
    graph.add_edge("asset_planner", END)

    return graph.compile()
