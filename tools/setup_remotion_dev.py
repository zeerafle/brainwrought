import json
import os
from pathlib import Path
import shutil

def setup_dev():
    """
    Sets up the local Remotion environment by symlinking assets
    to match the 'vol/' structure expected by the code.
    """
    print("🔧 Setting up Remotion local development environment...")

    # 1. Check for props file
    props_path = Path("remotion_src/input_props.json")
    if not props_path.exists():
        print("❌ remotion_src/input_props.json not found.")
        print("   👉 Run the pipeline once (with TEST_SESSION_ID) to generate it.")
        return

    try:
        with open(props_path) as f:
            props = json.load(f)
    except Exception as e:
        print(f"❌ Error reading props file: {e}")
        return

    # 2. Extract Session ID to link correct audio
    session_id = None
    # Try to find session_id in voice_timing paths
    # Path format: vol/sessions/<uuid>/audio/...
    if props.get("voice_timing"):
        for timing in props["voice_timing"]:
            path = timing.get("audio_path", "")
            parts = path.split("/")
            if "sessions" in parts:
                idx = parts.index("sessions")
                if idx + 1 < len(parts):
                    session_id = parts[idx+1]
                    break

    if not session_id:
        print("⚠️ Could not determine session_id from input_props.json.")
        print("   Audio assets might not link correctly.")
    else:
        print(f"   🎯 Detected Session ID: {session_id}")

    # 3. Create public/vol structure
    vol_path = Path("remotion_src/public/vol")
    if vol_path.exists():
        # Clean up old symlinks/dirs to ensure freshness
        shutil.rmtree(vol_path)

    vol_path.mkdir(parents=True, exist_ok=True)

    # 4. Symlink Stock Assets
    # Maps assets/stock -> remotion_src/public/vol/stock
    stock_source = Path("assets/stock").absolute()
    stock_target = vol_path / "stock"

    if stock_source.exists():
        os.symlink(stock_source, stock_target)
        print("   ✅ Linked stock assets")
    else:
        print(f"   ⚠️ Stock assets not found at {stock_source}")

    # 5. Symlink Audio Assets
    # Maps generated_audio -> remotion_src/public/vol/sessions/<id>/audio
    if session_id:
        audio_source = Path("generated_audio").absolute()
        session_audio_dir = vol_path / "sessions" / session_id / "audio"

        session_audio_dir.parent.mkdir(parents=True, exist_ok=True)

        if audio_source.exists():
            os.symlink(audio_source, session_audio_dir)
            print("   ✅ Linked audio assets")
        else:
            print(f"   ⚠️ Generated audio not found at {audio_source}")

    print("\n🎉 Environment ready!")
    print("   Run the following commands to start the studio:")
    print("   cd remotion_src")
    print("   npm install")
    print("   npm start -- --props=input_props.json")

if __name__ == "__main__":
    setup_dev()
