# Brainwrought 🧠⚙️

Convert PDFs into brainrot-style short videos through an agentic pipeline. This repo ships a Gradio UI designed for Hugging Face Spaces with background jobs, job IDs, and safe retrieval so users can come back later for their video.

## How it works (background jobs)

- Submit:
  - User uploads a PDF and clicks Start.
  - The app generates a job_id and immediately returns it plus a bookmarkable link like `?job_id=<id>`.
  - The long-running pipeline runs in a background worker (no blocking the UI).
- Processing:
  - Progress and logs are written to Space storage under `./data/jobs/<job_id>.json`.
  - The final video is stored under `./data/outputs/<job_id>/video.mp4`.
  - Optionally, the video is uploaded to a Hugging Face Dataset repo for a stable CDN-backed URL.
- Retrieve:
  - Users can return anytime to the Retrieve tab, paste their `job_id`, or open the bookmarked link that pre-fills it.
  - A small timer auto-polls status every few seconds until the job is completed.

## Deploying to Hugging Face Spaces

1) Create a new Space using the “Gradio” SDK.

2) App File:
   - Set App File to: `brainwrought/src/app_space.py`

3) Python dependencies:
   - The project uses `pyproject.toml`. If your Space build doesn’t install from it automatically, add a `requirements.txt` mirroring the dependencies in `pyproject.toml`.

4) Space storage:
   - Enable Space storage (small/medium/large) so job metadata and outputs persist across restarts.

5) Environment:
   - Add a Space Secret named `HF_TOKEN` if you want to upload results to a Dataset repo.
   - Add a Space Variable `HF_DATASET_REPO` set to your dataset repo (e.g., `your-username/brainrot-results`) to enable result uploads and stable HTTPS links.

6) Hardware and sleep:
   - For long jobs (~30 minutes), consider upgraded hardware and a sleep window that won’t interrupt running jobs.
   - On upgraded hardware, you can set sleep_time via API. Example:

```python
from huggingface_hub import HfApi, SpaceHardware

api = HfApi()
api.request_space_hardware(
    repo_id="OWNER/SPACE",             # replace with your Space id
    hardware=SpaceHardware.T4_MEDIUM,  # or CPU_UPGRADE, etc.
    sleep_time=7200,                   # 2 hours in seconds
)
```

   - On free `cpu-basic`, the sleep policy is fixed by the platform.

7) Run:
   - On Spaces, the UI launches automatically.
   - Concurrency is kept small at the UI layer; the heavy pipeline runs in a single background worker to protect memory.

## Using the app

- Submit tab:
  - Upload a PDF and click Start.
  - Copy your Job ID or use the provided return link (`?job_id=<id>`).
- Retrieve tab:
  - Paste your Job ID (or open the bookmarked return link).
  - Status, progress, and logs will update automatically.
  - When complete, you’ll see either:
    - A stable Dataset URL if `HF_DATASET_REPO` is configured, and/or
    - The local Space storage path where the video was saved.

## Storage layout

- Jobs: `./data/jobs/<job_id>.json`
- Inputs: `./data/inputs/<random_id>/input.pdf`
- Outputs: `./data/outputs/<job_id>/video.mp4`
- Optional upload target (if configured): `https://huggingface.co/datasets/<HF_DATASET_REPO>/resolve/main/videos/<job_id>/video.mp4`

## Environment configuration

Set only what you use:

- Hugging Face:
  - `HF_TOKEN` (Secret) — required to upload to a private Dataset repo or modify Space hardware/sleep via API.
  - `HF_DATASET_REPO` (Variable) — optional; enables stable CDN-backed output links.
- LLMs / media (optional, if your pipeline uses them):
  - `OPENAI_API_KEY`
  - `GOOGLE_API_KEY` (for Gemini/Vertex via LangChain integrations)
  - `ELEVENLABS_API_KEY` (if using ElevenLabs TTS)
  - Modal or other render providers — configure per provider’s docs if you use remote rendering in your pipeline.

## Local development

- Install:
  - Python 3.12+
  - From repo root: `pip install -e .` (or your preferred environment manager)
- Run the Gradio app locally:
  - `python brainwrought/src/app_space.py`
- Open http://127.0.0.1:7860 and follow the same flow (Submit, then Retrieve).

## Troubleshooting

- Long jobs stop midway:
  - Ensure your Space doesn’t sleep during jobs. On upgraded hardware, set `sleep_time` high enough (e.g., 7200 seconds).
- Space restarted while job was running:
  - Jobs marked RUNNING at shutdown are set to INTERRUPTED at next startup. Resubmit or requeue as needed.
- No video produced:
  - Check `./data/jobs/<job_id>.json` logs for errors.
  - Verify your model/provider keys are set and accessible in the Space environment.
- Upload to Dataset repo fails:
  - Ensure `HF_TOKEN` has write access to the specified `HF_DATASET_REPO`.
