import { Composition } from 'remotion';
import { BrainrotComposition } from './Composition';
import { BrainrotPropsSchema } from './schema';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="BrainrotComposition"
        component={BrainrotComposition}
        durationInFrames={30 * 60} // Default 60s, will be overridden by props
        fps={30}
        width={1080}
        height={1920}
        schema={BrainrotPropsSchema}
        defaultProps={{
          scenes: [],
          asset_plan: [],
          voice_timing: [],
          total_duration: 60,
        }}
      />
    </>
  );
};
