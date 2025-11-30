"""Node functions for content ingestion and analysis."""

from typing import Any, Dict, List

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field

from utils.llm_utils import simple_llm_call, structured_llm_call


class LectureAnalysis(BaseModel):
    """Structured output for complete lecture analysis."""

    toc: str = Field(
        description="Hierarchical table of contents extracted from the lecture"
    )
    key_concepts: List[str] = Field(
        description="List of 5-15 key concepts with short definitions",
        min_length=5,
        max_length=15,
    )
    summary: str = Field(
        description="Comprehensive summary of the lecture in 3-6 concise paragraphs"
    )
    language: str = Field(
        description="Language of the lecture with ISO 639 language codes"
    )


def pdf_to_pages_node(state: Dict[str, Any], llm: BaseChatModel) -> Dict[str, Any]:
    """
    Convert PDF file into list of pages.

    Args:
        state: Pipeline state with pdf_path or raw_text.
        llm: Language model (not used in this node).

    Returns:
        Dict with pages list.
    """
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


def combined_analysis_node(state: Dict[str, Any], llm: BaseChatModel) -> Dict[str, Any]:
    """
    Extract TOC, key concepts, summary, and language in one call.

    Args:
        state: Pipeline state with pages.
        llm: Language model for analysis.

    Returns:
        Dict with toc, key_concepts, summary, and language.
    """
    pages: List[str] = state.get("pages", [])

    joined = "\n\n".join(pages)

    system_prompt = """You are an expert at analyzing lecture materials.
You extract table of contents, identify key concepts, and create summaries."""

    user_prompt = f"""Analyze the following lecture pages and provide:

1. A hierarchical table of contents (TOC) - infer the structure even if not explicitly stated
2. 5-15 key concepts with brief definitions
3. A comprehensive summary in 3-6 concise paragraphs
4. What language does the lecture notes use. Write in ISO 639 language codes.

Return the content with the same language as the source language

Lecture content:
{joined}"""

    analysis = structured_llm_call(llm, system_prompt, user_prompt, LectureAnalysis)

    return {
        "toc": [{"raw": analysis.toc}],
        "key_concepts": analysis.key_concepts,
        "summary": analysis.summary,
        "language": analysis.language,
    }


def quiz_generator_node(state: Dict[str, Any], llm: BaseChatModel) -> Dict[str, Any]:
    """
    Generate quiz questions from key concepts and summary.

    Args:
        state: Pipeline state with key_concepts and summary.
        llm: Language model for quiz generation.

    Returns:
        Dict with quiz_items list.
    """
    concepts = state.get("key_concepts", [])
    summary = state.get("summary", "")
    language = state.get("language", "")

    quiz_text = simple_llm_call(
        llm,
        "You create quiz questions and answers from lecture material.",
        f"Using these key concepts and summary, create 5-10 Q&A items in a simple numbered list. \n\n"
        f"Key concepts:\n{concepts}\n\nSummary:\n{summary}"
        f"Keep the source language: {language}",
    )

    return {"quiz_items": [{"raw": quiz_text}]}
