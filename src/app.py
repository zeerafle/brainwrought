import asyncio
from pathlib import Path

from dotenv import load_dotenv
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from graphs.main_graph import build_main_graph
from utils.cache import setup_llm_cache

load_dotenv()

# Enable LLM caching to save costs during testing/development
# This will cache responses in .langchain.db
setup_llm_cache()


async def run_pipeline(raw_text_or_pdf_path: str | Path, thread_id: str = "default"):
    """
    Run the pipeline with either raw text or a PDF file path.

    Args:
        raw_text_or_pdf_path: Either a string of raw text content or a path to a PDF file

    Returns:
        The final state after running the pipeline
    """
    # Convert to Path object if it's a string
    if isinstance(raw_text_or_pdf_path, str):
        # Try to interpret as a file path
        potential_path = Path(raw_text_or_pdf_path)
        is_file = potential_path.exists() and potential_path.is_file()
    else:
        potential_path = raw_text_or_pdf_path
        is_file = potential_path.exists() and potential_path.is_file()

    # Build initial state based on whether it's a file or raw text
    if is_file:
        initial_state = {
            "pdf_path": str(potential_path),
        }
    else:
        initial_state = {
            "raw_text": raw_text_or_pdf_path
            if isinstance(raw_text_or_pdf_path, str)
            else str(raw_text_or_pdf_path),
        }

    # Create a checkpointer (persists in memory during the session)
    async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
        compiled_graph = build_main_graph(checkpointer=checkpointer)

        # configuration with thread_id enables checkpointing
        config = {"configurable": {"thread_id": thread_id}}

        # if graph fails mid-way, re-running with same thread_id will resume from checkpoint
        result = await compiled_graph.ainvoke(initial_state, config=config)
        return result


if __name__ == "__main__":

    async def main():
        # Example with PDF path
        # sample_pdf_path = "/home/zeerafle/Projects/brainwrought/CLIPS basics.pdf"
        sample_pdf_path = "/home/zeerafle/WorkFolder/Documents/College/Sınırsel Hesap ve Sınırsel Ağlar/yapay-sinir-aglariercan-oztemel-ch1-2.pdf"
        result = await run_pipeline(sample_pdf_path, thread_id="test_run_1")
        print(result.keys())

        # Example with raw text
        # raw_text = "This is some sample text content..."
        # result = run_pipeline(raw_text)
        # print(result.keys())

    asyncio.run(main())
