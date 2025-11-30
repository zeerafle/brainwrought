"""Node functions for asset generation (SFX, memes, etc.)."""

import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import modal
from elevenlabs import ElevenLabs
from langchain_core.language_models import BaseChatModel
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent


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

    if isinstance(asset_plan, dict):
        scenes = asset_plan.get("scenes", [])
    elif isinstance(asset_plan, list):
        scenes = asset_plan
    else:
        scenes = []

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
    newly_generated_sfx: list[Path] = []

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


def _extract_search_terms(meme_name_reference: str) -> List[str]:
    """
    Extract search terms from a meme name reference.

    Args:
        meme_name_reference: The meme name like "Drake Hotline Bling (reject/approve)"

    Returns:
        List of search terms to try.
    """
    # Remove parenthetical descriptions
    clean_name = re.sub(r"\s*\([^)]*\)\s*", " ", meme_name_reference).strip()

    # Common meme name mappings for better search results
    meme_mappings = {
        "drake": ["drake"],
        "distracted boyfriend": ["distracted", "boyfriend"],
        "expanding brain": ["brain", "expanding"],
        "change my mind": ["change my mind"],
        "two buttons": ["buttons"],
        "is this a pigeon": ["pigeon", "butterfly"],
        "woman yelling at cat": ["woman cat", "yelling"],
        "success kid": ["success"],
        "one does not simply": ["boromir", "simply"],
        "roll safe": ["roll safe", "thinking"],
        "surprised pikachu": ["pikachu"],
        "galaxy brain": ["brain"],
        "stonks": ["stonks"],
        "this is fine": ["fine", "dog fire"],
        "always has been": ["astronaut"],
        "gru's plan": ["gru"],
        "bernie sanders": ["bernie"],
        "spongebob": ["spongebob"],
        "patrick": ["patrick"],
    }

    # Check for known meme names
    lower_name = clean_name.lower()
    for meme_key, search_terms in meme_mappings.items():
        if meme_key in lower_name:
            return search_terms

    # Default: split by spaces and return significant words
    words = clean_name.split()
    # Filter out common words
    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "meme",
    }
    significant_words = [w for w in words if w.lower() not in stop_words and len(w) > 2]

    return significant_words[:3] if significant_words else [clean_name]


async def _generate_single_meme(
    meme_concept: Dict[str, Any],
    tools: List[Any],
    llm: BaseChatModel,
) -> Optional[Dict[str, Any]]:
    """
    Generate a single meme using imgflip MCP tools.

    Args:
        meme_concept: Dict with meme_name_reference and text_to_add
        tools: List of MCP tools from imgflip server
        llm: Language model for the agent

    Returns:
        Dict with meme URL and metadata, or None if failed
    """
    meme_name = meme_concept.get("meme_name_reference", "")
    text_to_add = meme_concept.get("text_to_add", [])

    if not meme_name or not text_to_add:
        print("   ⚠️  Skipping meme with missing name or text")
        return None

    # Create agent with imgflip tools
    agent = create_react_agent(llm, tools)

    # Build the prompt for the agent
    text_boxes_str = "\n".join([f"- {text}" for text in text_to_add])

    prompt = f"""Create a meme based on the following:

Meme template to find: {meme_name}

Text boxes to use (in order):
{text_boxes_str}

Instructions:
1. First, search for the meme template using imgflip_search_memes with relevant keywords
2. Get the template info using imgflip_get_template_info to know how many text boxes it needs
3. Create the meme using imgflip_create_meme with the template_id and text_boxes array
4. Return the meme URL

Important: If the template requires fewer text boxes than provided, use only the first ones. If it requires more, you can leave extra boxes empty or combine the text appropriately.
"""

    try:
        response = await agent.ainvoke(
            {"messages": [{"role": "user", "content": prompt}]}
        )

        # Extract the meme URL from the response
        final_message = response.get("messages", [])[-1]
        content = (
            final_message.content
            if hasattr(final_message, "content")
            else str(final_message)
        )

        # Try to extract URL from the response
        url_match = re.search(
            r"https?://[^\s<>\"']+\.(?:jpg|jpeg|png|gif|webp)", content, re.IGNORECASE
        )

        if url_match:
            meme_url = url_match.group(0)
            print(f"   ✅ Generated meme: {meme_url}")
            return {
                "meme_name_reference": meme_name,
                "scene_name": meme_concept.get("scene_name"),
                "text_to_add": text_to_add,
                "meme_url": meme_url,
                "success": True,
            }
        else:
            # Check for imgflip URLs in different format
            url_match = re.search(r"https?://i\.imgflip\.com/[^\s<>\"']+", content)
            if url_match:
                meme_url = url_match.group(0)
                print(f"   ✅ Generated meme: {meme_url}")
                return {
                    "meme_name_reference": meme_name,
                    "scene_name": meme_concept.get("scene_name"),
                    "text_to_add": text_to_add,
                    "meme_url": meme_url,
                    "success": True,
                }

            print("   ⚠️  Could not extract meme URL from response")
            return {
                "meme_name_reference": meme_name,
                "scene_name": meme_concept.get("scene_name"),
                "text_to_add": text_to_add,
                "meme_url": None,
                "success": False,
                "error": "Could not extract URL from response",
                "raw_response": content[:500],
            }

    except Exception as e:
        print(f"   ❌ Failed to generate meme '{meme_name}': {e}")
        return {
            "meme_name_reference": meme_name,
            "scene_name": meme_concept.get("scene_name"),
            "text_to_add": text_to_add,
            "meme_url": None,
            "success": False,
            "error": str(e),
        }


