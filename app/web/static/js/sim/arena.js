/*
 * arena.js — side-view arena geometry, colors, and sprite definitions.
 *
 * The fight domain uses a 1D arena: positions are scalars x in [0, 100]. The red
 * fighter (team 0) starts at x = 20 facing +x (right); the blue fighter (team 1)
 * starts at x = 80 facing -x (left). This module maps that world onto the canvas
 * and declares the per-fighter sprite strip definitions (adapted from the Street
 * Fighter reference sprites).
 */

export const WORLD = { MIN: 0, MAX: 100 };

// Team colors (used for bars and labels).
export const TEAM_COLORS = ["#38bdf8", "#fbbf24"]; // red team -> sky, blue team -> amber

// Fighter names shown in labels.
export const TEAM_NAMES = ["RED", "BLUE"];

// Per-fighter sprite definitions. `frame` is the square frame size of the source
// strip; `scale` is the target display height factor; `actions` maps a pose key to
// the source PNG filename. The blue fighter (wizard) has no Attack3 sprite, so its
// `attack3` pose reuses `Attack2`.
export const SPRITES = {
  red: {
    frame: 162,
    displayHeight: 200,
    actions: {
      idle: "Idle",
      run: "Run",
      jump: "Jump",
      attack1: "Attack1",
      attack2: "Attack2",
      attack3: "Attack3",
      hit: "Take hit",
      death: "Death",
      fall: "Fall",
    },
  },
  blue: {
    frame: 250,
    displayHeight: 200,
    actions: {
      idle: "Idle",
      run: "Run",
      jump: "Jump",
      attack1: "Attack1",
      attack2: "Attack2",
      attack3: "Attack2", // no Attack3 sprite for the wizard
      hit: "Take hit",
      death: "Death",
      fall: "Fall",
    },
  },
};

// Pose keys -> sprite action filenames are identical for both fighters; the fighter
// "teamIndex" (0 = red, 1 = blue) selects which SPRITES entry to use.
export function spriteFor(teamIndex) {
  return teamIndex === 0 ? SPRITES.red : SPRITES.blue;
}

// Map a world x (0..100) to a screen x, given a canvas width and side margins.
export function worldToScreenX(worldX, width, margin = 60) {
  const usable = width - margin * 2;
  return margin + (worldX / (WORLD.MAX - WORLD.MIN)) * usable;
}

// Map a screen x back to world x (for scrub/click, if needed).
export function screenToWorldX(screenX, width, margin = 60) {
  const usable = width - margin * 2;
  return ((screenX - margin) / usable) * (WORLD.MAX - WORLD.MIN);
}
