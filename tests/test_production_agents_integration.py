"""
Simple integration test - Real LLM + Real Modal calls

Prerequisites:
    1. modal setup (one-time authentication)
    2. modal deploy src/modal_app.py (deploy your app)
    3. export GOOGLE_API_KEY=your_key (or OPENAI_API_KEY)

Run: pytest tests/test_production_agents_integration.py -v -s
"""

from src.agents.production_agents import generate_video_assets_node
from src.config import get_llm


def test_generate_video_with_real_apis():
    """
    Test video generation with REAL LLM and REAL Modal

    ⚠️ This will:
    - Call real LLM API (small cost)
    - Generate actual videos via Modal (larger cost)
    """
    # 1. Setup real LLM
    llm = get_llm()

    # 2. Create test state
    state = {
        "asset_plan": {
            "scenes": [
                {
                    "video_assets": [
                        "A student studying at a desk",
                        "Close-up of textbook pages",
                    ]
                }
            ]
        }
    }

    # 3. Call the node with real APIs
    print("\n🎬 Generating videos with real LLM and Modal...")
    result = generate_video_assets_node(state, llm)

    # 4. Check results
    print(f"\n✅ Generated {len(result['video_filenames'])} videos:")
    for i, filename in enumerate(result["video_filenames"], 1):
        print(f"  {i}. {filename}")

    assert "video_filenames" in result
    assert len(result["video_filenames"]) > 0


if __name__ == "__main__":
    # Can run directly: python tests/test_production_agents_integration.py
    test_generate_video_with_real_apis()
