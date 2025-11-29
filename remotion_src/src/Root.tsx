import { Composition } from 'remotion';
import { BrainrotComposition } from './Composition';
import { BrainrotPropsSchema } from './schema';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="BrainrotComposition"
        component={BrainrotComposition}
        durationInFrames={30 * 60} // Fallback
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
        calculateMetadata={async ({ props }) => {
            const durationInSeconds = props.total_duration || 60;
            return {
                durationInFrames: Math.ceil(durationInSeconds * 30),
            };
        }}
      />
    </>
  );
};
