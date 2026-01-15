/**
 * Image enhancement utilities for real-time face/skin beautification.
 * Runs entirely in the browser using Canvas API for Pi 5 compatibility.
 */

export interface EnhancementSettings {
  brightness: number; // -100 to 100, default 0
  contrast: number; // -100 to 100, default 0
  saturation: number; // -100 to 100, default 0
  warmth: number; // -100 to 100, default 0 (skin tone warmth)
  smoothing: number; // 0 to 100, default 0 (skin smoothing)
}

export const DEFAULT_ENHANCEMENT: EnhancementSettings = {
  brightness: 0,
  contrast: 0,
  saturation: 0,
  warmth: 0,
  smoothing: 0,
};

// Preset configurations for quick selection
export const ENHANCEMENT_PRESETS: Record<string, EnhancementSettings> = {
  none: { ...DEFAULT_ENHANCEMENT },
  natural: {
    brightness: 5,
    contrast: 5,
    saturation: 5,
    warmth: 10,
    smoothing: 15,
  },
  bright: {
    brightness: 15,
    contrast: 10,
    saturation: 0,
    warmth: 5,
    smoothing: 10,
  },
  warm: {
    brightness: 5,
    contrast: 5,
    saturation: 10,
    warmth: 25,
    smoothing: 10,
  },
  soft: {
    brightness: 10,
    contrast: -5,
    saturation: -10,
    warmth: 15,
    smoothing: 30,
  },
};

/**
 * Apply CSS filter string for real-time video preview.
 * This is efficient and runs at 60fps.
 */
export function getFilterString(settings: EnhancementSettings): string {
  const filters: string[] = [];

  // Brightness: CSS filter uses 100% as baseline
  if (settings.brightness !== 0) {
    filters.push(`brightness(${100 + settings.brightness}%)`);
  }

  // Contrast: CSS filter uses 100% as baseline
  if (settings.contrast !== 0) {
    filters.push(`contrast(${100 + settings.contrast}%)`);
  }

  // Saturation: CSS filter uses 100% as baseline
  if (settings.saturation !== 0) {
    filters.push(`saturate(${100 + settings.saturation}%)`);
  }

  // Warmth: Use sepia + hue-rotate for warm effect
  if (settings.warmth > 0) {
    const sepiaAmount = Math.min(settings.warmth / 2, 30);
    filters.push(`sepia(${sepiaAmount}%)`);
  } else if (settings.warmth < 0) {
    // Cool effect using hue-rotate
    filters.push(`hue-rotate(${settings.warmth / 5}deg)`);
  }

  return filters.join(" ");
}

/**
 * Apply full enhancement to canvas image data.
 * Used when capturing the final photo.
 */
export function applyEnhancement(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  settings: EnhancementSettings,
): void {
  const imageData = ctx.getImageData(0, 0, width, height);
  const data = imageData.data;

  // Pre-calculate adjustment values
  const brightnessAdj = settings.brightness * 2.55; // Convert to 0-255 range
  const contrastFactor = (259 * (settings.contrast + 255)) / (255 * (259 - settings.contrast));
  const saturationAdj = 1 + settings.saturation / 100;
  const warmthAdj = settings.warmth / 100;

  for (let i = 0; i < data.length; i += 4) {
    let r = data[i];
    let g = data[i + 1];
    let b = data[i + 2];

    // Apply brightness
    r += brightnessAdj;
    g += brightnessAdj;
    b += brightnessAdj;

    // Apply contrast
    r = contrastFactor * (r - 128) + 128;
    g = contrastFactor * (g - 128) + 128;
    b = contrastFactor * (b - 128) + 128;

    // Apply saturation
    const gray = 0.2126 * r + 0.7152 * g + 0.0722 * b;
    r = gray + saturationAdj * (r - gray);
    g = gray + saturationAdj * (g - gray);
    b = gray + saturationAdj * (b - gray);

    // Apply warmth (shift red/blue balance)
    if (warmthAdj !== 0) {
      r += warmthAdj * 30;
      b -= warmthAdj * 20;
    }

    // Clamp values
    data[i] = Math.max(0, Math.min(255, r));
    data[i + 1] = Math.max(0, Math.min(255, g));
    data[i + 2] = Math.max(0, Math.min(255, b));
  }

  ctx.putImageData(imageData, 0, 0);

  // Apply smoothing if needed (using blur technique)
  if (settings.smoothing > 0) {
    applySoftSkinEffect(ctx, width, height, settings.smoothing);
  }
}

/**
 * Apply soft skin smoothing effect.
 * Uses a simple blur + blend technique for performance.
 */
function applySoftSkinEffect(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  intensity: number,
): void {
  // Create temporary canvas for blur
  const tempCanvas = document.createElement("canvas");
  tempCanvas.width = width;
  tempCanvas.height = height;
  const tempCtx = tempCanvas.getContext("2d");

  if (!tempCtx) return;

  // Copy original
  tempCtx.drawImage(ctx.canvas, 0, 0);

  // Apply blur to temp canvas
  const blurRadius = Math.ceil(intensity / 10);
  ctx.filter = `blur(${blurRadius}px)`;
  ctx.drawImage(tempCanvas, 0, 0);
  ctx.filter = "none";

  // Blend blurred with original for natural look
  const blendAlpha = intensity / 200; // 0 to 0.5
  ctx.globalAlpha = 1 - blendAlpha;
  ctx.drawImage(tempCanvas, 0, 0);
  ctx.globalAlpha = 1;
}

/**
 * Quick check if any enhancement is applied
 */
export function hasEnhancement(settings: EnhancementSettings): boolean {
  return (
    settings.brightness !== 0 ||
    settings.contrast !== 0 ||
    settings.saturation !== 0 ||
    settings.warmth !== 0 ||
    settings.smoothing !== 0
  );
}
