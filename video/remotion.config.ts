import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
// CRF 18 is visually lossless enough for slides that are mostly type.
// Type artefacts at higher CRF are the first thing a participant notices.
Config.setCrf(18);
