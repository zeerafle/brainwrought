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

# 2.5 Fix permissions for node user
# Ensure the node user (uid 1000) owns the directory
RUN chown -R node:node /app

# Switch to node user
USER node

# 3. Copy package files first to leverage Docker cache
COPY --chown=node:node package.json pnpm-lock.yaml* ./

# 4. Install dependencies
# We use --legacy-peer-deps to handle the zod conflict you saw earlier
RUN npm install --legacy-peer-deps

# 5. Copy the rest of the source code
COPY --chown=node:node . .

# 6. Expose port for Remotion Studio
EXPOSE 3000

# 7. Default command (can be overridden)
CMD ["npm", "start"]
