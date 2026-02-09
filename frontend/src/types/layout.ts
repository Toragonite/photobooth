/**
 * Layout type definitions for PhotoBooth
 */

/** Available layout types for photo arrangement */
export type LayoutType = "1x4" | "2x2" | "1x1";

/** Layout configuration with aspect ratio settings */
export interface LayoutConfig {
  type: LayoutType;
  label: string;
  description: string;
  /** Camera aspect ratio for this layout */
  aspectRatio: "16:9" | "4:3";
  /** Camera resolution */
  resolution: {
    width: number;
    height: number;
  };
  /** Number of photos in each dimension */
  grid: {
    cols: number;
    rows: number;
  };
  /** Number of photos required for this layout */
  photoCount: number;
}

/** Layout configurations */
export const LAYOUT_CONFIGS: Record<LayoutType, LayoutConfig> = {
  "1x1": {
    type: "1x1",
    label: "home.layout.single",
    description: "home.layout.singleDesc",
    aspectRatio: "4:3",
    resolution: {
      width: 1280,
      height: 960,
    },
    grid: {
      cols: 1,
      rows: 1,
    },
    photoCount: 1,
  },
  "1x4": {
    type: "1x4",
    label: "home.layout.strip",
    description: "home.layout.stripDesc",
    aspectRatio: "16:9",
    resolution: {
      width: 1920,
      height: 1080,
    },
    grid: {
      cols: 1,
      rows: 4,
    },
    photoCount: 4,
  },
  "2x2": {
    type: "2x2",
    label: "home.layout.grid",
    description: "home.layout.gridDesc",
    aspectRatio: "4:3",
    resolution: {
      width: 1280,
      height: 960,
    },
    grid: {
      cols: 2,
      rows: 2,
    },
    photoCount: 4,
  },
};

/** Default layout type */
export const DEFAULT_LAYOUT: LayoutType = "2x2";

/** Get required photo count for a layout */
export function getPhotoCount(layoutType: LayoutType): number {
  return LAYOUT_CONFIGS[layoutType]?.photoCount ?? 4;
}
