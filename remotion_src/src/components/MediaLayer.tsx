import React from 'react';
import { AbsoluteFill, Video, Img, staticFile } from 'remotion';

export const MediaLayer: React.FC<{
  assetPath: string | null;
  type: 'video' | 'image';
}> = ({ assetPath, type }) => {
  if (!assetPath) {
    // Fallback to generic background if no asset provided
    // Use a stock gameplay video from the volume if available
    const fallbackSrc = staticFile("vol/stock/gameplay/minecraft.mp4");

    return (
      <AbsoluteFill>
         <Video src={fallbackSrc} style={{ width: '100%', height: '100%', objectFit: 'cover' }} loop />
      </AbsoluteFill>
    );
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
