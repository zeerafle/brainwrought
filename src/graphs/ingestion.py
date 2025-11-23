from typing import Any, Dict

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from config import get_gemini_llm, get_llm
from nodes.ingestion import (
    combined_analysis_node,
    pdf_to_pages_node,
    quiz_generator_node,
)
from states import PipelineState


def build_ingestion_graph(llm: BaseChatModel | None = None):
    llm = llm or get_llm()
    gemini_llm = get_gemini_llm()

    def pdf_to_pages(state: Dict[str, Any]) -> Dict[str, Any]:
        return pdf_to_pages_node(state, llm)

    def combined_analysis(state: Dict[str, Any]) -> Dict[str, Any]:
        return combined_analysis_node(state, gemini_llm)

    def quiz_generator(state: Dict[str, Any]) -> Dict[str, Any]:
        return quiz_generator_node(state, llm)

    graph = StateGraph(PipelineState)
    graph.add_node("pdf_to_pages", pdf_to_pages)
    graph.add_node("combined_analysis", combined_analysis)
    graph.add_node("quiz_generator", quiz_generator)

    graph.add_edge(START, "pdf_to_pages")
    graph.add_edge("pdf_to_pages", "combined_analysis")
    graph.add_edge("combined_analysis", "quiz_generator")
    graph.add_edge("quiz_generator", END)

    return graph.compile()
