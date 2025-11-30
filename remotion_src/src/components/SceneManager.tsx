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

        const sfxList = assets?.sfx || [];

        return (
          <Sequence key={index} from={startFrame} durationInFrames={durationInFrames} style={{ zIndex: 1 }}>
            {/* Only render MediaLayer if we have a specific asset for this scene */}
            {assetPath && (
                <MediaLayer assetPath={assetPath} type="video" />
            )}

            {/* On-Screen Text Overlay */}
            {scene.on_screen_text && (
                <AbsoluteFill style={{
                    justifyContent: 'flex-start',
                    alignItems: 'center',
                    paddingTop: 100,
                    zIndex: 10
                }}>
                    <div style={{
                        fontFamily: 'monospace',
                        fontSize: 32,
                        color: '#00ff00',
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        padding: '20px',
                        borderRadius: '10px',
                        whiteSpace: 'pre-wrap',
                        textAlign: 'left',
                        maxWidth: '80%',
                        boxShadow: '0 0 10px #00ff00'
                    }}>
                        {scene.on_screen_text}
                    </div>
                </AbsoluteFill>
            )}

            {finalAudioSrc && (
               <Audio
                src={finalAudioSrc}
                onError={(e) => console.error(`❌ Failed to load audio: ${finalAudioSrc}`, e)}
               />
            )}

            {/* SFX Layers */}
            {sfxList.map((sfxItem: any, sfxIndex: number) => {
                if (!sfxItem.audio_path) return null;
                const sfxSrc = staticFile(sfxItem.audio_path);
                // Calculate start frame relative to the scene start
                // Ensure it doesn't start before the scene (max(0, ...))
                const offsetFrames = Math.max(0, Math.floor(sfxItem.timestamp_offset * 30));

                return (
                    <Sequence key={`sfx-${index}-${sfxIndex}`} from={offsetFrames}>
                        <Audio
                            src={sfxSrc}
                            onError={(e) => console.error(`❌ Failed to load SFX: ${sfxSrc}`, e)}
                        />
                    </Sequence>
                );
            })}

            {timing && (
              <WordLevelSubtitles voiceTiming={timing} startFrame={0} />
            )}
          </Sequence>
        );
      })}
    </>
  );
};
