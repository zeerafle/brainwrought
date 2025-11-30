import json
from pathlib import Path
import modal

# Load props (adjust path if needed)
props_path = Path("remotion_src/input_props.json")
props = json.loads(props_path.read_text())

# Get the deployed class and call the remote method
RemotionRenderer = modal.Cls.from_name("brainwrought-renderer", "RemotionRenderer")
renderer = RemotionRenderer()

print("⏳ Invoking remote renderer...")
video_bytes = renderer.render_video.remote(props)

out_dir = Path("rendered_videos")
out_dir.mkdir(exist_ok=True)
out_path = out_dir / "final_video_from_remote.mp4"

with open(out_path, "wb") as f:
    f.write(video_bytes)

print(f"✅ Saved remote-rendered video to: {out_path}")
