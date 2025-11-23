from typing import Any, Dict

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from config import get_llm
from nodes.meme import (
    hook_concept_node,
    language_slang_node,
    meme_concept_node,
    social_media_trends_node,
)
from states import PipelineState


def build_hook_and_meme_graph(llm: BaseChatModel | None = None):
    llm = llm or get_llm()

    async def social_media_trends(state: Dict[str, Any]):
        return await social_media_trends_node(state, llm)

    async def language_slang(state: Dict[str, Any]) -> Dict[str, Any]:
        return await language_slang_node(state, llm)

    def hook_concept(state: Dict[str, Any]) -> Dict[str, Any]:
        return hook_concept_node(state, llm)

    def meme_concept(state: Dict[str, Any]) -> Dict[str, Any]:
        return meme_concept_node(state, llm)

    graph = StateGraph(PipelineState)
    graph.add_node("social_media_trends", social_media_trends)
    graph.add_node("language_slang", language_slang)
    graph.add_node("hook_concept", hook_concept)
    graph.add_node("meme_concept", meme_concept)

    graph.add_edge(START, "social_media_trends")
    graph.add_edge(START, "language_slang")
    graph.add_edge("social_media_trends", "hook_concept")
    graph.add_edge("language_slang", "hook_concept")
    graph.add_edge("social_media_trends", "meme_concept")
    graph.add_edge("language_slang", "meme_concept")
    graph.add_edge("hook_concept", END)
    graph.add_edge("meme_concept", END)

    return graph.compile()
