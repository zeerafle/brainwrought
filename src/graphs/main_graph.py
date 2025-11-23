from typing import Any, Dict

from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from config import USE_MOCK_PRODUCTION, get_llm
from graphs.ingestion import build_ingestion_graph

# Import both real and mock
from graphs.production import build_production_graph
from graphs.production_mock import build_production_graph_mock
from graphs.story_studio import build_story_studio_graph
from states import PipelineState


def build_main_graph(
    llm: BaseChatModel | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
    use_mock_production: bool | None = None,
):
    llm = llm or get_llm()

    # Use flag to decide which production graph
    use_mock = (
        use_mock_production if use_mock_production is not None else USE_MOCK_PRODUCTION
    )

    ingestion_graph = build_ingestion_graph(llm)
    story_graph = build_story_studio_graph(llm)
    production_graph = (
        build_production_graph_mock(llm) if use_mock else build_production_graph(llm)
    )

    async def run_ingestion(state: Dict[str, Any]) -> Dict[str, Any]:
        return await ingestion_graph.ainvoke(state)

    async def run_story_studio(state: Dict[str, Any]) -> Dict[str, Any]:
        return await story_graph.ainvoke(state)

    async def run_production(state: Dict[str, Any]) -> Dict[str, Any]:
        return await production_graph.ainvoke(state)

    graph = StateGraph(PipelineState)
    graph.add_node("ingestion_pipeline", run_ingestion)
    graph.add_node("story_studio_pipeline", run_story_studio)
    graph.add_node("production_pipeline", run_production)

    graph.add_edge(START, "ingestion_pipeline")
    graph.add_edge("ingestion_pipeline", "story_studio_pipeline")
    graph.add_edge("story_studio_pipeline", "production_pipeline")
    graph.add_edge("production_pipeline", END)

    return graph.compile(checkpointer=checkpointer)
