"""
Production agents with Voice Design integration.
Caches designed voices to avoid regeneration.
"""

import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import modal
from elevenlabs import ElevenLabs
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from .llm_utils import simple_llm_call
from .voice_designer import VoiceDesigner


def generate_video_assets_node(
    state: Dict[str, Any], llm: BaseChatModel
) -> Dict[str, Any]:
    scenes = state.get("asset_plan", {}).get("scenes", [])
    video_assets = []
    messages_batch = []

    system_prompt = """You are a professional artist and text-to-video prompt engineer.
    You refine the given prompt to be more detail and appropriate for text-to-video model.
    Only respond with the refined prompt.
    """

    for scene in scenes:
        for asset in scene["video_assets"]:
            video_assets.append(asset)
            messages_batch.append(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(
                        content=f"Scene name: {scene['scene_name']}, Asset description: {asset}"
                    ),
                ]
            )

    # Execute all in parallel with a single batch call
    responses = llm.batch(messages_batch)

    # Extract content from responses
    video_assets_prompt = [
        resp.content if isinstance(resp.content, str) else str(resp.content)
        for resp in responses
    ]
    # get reference to the deployed Modal app
    generate_func = modal.Function.from_name("brainwrought-ltx", "LTXVideo.generate")
    # call the remote function
    video_filenames = list(generate_func.starmap([(p,) for p in video_assets_prompt]))

    return {"video_filenames": video_filenames}


# TODO: meme generation IMGFLIP


