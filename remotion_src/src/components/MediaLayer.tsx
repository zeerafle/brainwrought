import React from 'react';
import { AbsoluteFill, Video, Img, staticFile } from 'remotion';

export const MediaLayer: React.FC<{
  assetPath: string | null;
  type: 'video' | 'image';
}> = ({ assetPath, type }) => {
  if (!assetPath) {
    // If no asset path is provided, render nothing (transparent)
    // The background layer in SceneManager will show through
    return null;
  }

  // Assuming assets are served from a static folder or URL
  // For Modal, we might need to handle paths differently (e.g. signed URLs or mounted volume paths served via staticFile)
  // For now, we assume local paths or URLs.

  // Handle potential missing leading slash or volume prefix issues if needed
  // But staticFile usually handles relative paths from public/
  const src = assetPath.startsWith('http') ? assetPath : staticFile(assetPath);

  const onError = (e: any) => {
      console.error(`❌ Failed to load media: ${src}`, e);
  }

  if (type === 'video') {
    return (
      <AbsoluteFill>
        <Video
            src={src}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            onError={onError}
        />
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill>
      <Img
        src={src}
        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        onError={onError}
      />
    </AbsoluteFill>
  );
};
