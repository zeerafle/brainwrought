#!/usr/bin/env python3
"""
Hugging Face Space entrypoint for the Brainwrought Gradio app.

README hints:
- Set "App File" in Space settings to brainwrought/src/app_space.py
- Add a Space Secret named HF_TOKEN if you want to upload outputs to a Dataset repo
- Optionally set a public variable HF_DATASET_REPO (e.g., your-username/brainrot-results) to store outputs
- Consider requesting upgraded hardware and a safe sleep time (e.g., 2h) to avoid mid-job sleep:
    from huggingface_hub import HfApi, SpaceHardware
    api = HfApi()
    api.request_space_hardware(repo_id="OWNER/SPACE", hardware=SpaceHardware.T4_MEDIUM, sleep_time=7200)
- This entrypoint runs the job-queue UI and background worker. Results are persisted to Space storage and optionally uploaded to a Dataset for stable download URLs.

User flow:
1) Submit PDF → get Job ID and a bookmarkable link with the job_id query param
2) Return later to the Retrieve tab and paste Job ID (or use the bookmark link)
3) Auto-polling updates status and provides output link when ready
"""

import asyncio
import json
import os
import shutil
import time
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Optional

import gradio as gr
from huggingface_hub import HfApi

# Import pipeline
from app import (
    run_pipeline,  # relies on src layout; this file should live next to app.py
)

