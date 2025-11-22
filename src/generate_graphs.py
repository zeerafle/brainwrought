"""Generate Mermaid diagrams from compiled LangGraph graphs."""

from graphs.main_graph import build_main_graph


def generate_graph_visualization():
    """Generate and save the main graph visualization."""
    graph = build_main_graph()

    # Save Mermaid syntax
    mermaid_text = graph.get_graph(xray=True).draw_mermaid()
    with open("graph.mmd", "w") as f:
        f.write(mermaid_text)
    print("✓ Saved Mermaid syntax to graph.mmd")

    # Save PNG
    try:
        image_data = graph.get_graph(xray=True).draw_mermaid_png()
        with open("graph.png", "wb") as f:
            f.write(image_data)
        print("✓ Saved PNG to graph.png")
    except Exception as e:
        print(f"⚠ Could not save PNG (requires pillow): {e}")


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    generate_graph_visualization()
