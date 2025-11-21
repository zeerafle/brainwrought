from typing import Any, Dict, List

from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI

from agents.llm_utils import simple_llm_call


def pdf_to_pages_node(state: Dict[str, Any], llm: ChatOpenAI) -> Dict[str, Any]:
    """Converts a PDF file into a list of pages."""
    raw_text = state.get("raw_text", "")
    pdf_path = state.get("pdf_path", "")

    if raw_text:
        pages = [p for p in raw_text.split("\f") if p.strip()]
    elif pdf_path:
        loader = PyPDFLoader(
            pdf_path,
            mode="page",
            extract_images=False,
        )
        docs = loader.load()
        pages = [p.page_content for p in docs]
    else:
        pages = []

    return {"pages": pages}


def structure_and_toc_node(state: Dict[str, Any], llm: ChatOpenAI) -> Dict[str, Any]:
    pages: List[str] = state.get("pages", [])
    joined = "\n\n".join(pages[:10])

    toc_text = simple_llm_call(
        llm,
        "You extract a clean table-of-contents from lecture text.",
        f"From the following pages, infer a hierarchical TOC. \n\n{joined}",
    )

    return {"toc": [{"raw": toc_text}]}


def key_concepts_node(
    state: Dict[str, Any],
    llm: ChatOpenAI,
) -> Dict[str, Any]:
    pages = state.get("pages", [])
    joined = "\n\n".join(pages[:15])

    concepts_text = simple_llm_call(
        llm,
        "You extract 5-15 key concepts from lecture material.",
        f"Extract key concepts and short definitions from: \n\n{joined}",
    )

    key_concepts = [c.strip() for c in concepts_text.split("\n") if c.strip()]
    return {"key_concepts": key_concepts}


def summary_node(
    state: Dict[str, Any],
    llm: ChatOpenAI,
) -> Dict[str, Any]:
    pages = state.get("pages", [])
    joined = "\n\n".join(pages[:15])

    summary_text = simple_llm_call(
        llm,
        "You summarize lectures for students.",
        f"Summarize the lecture in 3-6 concise paragraphs: \n\n{joined}",
    )

    return {"summary": summary_text}


def quiz_generator_node(state: Dict[str, Any], llm: ChatOpenAI) -> Dict[str, Any]:
    concepts = state.get("key_concepts", [])
    summary = state.get("summary", "")

    quiz_text = simple_llm_call(
        llm,
        "You create quiz questions and answers from lecture material.",
        f"Using these key concepts and summary, create 5-10 Q&A items in a simple numbered list. \n\n"
        f"Key concepts:\n{concepts}\n\nSummary:\n{summary}",
    )

    return {"quiz_items": [{"raw": quiz_text}]}
