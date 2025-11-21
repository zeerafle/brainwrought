from typing import Any, Dict

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from agents.ingestion_agents import (
    key_concepts_and_summary_node,
    pdf_to_pages_node,
    quiz_generator_node,
    structure_and_toc_node,
)
from config import get_llm
from states import PipelineState


def build_ingestion_graph(llm: ChatOpenAI | None = None):
    llm = llm or get_llm()

    def pdf_to_pages(state: Dict[str, Any]) -> Dict[str, Any]:
        return pdf_to_pages_node(state, llm)

    def structure_and_toc(state: Dict[str, Any]) -> Dict[str, Any]:
        return structure_and_toc_node(state, llm)

    def key_concepts_and_summary(state: Dict[str, Any]) -> Dict[str, Any]:
        return key_concepts_and_summary_node(state, llm)

    def quiz_generator(state: Dict[str, Any]) -> Dict[str, Any]:
        return quiz_generator_node(state, llm)

    graph = StateGraph(PipelineState)
    graph.add_node(pdf_to_pages)
    graph.add_node(structure_and_toc)
    graph.add_node(key_concepts_and_summary)
    graph.add_node(quiz_generator)

    graph.add_edge(START, "pdf_to_pages")
    graph.add_edge("pdf_to_pages", "structure_and_toc")
    graph.add_edge("structure_and_toc", "key_concepts_and_summary")
    graph.add_edge("key_concepts_and_summary", "quiz_generator")
    graph.add_edge("quiz_generator", END)

    return graph.compile()