async def _generate_memes_async(
    meme_concepts: List[Dict[str, Any]],
    llm: BaseChatModel,
) -> List[Dict[str, Any]]:
    """
    Generate memes asynchronously using imgflip MCP.

    Args:
        meme_concepts: List of meme concept dicts with meme_name_reference and text_to_add
        llm: Language model for the agent

    Returns:
        List of generated meme results
    """
    # Check for imgflip credentials
    imgflip_username = os.getenv("IMGFLIP_USERNAME")
    imgflip_password = os.getenv("IMGFLIP_PASSWORD")

    if not imgflip_username or not imgflip_password:
        print(
            "⚠️  IMGFLIP_USERNAME and IMGFLIP_PASSWORD environment variables are required"
        )
        return []

    # Get imgflip MCP path from environment or use uvx (published package)
    imgflip_mcp_dir = os.getenv("IMGFLIP_MCP_DIR")

    # Configure the MCP client for imgflip
    # Use uvx if no local directory is specified (published package approach)
    if imgflip_mcp_dir:
        mcp_config: Dict[str, Any] = {
            "imgflip": {
                "command": "uv",
                "args": [
                    "--directory",
                    imgflip_mcp_dir,
                    "run",
                    "imgflip-mcp",
                ],
                "transport": "stdio",
                "env": {
                    "IMGFLIP_USERNAME": imgflip_username,
                    "IMGFLIP_PASSWORD": imgflip_password,
                },
            }
        }
    else:
        print("IMGFlip MCP not found!")
        return []

    results: List[Dict[str, Any]] = []

    # Create client following shared MCP client pattern (no explicit session)
    client = MultiServerMCPClient(cast(Any, mcp_config))

    try:
        tools = await client.get_tools()
        if not tools:
            print("❌ No tools available from imgflip MCP server")
            return []

        print(f"🔧 Available imgflip tools: {[t.name for t in tools]}")

        # Generate memes sequentially to avoid rate limiting
        for i, meme_concept in enumerate(meme_concepts):
            print(
                f"\n🎨 Generating meme {i + 1}/{len(meme_concepts)}: "
                f"{meme_concept.get('meme_name_reference', 'Unknown')}"
            )

            result = await _generate_single_meme(meme_concept, tools, llm)
            if result:
                results.append(result)
    except Exception as e:
        print(f"❌ Error connecting to imgflip MCP server: {e}")
        print("   Make sure imgflip-mcp is installed: pip install imgflip-mcp")
        print("   Or set IMGFLIP_MCP_DIR to point to a local clone of the repo")
        return []

    return results


async def generate_meme_assets_node(
    state: Dict[str, Any], llm: BaseChatModel
) -> Dict[str, Any]:
    """
    Generate meme assets using imgflip MCP based on the asset plan.
    Only processes scenes where the asset type is 'meme'. Uses the asset's
    description as the meme concept (template search phrase) and as the text payload.
    """
    # Normalize asset_plan
    asset_plan = state.get("asset_plan", {})
    if hasattr(asset_plan, "model_dump"):
        asset_plan = asset_plan.model_dump()
    elif hasattr(asset_plan, "dict"):
        asset_plan = asset_plan.dict()

    if isinstance(asset_plan, dict):
        scenes = asset_plan.get("scenes", [])
    elif isinstance(asset_plan, list):
        scenes = asset_plan
    else:
        scenes = []

    if not scenes:
        print("⚠️  No scenes found in asset_plan")
        return {"generated_memes": []}

    # Build meme concepts from scene assets
    processed_concepts = []
    for scene in scenes:
        scene_name = scene.get("scene_name", "Unknown Scene")

        # Support both current and future schema names:
        # - current: 'video_assets' with {description, type}
        # - future:  'asset' with {description, type}
        asset_obj = scene.get("asset") or scene.get("video_assets")
        if not asset_obj:
            continue

        # Normalize potential Pydantic object into dict
        if hasattr(asset_obj, "model_dump"):
            asset_obj = asset_obj.model_dump()
        elif hasattr(asset_obj, "dict"):
            asset_obj = asset_obj.dict()

        asset_type = str(asset_obj.get("type", "")).lower()
        description = asset_obj.get("description", "")

        if asset_type != "meme":
            continue
        if not description:
            print(f"⚠️  Skipping meme generation for '{scene_name}' (no description)")
            continue

        # Minimal, robust concept: use description for both template search and text payload
        processed_concepts.append(
            {
                "scene_name": scene_name,
                "meme_name_reference": description,  # agent will search with relevant keywords
                "text_to_add": [description],  # agent can trim/fit into boxes
            }
        )

    if not processed_concepts:
        print("⚠️  No meme-type assets found in asset_plan")
        return {"generated_memes": []}

    print(f"\n🖼️  Generating {len(processed_concepts)} meme(s) using imgflip MCP...")

    # Run the async meme generation (no new event loop to avoid lock binding issues)
    results = await _generate_memes_async(processed_concepts, llm)

    # Summary
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]

    print("\n📊 Meme generation summary:")
    print(f"   ✅ Successful: {len(successful)}")
    print(f"   ❌ Failed: {len(failed)}")

    if successful:
        print("\n🖼️  Generated meme URLs:")
        for meme in successful:
            label = (
                meme.get("meme_name_reference") or meme.get("scene_name") or "unknown"
            )
            print(f"   - {label}: {meme.get('meme_url')}")

    return {"generated_memes": results}
