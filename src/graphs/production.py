from typing import Any, Dict

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from config import get_llm
from nodes.assets import generate_meme_assets_node, generate_sfx_assets_node
from nodes.production import (
    deliver_export_node,
    generate_video_assets_node,
    qc_and_safety_node,
    video_editor_renderer_node,
    voice_and_timing_node,
)
from states import PipelineState


def build_production_graph(llm: BaseChatModel | None = None):
    llm = llm or get_llm()

    async def voice_and_timing(state: Dict[str, Any]) -> Dict[str, Any]:
        return voice_and_timing_node(state, llm)

    async def generate_sfx(state: Dict[str, Any]) -> Dict[str, Any]:
        return generate_sfx_assets_node(state, llm)

    async def generate_video_assets(state: Dict[str, Any]) -> Dict[str, Any]:
        return await generate_video_assets_node(state, llm)

    async def generate_meme_assets(state: Dict[str, Any]) -> Dict[str, Any]:
        return await generate_meme_assets_node(state, llm)

    async def video_editor_renderer(state: Dict[str, Any]) -> Dict[str, Any]:
        return video_editor_renderer_node(state, llm)

    async def qc_and_safety(state: Dict[str, Any]) -> Dict[str, Any]:
        return qc_and_safety_node(state, llm)

    async def deliver_export(state: Dict[str, Any]) -> Dict[str, Any]:
        return deliver_export_node(state, llm)

    graph = StateGraph(PipelineState)
    graph.add_node("voice_and_timing", voice_and_timing)
    graph.add_node("generate_sfx", generate_sfx)
    graph.add_node("generate_video_assets", generate_video_assets)
    graph.add_node("generate_meme_assets", generate_meme_assets)
    graph.add_node("video_editor_renderer", video_editor_renderer)
    graph.add_node("qc_and_safety", qc_and_safety)
    graph.add_node("deliver_export", deliver_export)

    graph.add_edge(START, "voice_and_timing")
    graph.add_edge(START, "generate_video_assets")
    graph.add_edge(START, "generate_meme_assets")

    graph.add_edge("generate_video_assets", "generate_sfx")
    graph.add_edge("voice_and_timing", "video_editor_renderer")
    graph.add_edge("generate_meme_assets", "video_editor_renderer")

    graph.add_edge("generate_sfx", "video_editor_renderer")
    graph.add_edge("video_editor_renderer", "qc_and_safety")
    graph.add_edge("qc_and_safety", "deliver_export")
    graph.add_edge("deliver_export", END)

    return graph.compile()
