"""Node functions for asset generation (SFX, etc.)."""

import os
import shutil
from pathlib import Path
from typing import Any, Dict

import modal
from elevenlabs import ElevenLabs
from langchain_core.language_models import BaseChatModel


def generate_sfx_assets_node(
    state: Dict[str, Any], llm: BaseChatModel
) -> Dict[str, Any]:
    """
    Generate or retrieve SFX assets.

    Args:
        state: Pipeline state with asset_plan.
        llm: Language model (unused).

    Returns:
        Dict with updated asset_plan.
    """
    asset_plan = state.get("asset_plan", {})
    if hasattr(asset_plan, "model_dump"):
        asset_plan = asset_plan.model_dump()
    elif hasattr(asset_plan, "dict"):
        asset_plan = asset_plan.dict()

    scenes = asset_plan.get("scenes", [])

    # Directories
    sfx_stock_dir = Path("assets/stock/sfx")
    sfx_stock_dir.mkdir(parents=True, exist_ok=True)

    # Local public volume for Remotion preview
    local_vol_sfx_dir = Path("remotion_src/public/vol/stock/sfx")
    local_vol_sfx_dir.mkdir(parents=True, exist_ok=True)

    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    client = None
    if elevenlabs_api_key:
        client = ElevenLabs(api_key=elevenlabs_api_key)

    # Get existing files
    existing_files = {f.name: f for f in sfx_stock_dir.glob("*.mp3")}

    # Track all SFX files used (for Modal Volume upload)
    all_used_sfx: set[Path] = set()

    for scene in scenes:
        sfx_list = scene.get("sfx", [])
        for sfx_item in sfx_list:
            description = sfx_item.get("description", "")
            if not description:
                continue

            # Check if description matches an existing filename
            matched_file = None

            # 1. Exact match
            if description in existing_files:
                matched_file = existing_files[description]

            # 2. Fuzzy match / Contains
            if not matched_file:
                for filename, filepath in existing_files.items():
                    if (
                        description.lower() in filename.lower()
                        or filename.lower() in description.lower()
                    ):
                        matched_file = filepath
                        break

            final_path = None

            if matched_file:
                print(f"✅ Found existing SFX for '{description}': {matched_file.name}")
                final_path = matched_file
            else:
                # Generate with ElevenLabs
                if client:
                    print(f"🎨 Generating SFX for '{description}'...")
                    try:
                        # Sanitize filename
                        safe_name = "".join(
                            c if c.isalnum() else "-" for c in description
                        ).lower()
                        filename = f"{safe_name}.mp3"
                        output_path = sfx_stock_dir / filename

                        # Check if we already generated it in this run or previously but missed the dict check
                        if output_path.exists():
                            print(f"   ♻️  Using previously generated: {filename}")
                            final_path = output_path
                            existing_files[filename] = output_path  # Update cache
                        else:
                            response = client.text_to_sound_effects.convert(
                                text=description,
                                duration_seconds=2.0,  # Default duration
                                prompt_influence=0.5,
                            )

                            # Response is a generator of bytes
                            audio_data = b""
                            for chunk in response:
                                if chunk:
                                    audio_data += chunk

                            with open(output_path, "wb") as f:
                                f.write(audio_data)

                            print(f"   ✅ Generated: {output_path}")
                            final_path = output_path
                            existing_files[filename] = output_path
                            # Track this as newly generated for Modal upload
                            newly_generated_sfx.append(output_path)
                    except Exception as e:
                        print(f"   ❌ Failed to generate SFX: {e}")
                else:
                    print(f"   ⚠️  Skipping generation for '{description}' (No API Key)")

            if final_path:
                # Copy to local vol for Remotion
                dest_path = local_vol_sfx_dir / final_path.name
                if not dest_path.exists():
                    shutil.copy2(final_path, dest_path)

                # Update asset item with the path Remotion expects
                # Remotion expects "vol/stock/sfx/filename.mp3"
                sfx_item["audio_path"] = f"vol/stock/sfx/{final_path.name}"

                # Track for Modal Volume upload
                all_used_sfx.add(final_path)

    # Upload all SFX files to Modal Volume
    if all_used_sfx:
        print(f"📤 Uploading {len(all_used_sfx)} SFX file(s) to Modal Volume...")
        try:
            assets_vol = modal.Volume.from_name("ltx-outputs", create_if_missing=True)
            with assets_vol.batch_upload(force=True) as batch:
                for sfx_path in all_used_sfx:
                    # Upload to stock/sfx/ on the volume
                    # The volume is mounted at public/vol, so the path becomes vol/stock/sfx/...
                    remote_path = f"stock/sfx/{sfx_path.name}"
                    batch.put_file(str(sfx_path), remote_path)
                    print(f"   ⬆️  Uploading {sfx_path.name} -> {remote_path}")
            print("✅ SFX files uploaded to Modal Volume")
        except Exception as e:
            print(f"⚠️ Failed to upload SFX to Modal Volume: {e}")

    return {"asset_plan": {"scenes": scenes}}
