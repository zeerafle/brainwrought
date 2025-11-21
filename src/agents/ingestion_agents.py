from typing import Any, Dict, List

from langchain_openai import ChatOpenAI

from agents.llm_utils import simple_llm_call


def pdf_to_pages_node(state: Dict[str, Any], llm: ChatOpenAI) -> Dict[str, Any]:
    """
    Converts a PDF file into a list of pages.

    Args:
        state (Dict[str, Any]): The current state of the system.
        llm (ChatOpenAI): The language model to use for processing.

    Returns:
        Dict[str, Any]: The updated state of the system.
    """
    ingestion = state.get("ingestion", {})
    raw_text = ingestion.get("raw_text", "")
    if not raw_text:
        # TODO: implement pdf parser + chunker
        return state

    pages = [p for p in raw_text.split("\f") if p.strip()]
    ingestion["pages"] = pages
    state["ingestion"] = ingestion
    return state


def structure_and_toc_node(state: Dict[str, Any], llm: ChatOpenAI) -> Dict[str, Any]:
    ingestion = state.get("ingestion", {})
    pages: List[str] = ingestion.get("pages", [])
    joined = "\n\n".join(pages[:10])  # keep short for context

    toc_text = simple_llm_call(
        llm,
        "You extract a clean table-of-contents from lecture text.",
        f"From the following pages, infer a hierarchical TOC. \n\n{joined}",
    )

    ingestion["toc"] = [{"raw": toc_text}]
    state["ingestion"] = ingestion

    return state


def key_concepts_node(
    state: Dict[str, Any],
    llm: ChatOpenAI,
) -> Dict[str, Any]:
    ingestion = state.get("ingestion", {})
    pages = ingestion.get("pages", [])
    joined = "\n\n".join(pages[:15])

    concepts_text = simple_llm_call(
        llm,
        "You extract 5-15 key concepts from lecture material.",
        f"Extract key concepts and short definitions from: \n\n{joined}",
    )

    ingestion["key_concepts"] = [
        c.strip() for c in concepts_text.split("\n") if c.strip()
    ]
    state["ingestion"] = ingestion
    return state


def summary_node(
    state: Dict[str, Any],
    llm: ChatOpenAI,
) -> Dict[str, Any]:
    ingestion = state.get("ingestion", {})
    pages = ingestion.get("pages", [])
    joined = "\n\n".join(pages[:15])

    summary_text = simple_llm_call(
        llm,
        "You summarize lectures for students.",
        f"Summarize the lecture in 3-6 concise paragraphs: \n\n{joined}",
    )

    ingestion["summary"] = summary_text
    state["ingestion"] = ingestion
    return state


def quiz_generator_node(state: Dict[str, Any], llm: ChatOpenAI) -> Dict[str, Any]:
    ingestion = state.get("ingestion", {})
    concepts = ingestion.get("key_concepts", [])
    summary = ingestion.get("summary", "")

    # TODO: structured output
    quiz_text = simple_llm_call(
        llm,
        "You create quiz questions and answers from lecture material.",
        f"Using these key concepts and summary, create 5-10 Q&A items in a simple nubered list. \n\n"
        f"Key concepts:\n{concepts}\n\nSummary:\n{summary}",
    )

    ingestion["quiz_items"] = [{"raw": quiz_text}]
    state["ingestion"] = ingestion
    return state
