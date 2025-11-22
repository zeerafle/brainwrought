from typing import Any, Dict

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from agents.production_agents import (
    deliver_export_node,
    qc_and_safety_node,
    video_editor_renderer_node,
    voice_and_timing_node,
)
from config import get_llm
from states import PipelineState


def build_production_graph(llm: BaseChatModel | None = None):
    llm = llm or get_llm()

    def voice_and_timing(state: Dict[str, Any]) -> Dict[str, Any]:
        return voice_and_timing_node(state, llm)

    def video_editor_renderer(state: Dict[str, Any]) -> Dict[str, Any]:
        return video_editor_renderer_node(state, llm)

    def qc_and_safety(state: Dict[str, Any]) -> Dict[str, Any]:
        return qc_and_safety_node(state, llm)

    def deliver_export(state: Dict[str, Any]) -> Dict[str, Any]:
        return deliver_export_node(state, llm)

    graph = StateGraph(PipelineState)
    graph.add_node(voice_and_timing)
    graph.add_node(video_editor_renderer)
    graph.add_node(qc_and_safety)
    graph.add_node(deliver_export)

    graph.add_edge(START, "voice_and_timing")
    graph.add_edge("voice_and_timing", "video_editor_renderer")
    graph.add_edge("video_editor_renderer", "qc_and_safety")
    graph.add_edge("qc_and_safety", "deliver_export")
    graph.add_edge("deliver_export", END)

    return graph.compile()
