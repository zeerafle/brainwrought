from typing import Any, Dict

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from states import PipelineState


def build_production_graph_mock(llm: BaseChatModel | None = None):
    """Mock production graph that skips expensive operations."""

    def voice_and_timing_mock(state: Dict[str, Any]) -> Dict[str, Any]:
        """Mock voice generation - returns fake data."""
        scenes = state.get("scenes", [])
        return {
            "voice_timing": [
                {
                    "scene_id": i,
                    "scene_name": f"Scene {i}",
                    "text": scene.get("dialogue_vo", ""),
                    "audio_path": f"mock_audio_{i}.mp3",
                    "duration_seconds": 5.0,
                    "character_timestamps": [],
                    "voice_config": {"source": "mock"},
                }
                for i, scene in enumerate(scenes)
            ]
        }

    def video_assets_mock(state: Dict[str, Any]) -> Dict[str, Any]:
        """Mock video generation."""
        return {"video_filenames": ["mock_video_1.mp4", "mock_video_2.mp4"]}

    def video_editor_mock(state: Dict[str, Any]) -> Dict[str, Any]:
        return {"video_timeline": {"raw": "mock timeline"}}

    def qc_mock(state: Dict[str, Any]) -> Dict[str, Any]:
        return {"qc_notes": ["mock qc note"]}

    def export_mock(state: Dict[str, Any]) -> Dict[str, Any]:
        return {"export_metadata": {"raw": "mock metadata"}}

    graph = StateGraph(PipelineState)
    graph.add_node("voice_and_timing", voice_and_timing_mock)
    graph.add_node("video_assets", video_assets_mock)
    graph.add_node("video_editor_renderer", video_editor_mock)
    graph.add_node("qc_and_safety", qc_mock)
    graph.add_node("deliver_export", export_mock)

    graph.add_edge(START, "voice_and_timing")
    graph.add_edge(START, "video_assets")
    graph.add_edge("voice_and_timing", "video_editor_renderer")
    graph.add_edge("video_assets", "video_editor_renderer")
    graph.add_edge("video_editor_renderer", "qc_and_safety")
    graph.add_edge("qc_and_safety", "deliver_export")
    graph.add_edge("deliver_export", END)

    return graph.compile()
