import os

from dotenv import load_dotenv

from graphs.main_graph import build_main_graph

load_dotenv()


def run_pipeline(raw_text: str):
    graph = build_main_graph()
    initial_state = {
        "ingestion": {
            "raw_text": raw_text,
        },
        "story": {},
        "production": {},
    }

    final_state = graph.invoke(initial_state)
    return final_state


if __name__ == "__main__":
    sample_file = os.path.join(os.path.dirname(__file__), "..", "clips_material.txt")
    with open(sample_file, "r") as f:
        example_text = f.read()
    result = run_pipeline(example_text)
    print(result.keys())
