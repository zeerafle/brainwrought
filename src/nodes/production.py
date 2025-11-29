"""Node functions for video production pipeline."""

import base64
import json
import os
from pathlib import Path
from typing import Any, Dict

import modal
from elevenlabs import ElevenLabs
from langchain_core.language_models import BaseChatModel

from utils.cache import VoiceCache
from utils.llm_utils import simple_llm_call
from utils.voice_designer import VoiceDesigner


def generate_video_assets_node(
    state: Dict[str, Any], llm: BaseChatModel
) -> Dict[str, Any]:
    """
    Generate video assets from scene descriptions using LTX Video model.

    Args:
        state: Pipeline state with asset_plan containing scenes and video_assets.
        llm: Language model for refining prompts.

    Returns:
        Dict with video_filenames list.
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    asset_plan = state.get("asset_plan", {})
    if hasattr(asset_plan, "model_dump"):
        asset_plan = asset_plan.model_dump()
    elif hasattr(asset_plan, "dict"):
        asset_plan = asset_plan.dict()

    scenes = asset_plan.get("scenes", [])
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

    responses = llm.batch(messages_batch)

    video_assets_prompt = [
        resp.content if isinstance(resp.content, str) else str(resp.content)
        for resp in responses
    ]

    session_id = state.get("session_id", "default")
    generate_func = modal.Function.from_name("brainwrought-ltx", "LTXVideo.generate")
    video_filenames = list(generate_func.starmap([(p, session_id) for p in video_assets_prompt]))

    # Update asset_plan with generated filenames
    # We need to map these back to the scenes.
    # Since we flattened the list for batch processing, we need to reconstruct.

    current_idx = 0
    updated_asset_plan = state.get("asset_plan", [])
    # Note: state["asset_plan"] is a list of SceneAssets.
    # But wait, the input to this node was state["asset_plan"] which is a list?
    # The docstring says "state: Pipeline state with asset_plan containing scenes and video_assets."
    # Let's assume asset_plan is a list of dicts.

    # Actually, we should probably update the asset_plan in the state to include the generated filenames
    # so the renderer can find them.
    # The renderer expects 'video_asset' in asset_plan to be the filename.

    # Let's iterate again and assign filenames
    for scene in scenes:
        new_assets = []
        for _ in scene["video_assets"]:
            if current_idx < len(video_filenames):
                # The filename returned by LTX is relative to volume root (e.g. "123_prompt.mp4")
                # Remotion expects "vol/123_prompt.mp4"
                filename = video_filenames[current_idx]
                new_assets.append(f"vol/{filename}")
                current_idx += 1
        scene["video_assets"] = new_assets

    return {"video_filenames": video_filenames, "asset_plan": {"scenes": scenes}}


def voice_and_timing_node(
    state: Dict[str, Any],
    llm: BaseChatModel,
    elevenlabs_api_key: str | None = None,
    output_dir: str = "generated_audio",
    use_voice_design: bool = True,
    voice_design_preview_index: int = 0,
) -> Dict[str, Any]:
    """
    Generate voice-over audio with Voice Design using existing dialogue_vo from scenes.

    Args:
        state: Pipeline state with scenes (containing dialogue_vo), audience_profile, language.
        llm: Language model (kept for compatibility, not used for VO text).
        elevenlabs_api_key: ElevenLabs API key.
        output_dir: Directory for audio files.
        use_voice_design: Whether to design custom voice (vs using presets).
        voice_design_preview_index: Which preview to select (0-2).

    Returns:
        Dict with voice_timing containing audio and metadata.
    """
    scenes = state.get("scenes", [])
    audience_profile = state.get("audience_profile", {})
    language = state.get("language", "en")

    if not elevenlabs_api_key:
        elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY", "")

    if not elevenlabs_api_key:
        return {"voice_timing": [{"error": "No ElevenLabs API key provided"}]}

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
            print("🎨 Designing new custom voice...")
            design_result = designer.design_voice(
                preview_selection_index=voice_design_preview_index
            )

            if design_result["success"]:
                generated_voice_id = design_result["selected_generated_voice_id"]
                voice_name = f"AutoVoice_{language}_{audience_profile.get('core_persona', {}).get('name', 'default')}"

                try:
                    voice_id = designer.create_voice_from_design(
                        generated_voice_id=generated_voice_id,
                        voice_name=voice_name,
                        voice_description=voice_description,
                    )

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
                    voice_id = "JBFqnCBsd6RMkjVDRZzb"
            else:
                print("⚠️  Voice design failed, using fallback")
                voice_id = "h2dQOVyUfIDqY2whPOMo"
    else:
        voice_id = "h2dQOVyUfIDqY2whPOMo"
        voice_config = {"source": "preset"}

    print(f"🎙️  Using voice ID: {voice_id}")

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

    client = ElevenLabs(api_key=elevenlabs_api_key)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)

    voice_timing_results = []

    for scene_data in scene_vo_data:
        scene_number = scene_data["scene_number"]
        voiceover_text = scene_data["dialogue_vo"]

        audio_filename = f"scene_{scene_number:03d}_{language}.mp3"
        audio_filepath = output_path / audio_filename
        json_filename = f"scene_{scene_number:03d}_{language}.json"
        json_filepath = output_path / json_filename

        # Check if audio and metadata already exist
        if audio_filepath.exists() and json_filepath.exists():
            print(f"♻️  Using cached audio for scene {scene_number}...")
            try:
                with open(json_filepath, "r") as f:
                    cached_data = json.load(f)

                # Check if text matches and we have word_timestamps
                cached_text = cached_data.get("text", "")
                # Simple normalization for comparison (strip whitespace)
                if cached_text.strip() == voiceover_text.strip():
                    if "word_timestamps" in cached_data:
                        voice_timing_results.append(cached_data)
                        continue
                    else:
                        print(f"⚠️  Cached data missing word_timestamps, regenerating...")
                else:
                    print(f"⚠️  Cached text differs from current text, regenerating...")
                    print(f"    Cached: {cached_text[:50]}...")
                    print(f"    Current: {voiceover_text[:50]}...")

            except Exception as e:
                print(f"⚠️  Failed to load cached metadata: {e}, regenerating...")

        try:
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

            actual_duration = 0.0
            timestamps = []

            if hasattr(response, "alignment") and response.alignment:
                alignment = response.alignment

                if hasattr(alignment, "model_dump"):
                    alignment_dict = alignment.model_dump()

                    if (
                        "characters" in alignment_dict
                        and "character_start_times_seconds" in alignment_dict
                    ):
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
                        chars = alignment_dict["characters"]
                        if chars and isinstance(chars[0], dict) and "start" in chars[0]:
                            timestamps = chars
                            if timestamps:
                                actual_duration = timestamps[-1]["end"]

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

            # Group characters into words
            word_timestamps = []
            current_word = ""
            word_start = 0.0

            for ts in timestamps:
                char = ts["character"]
                if not current_word and char.strip():
                    word_start = ts["start"]

                if char == " ":
                    if current_word:
                        # Use the END of the space to keep the word visible during the pause
                        word_timestamps.append({
                            "word": current_word,
                            "start": word_start,
                            "end": ts["end"]
                        })
                        current_word = ""
                else:
                    current_word += char
                    # Update end time for the current word
                    word_end = ts["end"]

            # Add last word if exists
            if current_word:
                word_timestamps.append({
                    "word": current_word,
                    "start": word_start,
                    "end": word_end
                })

            # Post-processing: Bridge small gaps between words to prevent flickering
            # This ensures the word stays on screen until the next one starts (if gap is small)
            for i in range(len(word_timestamps) - 1):
                current_item = word_timestamps[i]
                next_item = word_timestamps[i+1]

                gap = next_item["start"] - current_item["end"]
                # If gap is less than 0.5s, extend current word to meet next word
                if 0 < gap < 0.5:
                    current_item["end"] = next_item["start"]

            print(
                f"   ⏱️  Duration: {actual_duration:.2f}s ({len(timestamps)} chars, {len(word_timestamps)} words)"
            )

            request_id = getattr(response, "request_id", "unknown")

            result_data = {
                "scene_id": scene_number,
                "scene_name": f"Scene {scene_number}",
                "text": voiceover_text,
                "audio_path": str(audio_filepath),
                "duration_seconds": actual_duration,
                "character_timestamps": timestamps,
                "word_timestamps": word_timestamps,
                "request_id": request_id,
                "voice_config": voice_config,
                "language": language,
            }

            voice_timing_results.append(result_data)

            # Cache the metadata
            with open(json_filepath, "w") as f:
                json.dump(result_data, f, indent=2)

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
    """
    Render video using Remotion on Modal.

    Args:
        state: Pipeline state with scenes, asset_plan, and voice_timing.
        llm: Language model (unused for rendering but kept for signature).

    Returns:
        Dict with video_timeline containing the path to the rendered video.
    """
    scenes = state.get("scenes", [])
    asset_plan = state.get("asset_plan", [])
    voice_timing = state.get("voice_timing", [])

    # Upload audio files to Modal Volume AND copy to local dev volume
    print("📤 Uploading audio assets to Modal and syncing locally...")
    session_id = state.get("session_id", "default_session")

    # Ensure local dev volume structure exists
    local_vol_path = Path("remotion_src/public/vol")
    local_session_audio_path = local_vol_path / "sessions" / session_id / "audio"
    local_session_audio_path.mkdir(parents=True, exist_ok=True)

    try:
        assets_vol = modal.Volume.from_name("ltx-outputs", create_if_missing=True)
        with assets_vol.batch_upload(force=True) as batch:
            for vt in voice_timing:
                local_audio_path = vt.get("audio_path")
                if local_audio_path and os.path.exists(local_audio_path):
                    filename = os.path.basename(local_audio_path)

                    # 1. Upload to Modal (remote)
                    remote_path = f"sessions/{session_id}/audio/{filename}"
                    batch.put_file(local_audio_path, remote_path)

                    # 2. Copy to local dev volume (for Podman/local preview)
                    import shutil
                    dest_path = local_session_audio_path / filename
                    shutil.copy2(local_audio_path, dest_path)

                    # Also copy the JSON metadata for debugging/reference
                    json_src = local_audio_path.replace(".mp3", ".json")
                    if os.path.exists(json_src):
                        shutil.copy2(json_src, local_session_audio_path / os.path.basename(json_src))

                    # Update path in props to be relative for Remotion (vol/sessions/<id>/audio/filename)
                    # Since volume is mounted at public/vol
                    vt["audio_path"] = f"vol/sessions/{session_id}/audio/{filename}"
                else:
                    print(f"⚠️ Audio file not found: {local_audio_path}")
    except Exception as e:
        print(f"⚠️ Failed to upload/sync audio assets: {e}")

    # Construct props for Remotion
    # Ensure asset_plan is serializable (convert Pydantic models to dicts)
    if hasattr(asset_plan, "model_dump"):
        asset_plan = asset_plan.model_dump()
    elif hasattr(asset_plan, "dict"):
        asset_plan = asset_plan.dict()

    # Calculate total duration from voice timings
    calculated_duration = sum(vt.get("duration_seconds", 0) for vt in voice_timing)
    # Add a small buffer (e.g. 1 second)
    total_duration = calculated_duration + 1.0

    props = {
        "scenes": scenes,
        "asset_plan": asset_plan,
        "voice_timing": voice_timing,
        "total_duration": total_duration,
    }

    # Save props locally for Remotion Studio development
    local_props_path = Path("remotion_src/input_props.json")
    try:
        with open(local_props_path, "w") as f:
            json.dump(props, f, indent=2)
        print(f"💾 Saved local props to {local_props_path}")
    except Exception as e:
        print(f"⚠️ Failed to save local props: {e}")

    print("🚀 Triggering Remotion render on Modal...")

    try:
        RemotionRenderer = modal.Cls.from_name(
            "brainwrought-renderer", "RemotionRenderer"
        )
        renderer = RemotionRenderer()
        video_bytes = renderer.render_video.remote(props)

        output_dir = Path("rendered_videos")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "final_video.mp4"

        with open(output_path, "wb") as f:
            f.write(video_bytes)

        print(f"✅ Video rendered to: {output_path}")

        return {
            "video_timeline": {"video_path": str(output_path), "status": "rendered"}
        }

    except Exception as e:
        print(f"❌ Rendering failed: {e}")
        # Fallback to text description if render fails
        return {"video_timeline": {"error": str(e), "status": "failed"}}


def qc_and_safety_node(state: Dict[str, Any], llm: BaseChatModel) -> Dict[str, Any]:
    """
    Quality check and safety review of video content.

    Args:
        state: Pipeline state with video_timeline.
        llm: Language model for QC analysis.

    Returns:
        Dict with qc_notes list.
    """
    timeline = state.get("video_timeline", {})

    qc_text = simple_llm_call(
        llm,
        "You check for factual accuracy and safety issues in educational videos.",
        f"Review this planned video timeline and list potential issues or fact checks.\n\n{timeline}",
    )

    return {"qc_notes": [qc_text]}


def deliver_export_node(state: Dict[str, Any], llm: BaseChatModel) -> Dict[str, Any]:
    """
    Prepare export metadata for video delivery.

    Args:
        state: Pipeline state with video_timeline and qc_notes.
        llm: Language model for metadata generation.

    Returns:
        Dict with export_metadata.
    """
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
