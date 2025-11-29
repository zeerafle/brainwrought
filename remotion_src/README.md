To set up a local container for Remotion using Podman, we need to replicate the environment we defined for Modal (Node.js + Chromium dependencies + FFmpeg) in a standard `Dockerfile`.

Here is the complete setup.

### 1. Create the Dockerfile

Create a file named `Dockerfile` inside your remotion_src folder. This image installs all the necessary system libraries for the headless browser and FFmpeg.

```dockerfile
FROM node:22-bookworm-slim

# 1. Install system dependencies required for Chromium and FFmpeg
# These match exactly what we used in the Modal definition
RUN apt-get update && apt-get install -y \
    libnss3 \
    libdbus-1-3 \
    libatk1.0-0 \
    libgbm-dev \
    libasound2 \
    libxrandr2 \
    libxkbcommon-dev \
    libxfixes3 \
    libxcomposite1 \
    libxdamage1 \
    libatk-bridge2.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    libcups2 \
    chromium \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# 2. Set working directory
WORKDIR /app

# 3. Copy package files first to leverage Docker cache
COPY package.json pnpm-lock.yaml* ./

# 4. Install dependencies
# We use --legacy-peer-deps to handle the zod conflict you saw earlier
RUN npm install --legacy-peer-deps

# 5. Copy the rest of the source code
COPY . .

# 6. Expose port for Remotion Studio
EXPOSE 3000

# 7. Default command (can be overridden)
CMD ["npm", "start"]
```

### 2. Build the Image

Run this command from your terminal inside the remotion_src directory:

```bash
cd remotion_src
podman build -t brainwrought-remotion .
```

### 3. Run Remotion Studio (Preview)

To run the visual editor locally using Podman, use the following command.

*   `-p 3000:3000`: Maps the container port to your localhost.
*   `-v $(pwd):/app`: Mounts your current folder into the container so changes you make locally update live.
*   `--userns=keep-id`: **Crucial for Podman on Linux.** It maps your local user ID to the container user, ensuring you have permission to edit files and that generated files aren't owned by `root`.

```bash
podman run -it --rm \
  --userns=keep-id \
  -p 3000:3000 \
  -v $(pwd):/app \
  brainwrought-remotion \
  npm start -- --props=input_props.json
```

Open `http://localhost:3000` in your browser.

### 4. Run Remotion Render (Generate Video)

To render the video to a file (e.g., `out/video.mp4`):

```bash
podman run -it --rm \
  --userns=keep-id \
  -v $(pwd):/app \
  brainwrought-remotion \
  npx remotion render BrainrotComposition out/video.mp4 --props=input_props.json
```

### Troubleshooting Tips

*   **Permissions**: If you see "Permission denied" errors, ensure you are using `--userns=keep-id`.
*   **Missing Assets**: Ensure you have run `uv run tools/setup_remotion_dev.py` (from the previous step) before running the container. This ensures the `public/vol` symlinks exist so the container can see your audio/video assets.
*   **SELinux**: If you are on Fedora/RHEL/CentOS and have issues accessing files, append `:Z` to the volume mount: `-v $(pwd):/app:Z`.
