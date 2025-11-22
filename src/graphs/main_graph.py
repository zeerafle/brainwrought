from typing import Any, Dict

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from config import get_llm
from graphs.ingestion import build_ingestion_graph
from graphs.production import build_production_graph
from graphs.story_studio import build_story_studio_graph
from states import PipelineState


def build_main_graph(llm: BaseChatModel | None = None):
    llm = llm or get_llm()

    ingestion_graph = build_ingestion_graph(llm)
    story_graph = build_story_studio_graph(llm)
    production_graph = build_production_graph(llm)

    def run_ingestion(state: Dict[str, Any]) -> Dict[str, Any]:
        return ingestion_graph.invoke(state)

    def run_story_studio(state: Dict[str, Any]) -> Dict[str, Any]:
        return story_graph.invoke(state)

    def run_production(state: Dict[str, Any]) -> Dict[str, Any]:
        return production_graph.invoke(state)

    graph = StateGraph(PipelineState)
    graph.add_node("ingestion_pipeline", run_ingestion)
    graph.add_node("story_studio_pipeline", run_story_studio)
    graph.add_node("production_pipeline", run_production)

    graph.add_edge(START, "ingestion_pipeline")
    graph.add_edge("ingestion_pipeline", "story_studio_pipeline")
    graph.add_edge("story_studio_pipeline", "production_pipeline")
    graph.add_edge("production_pipeline", END)

    return graph.compile()
