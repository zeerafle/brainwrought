from pathlib import Path

from dotenv import load_dotenv

from graphs.main_graph import build_main_graph

load_dotenv()


def run_pipeline(raw_text_or_pdf_path: str | Path):
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

    compiled_graph = build_main_graph()
    result = compiled_graph.invoke(initial_state)
    return result


if __name__ == "__main__":
    # Example with PDF path
    sample_pdf_path = "/home/zeerafle/Projects/brainwrought/CLIPS basics.pdf"
    result = run_pipeline(sample_pdf_path)
    print(result.keys())

    # Example with raw text
    # raw_text = "This is some sample text content..."
    # result = run_pipeline(raw_text)
    # print(result.keys())
