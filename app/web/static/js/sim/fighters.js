/*
 * fighters.js — sprite loading for the two fighters.
 *
 * Each fighter's animation is a set of horizontal strip PNGs (one per pose). This
 * module loads them all and exposes a cache so the renderer can draw the correct
 * frame. Missing images (e.g. the blue fighter's Attack3) are handled by falling
 * back to another pose; if an image fails to load, the renderer draws a procedural
 * fallback silhouette instead.
 */

import { SPRITES } from "./arena.js";

// cache: "red:Idle" -> { img, frameCount }
const cache = {};

const loadImage = (src) =>
  new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => resolve(null);
    img.src = src;
  });

export async function loadFighterSprites() {
  for (const team of Object.keys(SPRITES)) {
    const spec = SPRITES[team];
    // Collect the unique filenames we need (attack3 may alias Attack2 for blue).
    const unique = new Set(Object.values(spec.actions));
    for (const filename of unique) {
      const img = await loadImage(`/static/img/fighters/${team}/${filename}.png`);
      if (img) {
        cache[`${team}:${filename}`] = {
          img,
          frameCount: Math.max(1, Math.floor(img.naturalWidth / spec.frame)),
        };
      }
    }
  }
  return cache;
}

// Resolve a pose key into { img, frameCount, frameSize } for a fighter, or null.
export function getFrame(teamIndex, poseKey) {
  const team = teamIndex === 0 ? "red" : "blue";
  const spec = SPRITES[team];
  const filename = spec.actions[poseKey] || "Idle";
  const entry = cache[`${team}:${filename}`];
  if (!entry) return null;
  return { ...entry, frameSize: spec.frame };
}
