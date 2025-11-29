import React from 'react';
import { AbsoluteFill } from 'remotion';
import { BrainrotProps } from './schema';
import { SceneManager } from './components/SceneManager';

export const BrainrotComposition: React.FC<BrainrotProps> = (props) => {
  return (
    <AbsoluteFill style={{ backgroundColor: 'black' }}>
      <SceneManager {...props} />
    </AbsoluteFill>
  );
};
