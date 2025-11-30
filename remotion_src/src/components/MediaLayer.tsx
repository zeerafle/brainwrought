import React, {useRef, useState} from 'react';
import { AbsoluteFill, Video, Img, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';

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

  // Center content and make it slightly smaller than full frame
  const containerStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  };

  const mediaStyle: React.CSSProperties = {
    width: '96%',
    height: '96%',
    objectFit: 'contain',
    transform: 'scale(0.98)',
  };

  if (type === 'video') {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    const [durationSec, setDurationSec] = useState<number | null>(null);

    // Capture the frame when this layer first mounts to compute relative time
    const mountFrameRef = useRef<number | null>(null);
    if (mountFrameRef.current === null) {
      mountFrameRef.current = frame;
    }
    const relFrame = mountFrameRef.current !== null ? frame - mountFrameRef.current : 0;
    const maxFrames = durationSec != null ? Math.floor(durationSec * fps) : null;

    // If the video finished, hide the layer so it doesn't wait for scene end
    if (maxFrames != null && relFrame > maxFrames) {
      return null;
    }

    return (
      <AbsoluteFill style={containerStyle}>
        <Video
            src={src}
            style={mediaStyle}
            onError={onError}
            onLoadedMetadata={(e: any) => {
              const d = e?.currentTarget?.duration;
              if (typeof d === 'number' && isFinite(d) && d > 0) {
                setDurationSec(d);
              }
            }}
        />
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={containerStyle}>
      <Img
        src={src}
        style={mediaStyle}
        onError={onError}
      />
    </AbsoluteFill>
  );
};
