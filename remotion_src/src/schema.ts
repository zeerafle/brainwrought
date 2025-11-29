import { z } from 'zod';

export const VoiceTimingSchema = z.object({
  scene_id: z.number(),
  scene_name: z.string(),
  text: z.string(),
  audio_path: z.string().nullable(),
  duration_seconds: z.number(),
  character_timestamps: z.array(
    z.object({
      character: z.string(),
      start: z.number(),
      end: z.number(),
    })
  ),
});

export const SceneAssetSchema = z.object({
  scene_name: z.string(),
  video_asset: z.array(z.string()),
  bgm: z.array(z.string()).optional(),
  sfx: z.array(z.string()).optional(),
});

export const SceneSchema = z.object({
  scene_number: z.number(),
  on_screen_action: z.string(),
  dialogue_vo: z.string(),
  on_screen_text: z.string(),
});

export const BrainrotPropsSchema = z.object({
  scenes: z.array(SceneSchema),
  asset_plan: z.array(SceneAssetSchema),
  voice_timing: z.array(VoiceTimingSchema),
  total_duration: z.number().optional(),
});

export type BrainrotProps = z.infer<typeof BrainrotPropsSchema>;
