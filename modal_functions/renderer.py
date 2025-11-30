import json
import os
import subprocess
from pathlib import Path

import modal

app = modal.App("brainwrought-renderer")

# Mount the Remotion project
remotion_src_path = Path(__file__).parent.parent / "remotion_src"
remote_remotion_path = "/app/remotion_src"

# Define the image with Node.js and Chrome dependencies
image = (
    modal.Image.from_registry("node:22-bookworm-slim", add_python="3.12")
    .apt_install(
        "libnss3",
        "libdbus-1-3",
        "libatk1.0-0",
        "libgbm-dev",
        "libasound2",
        "libxrandr2",
        "libxkbcommon-dev",
        "libxfixes3",
        "libxcomposite1",
        "libxdamage1",
        "libatk-bridge2.0-0",
        "libpango-1.0-0",
        "libcairo2",
        "libcups2",
        "chromium",
        "ffmpeg",
        "git",
    )
    .run_commands("npm install -g pnpm")
    # Install dependencies: Copy package.json first to cache the npm install step
    .add_local_file(
        remotion_src_path / "package.json", remote_path="/tmp/package.json", copy=True
    )
    .run_commands(
        "cd /tmp && npm install --legacy-peer-deps",
        "mkdir -p /app/remotion_src",
        "cp -r /tmp/node_modules /app/",
    )
    .add_local_dir(
        remotion_src_path,
        remote_path=remote_remotion_path,
        ignore=["node_modules", ".remotion", "out", ".git", "public/vol"],
    )
)

# Volume for assets (shared with LTX generator)
ASSETS_VOLUME_NAME = "ltx-outputs"
assets_vol = modal.Volume.from_name(ASSETS_VOLUME_NAME, create_if_missing=True)

# Mount to public/vol so it's accessible via staticFile("vol/...")
# Remotion's public folder is at /app/remotion_src/public
ASSETS_PATH = "/app/remotion_src/public/vol"


@app.cls(
    image=image,
    volumes={ASSETS_PATH: assets_vol},
    timeout=1800,  # 30 mins
    cpu=8,
    memory=4096,
)
class RemotionRenderer:
    @modal.enter()
    def install_dependencies(self):
        # Install dependencies if node_modules is missing or check if needed
        # Since the mount is read-only for code but we might need to write to node_modules?
        # Modal mounts are read-only by default? No, from_local_dir is.
        # We should probably install dependencies in the build step (image definition) if possible,
        # but package.json is in the local dir.
        # Better strategy: Copy package.json in image build and install there.
        pass

    @modal.method()
    def render_video(self, props: dict) -> bytes:
        # We need to ensure dependencies are installed.
        # Since we mounted the source code, we might need to run npm install once.
        # But mounts are read-only?
        # Let's try running npm install in a writable directory or assume we can write.
        # Actually, standard practice is to install deps in the image.
        # But our package.json is local.
        # Let's run npm install in the container at runtime for now (slow but works)
        # or use a persistent volume for node_modules.

        os.chdir(remote_remotion_path)

        # Check if node_modules exists, if not install
        # Note: We installed deps in the image build step to /app/node_modules
        # Since we are in /app/remotion_src, node will look up to /app/node_modules
        # So we might not need to install here if everything is correct.
        # However, if we need to install devDependencies or if something is missing:
        if not os.path.exists("node_modules") and not os.path.exists("../node_modules"):
            print("📦 Installing dependencies...")
            subprocess.run(["npm", "install", "--legacy-peer-deps"], check=True)

        # Write props to file
        props_file = "input_props.json"
        with open(props_file, "w") as f:
            json.dump(props, f)

        output_file = "out/video.mp4"
        os.makedirs("out", exist_ok=True)

        print("🎬 Starting render...")
        # npx remotion render BrainrotComposition out/video.mp4 --props=input_props.json
        cmd = [
            "npx",
            "remotion",
            "render",
            "BrainrotComposition",
            output_file,
            f"--props={props_file}",
            "--gl=angle",  # Often needed in headless envs
            "--concurrency=80%",
        ]

        subprocess.run(cmd, check=True)

        print("✅ Render complete!")

        with open(output_file, "rb") as f:
            video_bytes = f.read()

        return video_bytes


@app.local_entrypoint()
def main():
    print("🧪 Testing renderer...")
    renderer = RemotionRenderer()
    # Dummy props
    props = {"scenes": [], "asset_plan": [], "voice_timing": [], "total_duration": 10}
    try:
        video_bytes = renderer.render_video.remote(props)
        print(f"✅ Render successful! Got {len(video_bytes)} bytes.")
    except Exception as e:
        print(f"❌ Render failed: {e}")
