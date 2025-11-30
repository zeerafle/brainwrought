import React from 'react';
import {
  AbsoluteFill,
  Img,
  interpolate,
  Easing,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type MemeInput =
  | string
  | {
      src: string;
      captionTop?: string;
      captionBottom?: string;
    };

export type MemeLayerProps = {
  // One or more meme images. Each entry can be a string path/URL or an object with captions.
  memes: MemeInput[];

  // Total duration available for this layer (in frames).
  durationInFrames: number;

  // How to render multiple memes:
  // - 'auto'     : choose grid or sequence based on count
  // - 'grid'     : display all at once in a grid
  // - 'sequence' : display one at a time with optional crossfades
  mode?: 'auto' | 'grid' | 'sequence';

  // Grid options (used for mode='grid' or when auto chooses grid)
  grid?: {
    columns?: number;
    rows?: number;
    gap?: number; // px
    padding?: number; // px
  };

  // Sequence options (used for mode='sequence' or when auto chooses sequence)
  sequence?: {
    perImageFrames?: number; // If not provided, divided evenly
    crossfadeFrames?: number; // Defaults to ~15% of perImageFrames, max perImageFrames/2
  };

  // Image fit mode
  objectFit?: 'contain' | 'cover';

  // Slight zoom animation on images
  animate?: boolean;

  // Border radius in px for each image
  imageRadius?: number;

  // Apply classic meme-style white text with black stroke for captions
  strokeText?: boolean;

  // Optional global background color to show behind images
  backgroundColor?: string;
};

const isObjectInput = (m: MemeInput): m is Exclude<MemeInput, string> =>
  typeof m === 'object' && m !== null && 'src' in m;

const resolveSrc = (src: string) => {
  // If it's an absolute URL, use as-is, else resolve via staticFile
  return src.startsWith('http://') || src.startsWith('https://')
    ? src
    : staticFile(src);
};

const pickMode = (count: number, explicit?: MemeLayerProps['mode']): NonNullable<MemeLayerProps['mode']> => {
  if (explicit && explicit !== 'auto') return explicit;
  // Auto selection heuristics:
  // 1 => single (grid falls back to 1x1)
  // 2-6 => grid
  // >6 => sequence
  if (count <= 6) return 'grid';
  return 'sequence';
};

const defaultGridForCount = (count: number) => {
  // Determine a reasonable grid for a given number of items
  if (count <= 1) return { columns: 1, rows: 1 };
  if (count <= 2) return { columns: 1, rows: 2 }; // vertical stack for 2 (TikTok vibe)
  if (count <= 4) return { columns: 2, rows: 2 };
  if (count <= 6) return { columns: 3, rows: 2 };
  if (count <= 9) return { columns: 3, rows: 3 };
  // Fallback to square-ish
  const columns = Math.ceil(Math.sqrt(count));
  const rows = Math.ceil(count / columns);
  return { columns, rows };
};

const Caption: React.FC<{
  text: string;
  position: 'top' | 'bottom';
  strokeText: boolean;
}> = ({ text, position, strokeText }) => {
  if (!text) return null;

  const baseStyle: React.CSSProperties = {
    position: 'absolute',
    left: '50%',
    transform: 'translateX(-50%)',
    width: '90%',
    textAlign: 'center',
    color: '#fff',
    fontFamily: 'Impact, "Arial Black", sans-serif',
    fontSize: 64,
    letterSpacing: 1,
    lineHeight: 1.05,
    textTransform: 'uppercase',
    // Ensure text is readable in front of busy images
    textShadow: strokeText
      ? '4px 4px 0 #000, -4px -4px 0 #000, 4px -4px 0 #000, -4px 4px 0 #000, 0 0 12px rgba(0,0,0,0.8)'
      : '0 0 12px rgba(0,0,0,0.8)',
    padding: '8px 12px',
    boxSizing: 'border-box',
  };

  return (
    <div
      style={{
        ...baseStyle,
        top: position === 'top' ? 16 : 'unset',
        bottom: position === 'bottom' ? 16 : 'unset',
      }}
    >
      {text}
    </div>
  );
};

export const MemeLayer: React.FC<MemeLayerProps> = ({
  memes,
  durationInFrames,
  mode = 'auto',
  grid,
  sequence,
  objectFit = 'cover',
  animate = true,
  imageRadius = 0,
  strokeText = true,
  backgroundColor = 'transparent',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (!memes || memes.length === 0 || durationInFrames <= 0) {
    return null;
  }

  // Normalize inputs to object form
  const normalized = memes.map((m) =>
    isObjectInput(m) ? m : { src: m }
  );

  const chosenMode = pickMode(normalized.length, mode);
  const resolved = normalized.map((m) => ({
    ...m,
    src: resolveSrc(m.src),
  }));

  const zoomScale = animate
    ? interpolate(frame, [0, durationInFrames], [1.025, 1.075], {
        easing: Easing.ease,
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 1.0;

  if (chosenMode === 'grid') {
    const defaults = defaultGridForCount(resolved.length);
    const columns = grid?.columns ?? defaults.columns;
    const rows = grid?.rows ?? defaults.rows;
    const gap = grid?.gap ?? 12;
    const padding = grid?.padding ?? 16;

    return (
      <AbsoluteFill
        style={{
          backgroundColor,
          display: 'grid',
          gridTemplateColumns: `repeat(${columns}, 1fr)`,
          gridTemplateRows: `repeat(${rows}, 1fr)`,
          gap,
          padding,
        }}
      >
        {resolved.map((m, idx) => (
          <div
            key={idx}
            style={{
              position: 'relative',
              overflow: 'hidden',
              borderRadius: imageRadius,
            }}
          >
            <Img
              src={m.src}
              style={{
                width: '100%',
                height: '100%',
                objectFit,
                transform: `scale(${zoomScale})`,
                transition: 'transform 0.3s ease-out',
              }}
              onError={(e) => {
                // eslint-disable-next-line no-console
                console.error(`❌ Failed to load meme image: ${m.src}`, e);
              }}
            />
            {m.captionTop && (
              <Caption text={m.captionTop} position="top" strokeText={strokeText} />
            )}
            {m.captionBottom && (
              <Caption text={m.captionBottom} position="bottom" strokeText={strokeText} />
            )}
          </div>
        ))}
      </AbsoluteFill>
    );
  }

  // Sequence mode: show one image at a time, optional crossfade
  const count = resolved.length;
  const perImageFrames =
    sequence?.perImageFrames ?? Math.max(1, Math.floor(durationInFrames / count));
  const crossfadeFramesRaw =
    sequence?.crossfadeFrames ?? Math.max(0, Math.floor(perImageFrames * 0.15));
  const crossfadeFrames = Math.min(crossfadeFramesRaw, Math.floor(perImageFrames / 2));

  return (
    <AbsoluteFill style={{ backgroundColor }}>
      {resolved.map((m, index) => {
        const from = index * perImageFrames;
        const isLast = index === count - 1;
        const duration = isLast
          ? Math.max(1, durationInFrames - from)
          : perImageFrames;

        // Calculate opacity with crossfade
        const rel = frame - from;
        const opacity =
          crossfadeFrames > 0
            ? interpolate(
                rel,
                [0, crossfadeFrames, duration - crossfadeFrames, duration],
                [0, 1, 1, 0],
                { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
              )
            : rel >= 0 && rel <= duration
            ? 1
            : 0;

        if (opacity <= 0) return null;

        return (
          <div
            key={index}
            style={{
              position: 'absolute',
              inset: 0,
              opacity,
              overflow: 'hidden',
              borderRadius: imageRadius,
            }}
          >
            <Img
              src={m.src}
              style={{
                width: '100%',
                height: '100%',
                objectFit,
                transform: `scale(${zoomScale})`,
                transition: 'transform 0.3s ease-out',
              }}
              onError={(e) => {
                // eslint-disable-next-line no-console
                console.error(`❌ Failed to load meme image: ${m.src}`, e);
              }}
            />
            {m.captionTop && (
              <Caption text={m.captionTop} position="top" strokeText={strokeText} />
            )}
            {m.captionBottom && (
              <Caption text={m.captionBottom} position="bottom" strokeText={strokeText} />
            )}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
