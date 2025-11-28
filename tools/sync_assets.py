import modal
import os
from pathlib import Path

app = modal.App("brainwrought-asset-syncer")
vol = modal.Volume.from_name("ltx-outputs", create_if_missing=True)

@app.local_entrypoint()
def upload_stock_assets():
    # Local path to assets
    local_assets_path = Path(__file__).parent.parent / "assets"

    if not local_assets_path.exists():
        print(f"❌ Assets directory not found at {local_assets_path}")
        return

    print(f"📂 Syncing {local_assets_path} to Volume...")

    # Walk through the directory
    for root, _, files in os.walk(local_assets_path):
        for file in files:
            local_file = Path(root) / file
            # Calculate relative path for the volume (e.g., stock/gameplay/minecraft.mp4)
            rel_path = local_file.relative_to(local_assets_path)
            remote_path = str(rel_path) # This will be at the root of the volume?
            # No, let's put it under 'stock' if it's not already.
            # If local structure is assets/stock/gameplay, rel_path is stock/gameplay/...

            print(f"   ⬆️  Uploading {rel_path}...")
            with open(local_file, "rb") as f:
                # modal.Volume.write_file takes bytes
                # But wait, write_file is not a method on Volume in recent versions?
                # It's usually handled via mounts or batch_upload.
                # Let's use batch_upload for efficiency if possible, or simple put/write.
                # Checking docs... Volume has no write_file?
                # It has .commit() but how to write?
                # Ah, we can use a Function to write to the volume.
                pass

    # Better approach: Use a remote function to write files
    # Or use `modal volume put` CLI command.
    # But let's do it programmatically via a Function that mounts the volume.

    # Actually, the best way to upload local files to a Volume is via `vol.batch_upload()` context manager
    # if running locally.

    with vol.batch_upload() as batch:
        for root, _, files in os.walk(local_assets_path):
            for file in files:
                local_file = Path(root) / file
                rel_path = local_file.relative_to(local_assets_path)
                # Ensure we use forward slashes
                remote_path = str(rel_path).replace(os.sep, "/")

                print(f"   queueing {remote_path}")
                batch.put_file(local_file, remote_path)

    print("✅ Sync complete!")