# ----------------------------
# Config and persistence
# ----------------------------
DATA_DIR = Path("./data")  # In Space storage if storage is enabled
JOBS_DIR = DATA_DIR / "jobs"
OUTPUTS_DIR = DATA_DIR / "outputs"
INPUTS_DIR = DATA_DIR / "inputs"
for d in (JOBS_DIR, OUTPUTS_DIR, INPUTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Optional: upload results to this Dataset repo (set via Space variable or hardcode)
HF_DATASET_REPO = "zeerafle/brainwrought-data"
api = HfApi()


# ----------------------------
# Job store helpers
# ----------------------------
def job_path(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.json"


def read_job(job_id: str) -> Optional[Dict]:
    p = job_path(job_id)
    if not p.exists():
        return None
    return json.loads(p.read_text())


def write_job(job: Dict) -> None:
    job_path(job["job_id"]).write_text(json.dumps(job, indent=2))


def create_job(input_meta: Dict) -> Dict:
    job_id = uuid.uuid4().hex
    job = {
        "job_id": job_id,
        "status": "PENDING",  # PENDING | RUNNING | COMPLETED | FAILED | INTERRUPTED
        "created_at": time.time(),
        "updated_at": time.time(),
        "input_meta": input_meta,
        "progress": 0.0,
        "logs": [],
        "output_local_path": None,
        "output_hf_url": None,
        "error": None,
    }
    write_job(job)
    return job


def update_job(job_id: str, **kwargs):
    job = read_job(job_id)
    if not job:
        return
    job.update(kwargs)
    job["updated_at"] = time.time()
    write_job(job)


def append_log(job_id: str, msg: str):
    job = read_job(job_id)
    if not job:
        return
    job["logs"].append(f"[{time.strftime('%H:%M:%S')}] {msg}")
    job["updated_at"] = time.time()
    write_job(job)


def recover_incomplete_jobs():
    # Mark any RUNNING jobs as INTERRUPTED on startup
    for jf in JOBS_DIR.glob("*.json"):
        try:
            job = json.loads(jf.read_text())
            if job.get("status") == "RUNNING":
                job["status"] = "INTERRUPTED"
                job["logs"] = job.get("logs", []) + [
                    "[startup] Marked as INTERRUPTED after Space restart."
                ]
                job["updated_at"] = time.time()
                jf.write_text(json.dumps(job, indent=2))
        except Exception:
            continue


recover_incomplete_jobs()


# ----------------------------
# Long-running pipeline wrapper
# ----------------------------
def pdf_to_brainrot(pdf_path: str, out_dir: Path, progress_cb=None) -> Path:
    # Execute the real pipeline with a unique thread_id so checkpointing is isolated
    out_dir.mkdir(parents=True, exist_ok=True)
    if progress_cb:
        progress_cb(0.01)

    thread_id = uuid.uuid4().hex
    result = asyncio.run(run_pipeline(pdf_path, thread_id=thread_id))

    # Extract produced video path from pipeline result
    video_path = None
    if isinstance(result, dict):
        vt = result.get("video_timeline", {})
        if isinstance(vt, dict):
            candidate = vt.get("video_path") or vt.get("path") or vt.get("output")
            if candidate:
                candidate_path = Path(candidate)
                if candidate_path.exists():
                    video_path = candidate_path

    if video_path is None:
        raise RuntimeError("Pipeline did not produce a video file.")

    dest_path = out_dir / "video.mp4"
    shutil.copy2(video_path, dest_path)

    if progress_cb:
        progress_cb(1.0)

    return dest_path


# ----------------------------
# Background worker
# ----------------------------
executor = ThreadPoolExecutor(max_workers=1)


def run_job(job_id: str):
    job = read_job(job_id)
    if not job:
        return
    try:
        update_job(job_id, status="RUNNING", progress=0.0)
        append_log(job_id, "Starting processing...")

        input_pdf = job["input_meta"]["pdf_path"]
        out_dir = OUTPUTS_DIR / job_id

        def on_progress(p):
            update_job(job_id, progress=float(p))

        video_path = pdf_to_brainrot(input_pdf, out_dir, progress_cb=on_progress)
        append_log(job_id, "Processing finished. Preparing artifact...")

        # Upload to HF Dataset for stable URL (optional)
        hf_url = None
        if HF_DATASET_REPO:
            path_in_repo = f"videos/{job_id}/video.mp4"
            try:
                api.upload_file(
                    path_or_fileobj=str(video_path),
                    path_in_repo=path_in_repo,
                    repo_id=HF_DATASET_REPO,
                    repo_type="dataset",
                )
                hf_url = f"https://huggingface.co/datasets/{HF_DATASET_REPO}/resolve/main/{path_in_repo}"
            except Exception as ue:
                append_log(job_id, f"Upload to dataset failed: {ue}")
                hf_url = None

        update_job(
            job_id,
            status="COMPLETED",
            output_local_path=str(video_path),
            output_hf_url=hf_url,
            progress=1.0,
        )
        append_log(job_id, "Job completed successfully.")
    except Exception as e:
        append_log(job_id, f"Error: {e}")
        append_log(job_id, traceback.format_exc())
        update_job(job_id, status="FAILED", error=str(e))


def enqueue_job(job_id: str):
    executor.submit(run_job, job_id)


# ----------------------------
# Gradio UI callbacks
# ----------------------------
def submit_job(pdf_file: gr.File):
    if pdf_file is None:
        return gr.update(), "Please upload a PDF.", ""

    # Persist input
    stored_pdf_dir = INPUTS_DIR / uuid.uuid4().hex
    stored_pdf_dir.mkdir(parents=True, exist_ok=True)
    stored_pdf_path = stored_pdf_dir / "input.pdf"
    # Resolve gradio file to a path and copy to avoid cross-device issues
    src_path = None
    if isinstance(pdf_file, dict):
        src_path = (
            pdf_file.get("name") or pdf_file.get("path") or pdf_file.get("orig_name")
        )
    elif isinstance(pdf_file, (str, Path)):
        src_path = str(pdf_file)
    elif isinstance(pdf_file, list) and pdf_file:
        item = pdf_file[0]
        if isinstance(item, dict):
            src_path = item.get("name") or item.get("path") or item.get("orig_name")
        else:
            src_path = str(item)

    if not src_path or not os.path.exists(src_path):
        return gr.update(), "Invalid upload. Please re-upload your PDF.", ""

    try:
        shutil.copy2(src_path, str(stored_pdf_path))
        # Best-effort cleanup of gradio temp file if applicable
        try:
            if str(src_path).startswith("/tmp/gradio") and os.path.exists(src_path):
                os.remove(src_path)
        except Exception:
            pass
    except Exception:
        # Fallback: byte-wise copy
        with open(src_path, "rb") as rf, open(stored_pdf_path, "wb") as wf:
            wf.write(rf.read())

    job = create_job({"pdf_path": str(stored_pdf_path)})
    enqueue_job(job["job_id"])

    # Return a relative link with query param so the bookmark works regardless of Space URL
    return (
        job["job_id"],
        "Job submitted. Save your Job ID or bookmark the link below.",
        f"?job_id={job['job_id']}",
    )


def check_status(job_id: str):
    job = read_job(job_id)
    if not job:
        return "NOT_FOUND", 0.0, [], None, None
    return (
        job["status"],
        float(job.get("progress", 0.0)),
        job.get("logs", []),
        job.get("output_hf_url", None),
        job.get("output_local_path", None),
    )


def prefill_job_id(request: gr.Request):
    try:
        qp = getattr(request, "query_params", {}) or {}
        return qp.get("job_id", "")
    except Exception:
        return ""


# ----------------------------
# Build Gradio UI
# ----------------------------
with gr.Blocks(title="Brainwrought | Food for your brain") as demo:
    gr.Markdown("# 🧠 Brainwrought ")
    gr.Markdown(
        "Put your boring pdf lecture here, and consume brainwrought instead\n"
        "- After submitting, copy the Job ID or bookmark the link.\n"
        "- Come back later and use the Retrieve tab to check status.\n"
    )

    with gr.Tab("Submit"):
        pdf = gr.File(label="Upload PDF", file_types=[".pdf"])
        submit_btn = gr.Button("Start")
        job_id_out = gr.Textbox(label="Job ID", interactive=False)
        status_text = gr.Markdown()
        return_link = gr.Textbox(label="Return Link", interactive=False)

        submit_btn.click(
            fn=submit_job,
            inputs=[pdf],
            outputs=[job_id_out, status_text, return_link],
        )

    with gr.Tab("Retrieve"):
        job_id_in = gr.Textbox(label="Paste your Job ID")
        with gr.Row():
            refresh = gr.Button("Check status")
            progress = gr.Slider(
                label="Progress", minimum=0, maximum=1, interactive=False
            )
        status = gr.Textbox(label="Status", interactive=False)
        logs = gr.JSON(label="Logs")
        video_url = gr.Textbox(label="Download URL (HF Dataset)", interactive=False)
        local_path = gr.Textbox(label="Local path (Space storage)", interactive=False)

        refresh.click(
            fn=check_status,
            inputs=[job_id_in],
            outputs=[status, progress, logs, video_url, local_path],
            queue=True,
        )

        # Auto-poll while the Retrieve tab is open
        poller = gr.Timer(5.0)
        poller.tick(
            fn=check_status,
            inputs=[job_id_in],
            outputs=[status, progress, logs, video_url, local_path],
        )

    # Autofill job_id from query params when the app loads
    demo.load(
        fn=prefill_job_id,
        inputs=None,
        outputs=[job_id_in],
    )

# Expose app for frameworks that auto-discover 'app'
demo.queue(max_size=20, default_concurrency_limit=2)
app = demo

if __name__ == "__main__":
    # Enable queue with conservative concurrency (heavy work is in the background executor)
    demo.queue(max_size=20, default_concurrency_limit=2)
    # Respect HF Spaces port env; bind to all interfaces
    port = int(os.getenv("PORT", "7860"))
    demo.launch(server_name="0.0.0.0", server_port=port)
