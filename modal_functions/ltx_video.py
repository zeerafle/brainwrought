import time
from pathlib import Path

import modal

app = modal.App("brainwrought-ltx")

# Container image with dependencies
image = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install(
        "accelerate==1.6.0",
        "diffusers==0.33.1",
        "huggingface-hub==0.36.0",
        "imageio==2.37.0",
        "imageio-ffmpeg==0.5.1",
        "sentencepiece==0.2.0",
        "torch==2.7.0",
        "transformers==4.51.3",
    )
    .env({"HF_XET_HIGH_PERFORMANCE": "1"})
)

# Volumes for model weights and outputs
MODEL_VOLUME_NAME = "ltx-model"
OUTPUTS_VOLUME_NAME = "ltx-outputs"
model_vol = modal.Volume.from_name(MODEL_VOLUME_NAME, create_if_missing=True)
outputs_vol = modal.Volume.from_name(OUTPUTS_VOLUME_NAME, create_if_missing=True)

MODEL_PATH = Path("/models")
OUTPUTS_PATH = Path("/outputs")

image = image.env({"HF_HOME": str(MODEL_PATH)})

MINUTES = 60  # seconds


@app.cls(
    image=image,
    volumes={OUTPUTS_PATH: outputs_vol, MODEL_PATH: model_vol},
    gpu="H100",
    timeout=10 * MINUTES,
    scaledown_window=15 * MINUTES,
)
class LTXVideo:
    @modal.enter()
    def load_model(self):
        import torch  # pyright: ignore[reportMissingImports]
        from diffusers import DiffusionPipeline  # pyright: ignore[reportMissingImports]

        self.pipe = DiffusionPipeline.from_pretrained(
            "Lightricks/LTX-Video", torch_dtype=torch.bfloat16
        )

        self.pipe.to("cuda")
        _vae = getattr(self.pipe, "vae", None)
        (_vae and hasattr(_vae, "enable_tiling") and _vae.enable_tiling())

    @modal.method()
    def generate(
        self,
        prompt: str,
        session_id: str = "default",
        negative_prompt: str = "worst quality, inconsistent motion, blurry, jittery, distorted, artifacts",
        num_inference_steps: int = 30,
        guidance_scale: float = 3.5,
        num_frames: int = 97,
        width: int = 704,
        height: int = 480,
        fps: int = 24,
        seed: int | None = None,
    ) -> str:
        """Generate video from text prompt and return the video file path."""
        from diffusers.utils import (  # pyright: ignore[reportMissingImports]
            export_to_video,
        )

        # Using preloaded pipeline (best public dev model or umbrella fallback loaded at startup)

        # Using caller-provided or default steps/guidance

        adjusted_width = max(32, width - (width % 32))
        adjusted_height = max(32, height - (height % 32))
        adjusted_frames = max(9, ((num_frames - 1) // 8) * 8 + 1)
        import torch as _torch

        _gen = (
            _torch.Generator(device="cuda").manual_seed(seed)
            if seed is not None
            else None
        )
        frames = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            num_frames=adjusted_frames,
            width=adjusted_width,
            height=adjusted_height,
            generator=_gen,
        ).frames[0]

        # Save to Modal Volume
        filename = f"{int(time.time())}_{prompt[:50].replace(' ', '_')}.mp4"

        if session_id != "default":
            # Create session directory structure: sessions/<id>/video/
            session_dir = OUTPUTS_PATH / "sessions" / session_id / "video"
            session_dir.mkdir(parents=True, exist_ok=True)
            video_path = session_dir / filename
            # Return relative path for Remotion (vol/sessions/<id>/video/<filename>)
            # Note: Remotion mounts the volume at public/vol, so we return path relative to volume root
            relative_path = f"sessions/{session_id}/video/{filename}"
        else:
            video_path = OUTPUTS_PATH / filename
            relative_path = filename

        export_to_video(frames, video_path, fps=fps)
        outputs_vol.commit()

        return relative_path
