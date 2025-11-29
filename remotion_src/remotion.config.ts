import { Config } from '@remotion/cli/config';
import path from 'path';

Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
// Ensure public dir is absolute path to avoid ambiguity
Config.setPublicDir(path.join(process.cwd(), 'public'));
Config.setDelayRenderTimeoutInMilliseconds(60000); // Increase timeout for large assets