class VoiceCache:
    """Simple file-based cache for designed voices."""

    def __init__(self, cache_dir: str = ".voice_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "voice_cache.json"
        self._cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from disk."""
        if self.cache_file.exists():
            with open(self.cache_file, "r") as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        """Save cache to disk."""
        with open(self.cache_file, "w") as f:
            json.dump(self._cache, f, indent=2)

    def get_cached_voice(self, voice_description: str, language: str) -> Optional[str]:
        """
        Get cached voice ID if available.

        Args:
            voice_description: Voice description used for design
            language: Language code

        Returns:
            Voice ID string if cached, None otherwise
        """
        cache_key = f"{language}:{voice_description}"
        cached_data = self._cache.get(cache_key)
        if cached_data and isinstance(cached_data, dict):
            return cached_data.get("voice_id")
        return None

    def cache_voice(self, voice_description: str, language: str, voice_id: str):
        """
        Cache a designed voice.

        Args:
            voice_description: Voice description used for design
            language: Language code
            voice_id: ElevenLabs voice ID
        """
        cache_key = f"{language}:{voice_description}"
        self._cache[cache_key] = {
            "voice_id": voice_id,
            "description": voice_description,
            "language": language,
        }
        self._save_cache()
        print(f"💾 Cached voice: {cache_key} -> {voice_id}")


def voice_and_timing_node(
    state: Dict[str, Any],
    llm: BaseChatModel,
    elevenlabs_api_key: str = None,
    output_dir: str = "generated_audio",
    use_voice_design: bool = True,
    voice_design_preview_index: int = 0,
) -> Dict[str, Any]:
    """
    Generate voice-over audio with Voice Design using existing dialogue_vo from scenes.

    Features:
    - Uses pre-generated dialogue_vo from state.scenes (no LLM regeneration)
    - Auto-generates custom voices based on audience persona
    - Supports multiple languages via state.language
    - Caches designed voices to avoid regeneration
    - Falls back to preset voices if design fails

    Args:
        state: Pipeline state with scenes (containing dialogue_vo), audience_profile, language
        llm: Language model (not used for VO text, only kept for compatibility)
        elevenlabs_api_key: ElevenLabs API key
        output_dir: Directory for audio files
        use_voice_design: Whether to design custom voice (vs using presets)
        voice_design_preview_index: Which preview to select (0-2)

    Returns:
        Dict with voice_timing containing audio and metadata
    """
    scenes = state.get("scenes", [])
    audience_profile = state.get("audience_profile", {})
    language = state.get("language", "en")

    # Initialize API
    if not elevenlabs_api_key:
        elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY", "")

    if not elevenlabs_api_key:
        return {"voice_timing": [{"error": "No ElevenLabs API key provided"}]}

    # Phase 1: Design or select voice
    voice_cache = VoiceCache()
    voice_id = None
    voice_config = {}

    if use_voice_design:
        designer = VoiceDesigner(
            api_key=elevenlabs_api_key,
            audience_profile=audience_profile,
            language=language,
        )

        voice_description = designer.generate_voice_description()

        # Check cache first
        cached_voice_id = voice_cache.get_cached_voice(voice_description, language)

        if cached_voice_id:
            print(f"♻️  Using cached voice: {cached_voice_id}")
            voice_id = cached_voice_id
            voice_config = {
                "source": "cached",
                "description": voice_description,
                "language": language,
            }
        else:
            # Design new voice
            print("🎨 Designing new custom voice...")
            design_result = designer.design_voice(
                preview_selection_index=voice_design_preview_index
            )

            if design_result["success"]:
                # Create permanent voice from preview
                generated_voice_id = design_result["selected_generated_voice_id"]
                voice_name = f"AutoVoice_{language}_{audience_profile.get('core_persona', {}).get('name', 'default')}"

                try:
                    voice_id = designer.create_voice_from_design(
                        generated_voice_id=generated_voice_id,
                        voice_name=voice_name,
                        voice_description=voice_description,
                    )

                    # Cache the voice
                    voice_cache.cache_voice(voice_description, language, voice_id)

                    voice_config = {
                        "source": "designed",
                        "description": voice_description,
                        "language": language,
                        "generated_from": generated_voice_id,
                        "all_preview_ids": [
                            p["generated_voice_id"]
                            for p in design_result["all_previews"]
                        ],
                    }

                except Exception as e:
                    print(f"⚠️  Voice creation failed, using fallback: {e}")
                    voice_id = "JBFqnCBsd6RMkjVDRZzb"  # Fallback
            else:
                print("⚠️  Voice design failed, using fallback")
                voice_id = "JBFqnCBsd6RMkjVDRZzb"  # Fallback
    else:
        # Use preset voice
        voice_id = "JBFqnCBsd6RMkjVDRZzb"  # Default
        voice_config = {"source": "preset"}

    print(f"🎙️  Using voice ID: {voice_id}")

    # Phase 2: Extract dialogue_vo from scenes (no LLM regeneration needed)
    # The dialogue_vo was already generated by scene_by_scene_script_node in story_agents.py
    scene_vo_data = []
    for scene in scenes:
        if isinstance(scene, dict):
            scene_number = scene.get("scene_number", 0)
            dialogue_vo = scene.get("dialogue_vo", "")

            if not dialogue_vo:
                print(f"⚠️  Warning: Scene {scene_number} has no dialogue_vo, skipping")
                continue

            scene_vo_data.append(
                {
                    "scene_number": scene_number,
                    "dialogue_vo": dialogue_vo,
                }
            )
        else:
            print(f"⚠️  Warning: Unexpected scene format: {type(scene)}")

    if not scene_vo_data:
        return {"voice_timing": [{"error": "No scenes with dialogue_vo found"}]}

    print(f"📝 Using pre-generated dialogue_vo from {len(scene_vo_data)} scenes")

    # Phase 3: Generate audio with timestamps
    client = ElevenLabs(api_key=elevenlabs_api_key)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)

    voice_timing_results = []

    for scene_data in scene_vo_data:
        scene_number = scene_data["scene_number"]
        voiceover_text = scene_data["dialogue_vo"]

        try:
            # Generate with language support
            print(f"🎤 Generating audio for scene {scene_number}...")
            response = client.text_to_speech.convert_with_timestamps(
                voice_id=voice_id,
                text=voiceover_text,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
                enable_logging=True,
                optimize_streaming_latency=1,
                language_code=language if language != "en" else None,
            )

            # Save audio - response has audio_base_64 attribute
            audio_filename = f"scene_{scene_number:03d}_{language}.mp3"
            audio_filepath = output_path / audio_filename

            # Extract audio from response
            if hasattr(response, "audio_base_64"):
                audio_bytes = base64.b64decode(response.audio_base_64)
            elif hasattr(response, "audio_content"):
                audio_bytes = base64.b64decode(response.audio_content)
            elif hasattr(response, "audio"):
                audio_data = response.audio
                if isinstance(audio_data, bytes):
                    audio_bytes = audio_data
                elif isinstance(audio_data, str):
                    audio_bytes = base64.b64decode(audio_data)
                else:
                    raise TypeError(f"Unexpected audio type: {type(audio_data)}")
            else:
                raise AttributeError(
                    f"Could not find audio data in response. "
                    f"Available attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}"
                )

            with open(audio_filepath, "wb") as f:
                f.write(audio_bytes)

            print(f"   ✅ Audio saved: {audio_filepath}")

            # Extract timestamps from alignment
            # The alignment is a CharacterAlignmentResponseModel (Pydantic model)
            actual_duration = 0.0
            timestamps = []

            if hasattr(response, "alignment") and response.alignment:
                alignment = response.alignment

                # DEBUG: Print alignment structure
                print(f"   🔍 Alignment type: {type(alignment)}")
                print(
                    f"   🔍 Alignment dir: {[a for a in dir(alignment) if not a.startswith('_')]}"
                )

                # Try to dump to dict to see structure
                if hasattr(alignment, "model_dump"):
                    alignment_dict = alignment.model_dump()
                    print(f"   🔍 Alignment dict keys: {alignment_dict.keys()}")
                    print(
                        f"   🔍 Alignment dict sample: {str(alignment_dict)[:200]}..."
                    )

                    # Extract character alignments
                    # Common structures: {"characters": [...], "character_start_times_seconds": [...]}
                    if (
                        "characters" in alignment_dict
                        and "character_start_times_seconds" in alignment_dict
                    ):
                        # Format: separate arrays for characters, starts, ends
                        characters = alignment_dict["characters"]
                        char_starts = alignment_dict["character_start_times_seconds"]
                        char_ends = alignment_dict.get(
                            "character_end_times_seconds", []
                        )

                        timestamps = [
                            {
                                "character": characters[i]
                                if i < len(characters)
                                else "",
                                "start": char_starts[i] if i < len(char_starts) else 0,
                                "end": char_ends[i]
                                if i < len(char_ends)
                                else (
                                    char_starts[i] + 0.1 if i < len(char_starts) else 0
                                ),
                            }
                            for i in range(min(len(characters), len(char_starts)))
                        ]
                        if timestamps:
                            actual_duration = timestamps[-1]["end"]

                    elif "characters" in alignment_dict and isinstance(
                        alignment_dict["characters"], list
                    ):
                        # Check if characters is a list of dicts with timing info
                        chars = alignment_dict["characters"]
                        if chars and isinstance(chars[0], dict) and "start" in chars[0]:
                            # Format: [{"character": "H", "start": 0.0, "end": 0.1}, ...]
                            timestamps = chars
                            if timestamps:
                                actual_duration = timestamps[-1]["end"]

                # Try direct attribute access
                elif hasattr(alignment, "characters") and hasattr(
                    alignment, "character_start_times_seconds"
                ):
                    characters = alignment.characters
                    char_starts = alignment.character_start_times_seconds
                    char_ends = getattr(alignment, "character_end_times_seconds", [])

                    timestamps = [
                        {
                            "character": characters[i] if i < len(characters) else "",
                            "start": char_starts[i] if i < len(char_starts) else 0,
                            "end": char_ends[i]
                            if i < len(char_ends)
                            else (char_starts[i] + 0.1 if i < len(char_starts) else 0),
                        }
                        for i in range(min(len(characters), len(char_starts)))
                    ]
                    if timestamps:
                        actual_duration = timestamps[-1]["end"]

            print(
                f"   ⏱️  Duration: {actual_duration:.2f}s ({len(timestamps)} timestamps)"
            )

            # Get request ID
            request_id = getattr(response, "request_id", "unknown")

            voice_timing_results.append(
                {
                    "scene_id": scene_number,
                    "scene_name": f"Scene {scene_number}",
                    "text": voiceover_text,
                    "audio_path": str(audio_filepath),
                    "duration_seconds": actual_duration,
                    "character_timestamps": timestamps,
                    "request_id": request_id,
                    "voice_config": voice_config,
                    "language": language,
                }
            )

            print(f"✅ Scene {scene_number}: {actual_duration:.2f}s")

        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            print(f"❌ Scene {scene_number} failed:")
            print(f"   Error: {e}")
            print(f"   Details:\n{error_details}")

            voice_timing_results.append(
                {
                    "scene_id": scene_number,
                    "scene_name": f"Scene {scene_number}",
                    "text": voiceover_text,
                    "audio_path": None,
                    "duration_seconds": 0.0,
                    "error": str(e),
                    "error_details": error_details,
                    "voice_config": voice_config,
                    "language": language,
                }
            )

    return {"voice_timing": voice_timing_results}


def video_editor_renderer_node(
    state: Dict[str, Any],
    llm: BaseChatModel,
) -> Dict[str, Any]:
    scenes = state.get("scenes", [])
    asset_plan = state.get("asset_plan", [])
    voice_timing = state.get("voice_timing", [])

    timeline_text = simple_llm_call(
        llm,
        "You act as a non-technical video editor describing a clear edit timeline.",
        "Create a JSON-like timeline that maps scenes, assets, and voice timing for a "
        "simple linear edit.\n\n"
        f"Scenes:\n{scenes}\n\nAssets:\n{asset_plan}\n\nVoice/timing:\n{voice_timing}",
    )

    return {"video_timeline": {"raw": timeline_text}}


# TODO: find a way to make this useful (e.g. reiterate to the previous node)
def qc_and_safety_node(state: Dict[str, Any], llm: BaseChatModel) -> Dict[str, Any]:
    timeline = state.get("video_timeline", {})

    qc_text = simple_llm_call(
        llm,
        "You check for factual accuracy and safety issues in educational videos.",
        f"Review this planned video timeline and list potential issues or fact checks.\n\n{timeline}",
    )

    return {"qc_notes": [qc_text]}


def deliver_export_node(state: Dict[str, Any], llm: BaseChatModel) -> Dict[str, Any]:
    timeline = state.get("video_timeline", {})
    qc_notes = state.get("qc_notes", [])

    export_text = simple_llm_call(
        llm,
        "You prepare metadata for LMS/calendar export.",
        f"Given this timeline and QC notes, create:\n"
        f"- a title\n- short description\n- tags\n- estimated length\n"
        f"- suggested LMS module name\n- suggested publish date offset.\n\n"
        f"Timeline:\n{timeline}\n\nQC:\n{qc_notes}",
    )

    return {"export_metadata": {"raw": export_text}}
