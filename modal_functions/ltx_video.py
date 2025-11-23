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

    @modal.method()
    def generate(
        self,
        prompt: str,
        negative_prompt: str = "worst quality, blurry, jittery, distorted",
        num_inference_steps: int = 100,
        guidance_scale: float = 4.5,
        num_frames: int = 150,
        width: int = 704,
        height: int = 480,
    ) -> str:
        """Generate video from text prompt and return the video file path."""
        from diffusers.utils import (  # pyright: ignore[reportMissingImports]
            export_to_video,
        )

        frames = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            num_frames=num_frames,
            width=width,
            height=height,
        ).frames[0]

        # Save to Modal Volume
        video_filename = f"{int(time.time())}_{prompt[:50].replace(' ', '_')}.mp4"
        video_path = OUTPUTS_PATH / video_filename
        export_to_video(frames, video_path)
        outputs_vol.commit()

        return video_filename
