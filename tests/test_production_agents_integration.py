"""
Simple integration test - Real LLM + Real Modal calls

Prerequisites:
    1. modal setup (one-time authentication)
    2. modal deploy src/modal_app.py (deploy your app)
    3. export GOOGLE_API_KEY=your_key (or OPENAI_API_KEY)

Run:
    RUN_REAL_INTEGRATION_TESTS=1 pytest tests/test_production_agents_integration.py -v -s
"""

import os

import pytest

from src.config import get_llm

# Import the node from the actual module
from src.nodes import generate_video_assets_node


@pytest.mark.skipif(
    os.environ.get("RUN_REAL_INTEGRATION_TESTS") != "1",
    reason="Real LLM/Modal integration tests are disabled. Set RUN_REAL_INTEGRATION_TESTS=1 to enable.",
)
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
    # NOTE: use the canonical `video_asset` key (singular) expected by the node
    state = {
        "session_id": "integration-test-session",
        "asset_plan": {
            "scenes": [
                {
                    "scene_name": "Test Scene 1",
                    "video_asset": [
                        "A student studying at a desk",
                        "Close-up of textbook pages",
                    ],
                }
            ]
        },
    }

    # 3. Call the node with real APIs
    print("\n🎬 Generating videos with real LLM and Modal...")
    result = generate_video_assets_node(state, llm)

    # 4. Check results
    print(f"\n✅ Generated {len(result.get('video_filenames', []))} videos:")
    for i, filename in enumerate(result.get("video_filenames", []), 1):
        print(f"  {i}. {filename}")

    assert "video_filenames" in result
    assert len(result["video_filenames"]) > 0


if __name__ == "__main__":
    test_generate_video_with_real_apis()
