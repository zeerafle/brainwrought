import React, { useMemo } from 'react';
import { Sequence, Audio, staticFile, AbsoluteFill, Video, random } from 'remotion';
import { BrainrotProps } from '../schema';
import { MediaLayer } from './MediaLayer';
import { WordLevelSubtitles } from './WordLevelSubtitles';

export const SceneManager: React.FC<BrainrotProps> = ({ scenes, asset_plan, voice_timing }) => {
  let currentFrame = 0;

  // Ensure asset_plan is an array before trying to find
  const safeAssetPlan = Array.isArray(asset_plan) ? asset_plan : (asset_plan as any)?.scenes || [];

  // Calculate random start time for the background gameplay video
  // Use the first scene's text as a seed to keep it consistent for this video
  const seed = scenes[0]?.dialogue_vo || 'default-seed';
  const gameplayStart = useMemo(() => {
      // Random start between 0 and 20 minutes (1200 seconds)
      // Assuming the video is 30 mins long, this leaves plenty of room
      return Math.floor(random(seed) * 1200);
  }, [seed]);

  const backgroundSrc = staticFile("vol/stock/gameplay/minecraft.mp4");

  return (
    <>
      {/* Continuous Background Layer */}
      <AbsoluteFill style={{ zIndex: 0 }}>
        <Video
            src={backgroundSrc}
            startFrom={gameplayStart * 30} // Convert seconds to frames
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            loop
            muted
            onError={(e) => console.error(`❌ Failed to load background media: ${backgroundSrc}`, e)}
        />
      </AbsoluteFill>

      {scenes.map((scene, index) => {
        const timing = voice_timing.find((vt) => vt.scene_id === scene.scene_number);
        const assets = safeAssetPlan.find((ap: any) => ap.scene_name.includes(scene.scene_number.toString()) || ap.scene_name === scene.scene_number.toString()); // Loose matching for now

        // Default duration if no audio timing (e.g. 5 seconds)
        const durationInSeconds = timing ? timing.duration_seconds : 5;
        const durationInFrames = Math.ceil(durationInSeconds * 30);

        const startFrame = currentFrame;
        currentFrame += durationInFrames;

        const videoAsset = assets?.video_asset?.[0]; // Take first video asset

        let assetPath = null;
        if (videoAsset) {
            if (videoAsset.startsWith('vol/') || videoAsset.startsWith('http')) {
                assetPath = videoAsset;
            } else {
                if (videoAsset.includes(' ')) {
                    // console.warn(`⚠️ Asset path looks like a description, skipping: "${videoAsset}"`);
                    assetPath = null;
                } else {
                    assetPath = `vol/${videoAsset}`;
                }
            }
        }

        const audioPath = timing?.audio_path;
        const finalAudioSrc = audioPath ? (audioPath.startsWith("http") ? audioPath : staticFile(audioPath)) : null;

        return (
          <Sequence key={index} from={startFrame} durationInFrames={durationInFrames} style={{ zIndex: 1 }}>
            {/* Only render MediaLayer if we have a specific asset for this scene */}
            {assetPath && (
                <MediaLayer assetPath={assetPath} type="video" />
            )}

            {finalAudioSrc && (
               <Audio
                src={finalAudioSrc}
                onError={(e) => console.error(`❌ Failed to load audio: ${finalAudioSrc}`, e)}
               />
            )}

            {timing && (
              <WordLevelSubtitles voiceTiming={timing} startFrame={0} />
            )}
          </Sequence>
        );
      })}
    </>
  );
};
