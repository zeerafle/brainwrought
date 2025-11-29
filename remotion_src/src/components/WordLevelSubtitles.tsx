import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';
import { z } from 'zod';
import { VoiceTimingSchema } from '../schema';

type VoiceTiming = z.infer<typeof VoiceTimingSchema>;

export const WordLevelSubtitles: React.FC<{
  voiceTiming: VoiceTiming;
  startFrame: number;
}> = ({ voiceTiming, startFrame }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const relativeFrame = frame - startFrame;
  const currentTime = relativeFrame / fps;

  const currentItem = voiceTiming.word_timestamps
    ? voiceTiming.word_timestamps.find(
        (ts) => currentTime >= ts.start && currentTime <= ts.end
      )
    : voiceTiming.character_timestamps.find(
        (ts) => currentTime >= ts.start && currentTime <= ts.end
      );

  if (!currentItem) return null;

  const text = 'word' in currentItem ? currentItem.word : currentItem.character;

  return (
    <AbsoluteFill
      style={{
        justifyContent: 'center',
        alignItems: 'center',
        top: '30%', // Position lower for "brainrot" style usually, or center
      }}
    >
      <div
        style={{
          fontFamily: 'Impact, sans-serif',
          fontSize: 100,
          color: 'white',
          textShadow: '4px 4px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000',
          textAlign: 'center',
          padding: '0 20px',
          transform: 'scale(1.1)', // Slight pop
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};
