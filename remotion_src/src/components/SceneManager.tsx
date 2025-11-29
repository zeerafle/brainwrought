import React from 'react';
import { Sequence, Audio, staticFile } from 'remotion';
import { BrainrotProps } from '../schema';
import { MediaLayer } from './MediaLayer';
import { WordLevelSubtitles } from './WordLevelSubtitles';

export const SceneManager: React.FC<BrainrotProps> = ({ scenes, asset_plan, voice_timing }) => {
  let currentFrame = 0;

  // Ensure asset_plan is an array before trying to find
  const safeAssetPlan = Array.isArray(asset_plan) ? asset_plan : (asset_plan as any)?.scenes || [];

  return (
    <>
      {scenes.map((scene, index) => {
        const timing = voice_timing.find((vt) => vt.scene_id === scene.scene_number);
        const assets = safeAssetPlan.find((ap: any) => ap.scene_name.includes(scene.scene_number.toString()) || ap.scene_name === scene.scene_number.toString()); // Loose matching for now

        // Default duration if no audio timing (e.g. 5 seconds)
        const durationInSeconds = timing ? timing.duration_seconds : 5;
        const durationInFrames = Math.ceil(durationInSeconds * 30);

        const startFrame = currentFrame;
        currentFrame += durationInFrames;

        const videoAsset = assets?.video_asset?.[0]; // Take first video asset
        // If video asset is a filename, we assume it's in the assets folder.
        // We might need to adjust this path logic based on how Modal mounts volumes.
        // If it's a generated asset, it might already have the full path from the production node.
        // If it's a stock asset, we might need to prepend 'vol/stock/'.
        // For now, let's assume if it doesn't start with 'vol/', it's a stock asset or needs prefixing.

        let assetPath = null;
        if (videoAsset) {
            if (videoAsset.startsWith('vol/') || videoAsset.startsWith('http')) {
                assetPath = videoAsset;
            } else {
                // If the asset name looks like a description (contains spaces), it's likely a placeholder
                // that hasn't been replaced by a real file path yet.
                if (videoAsset.includes(' ')) {
                    console.warn(`⚠️ Asset path looks like a description, skipping: "${videoAsset}"`);
                    assetPath = null;
                } else {
                    // Assume it's a generated LTX video in the volume root or stock
                    assetPath = `vol/${videoAsset}`;
                }
            }
        }

        const audioPath = timing?.audio_path;
        // Ensure audioPath is handled correctly with staticFile
        // If it already starts with vol/, staticFile handles it relative to public/
        // If it's an absolute path or URL, we might need adjustment.
        // Our pipeline sends "vol/sessions/..." which is correct for staticFile("vol/sessions/...")

        const finalAudioSrc = audioPath ? (audioPath.startsWith("http") ? audioPath : staticFile(audioPath)) : null;

        return (
          <Sequence key={index} from={startFrame} durationInFrames={durationInFrames}>
            <MediaLayer assetPath={assetPath} type="video" />

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
