/*
 * renderer.js — side-view arena renderer.
 *
 * Layout: the two fighters are drawn on FIXED opposite sides (red left, blue right)
 * with a horizontal gap derived from the current *distance* between them. This keeps
 * them from ever overlapping while still letting "advance / retreat" read as the gap
 * shrinking or growing. Health/stamina bars sit above each fighter, a distance gauge
 * sits at the top, and a transient "ROUND N — RED/BLUE" banner plus a final victory
 * overlay communicate the result.
 *
 * Hit feedback: while a fighter is within its hit window it is (a) flashed red,
 * (b) knocked backward with a decaying offset, and (c) shows an impact burst at the
 * point of contact. A block draws a green guard arc; a dodge leans the fighter aside.
 */

import { spriteFor } from "./arena.js";
import { getFrame } from "./fighters.js";

// Arena layout: min/max pixel gap between the fighters (mapped from distance 0..100).
const GAP_MIN = 170;
const GAP_MAX = 380;
// Hit feedback constants (must roughly match replay.js HIT_DUR).
const HIT_FLASH_MS = 380;
const KNOCKBACK_PX = 28;

export class Renderer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.bg = null;       // optional background image
    this.victory = null;  // optional victory image
    this.resize();
  }

  setBackground(img) {
    this.bg = img;
  }

  setVictory(img) {
    this.victory = img;
  }

  resize() {
    // The canvas fills its container width; height is derived at a 16:9-ish ratio.
    const rect = this.canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.width = rect.width || 960;
    this.height = Math.round(this.width * 0.55);
    this.canvas.width = Math.round(this.width * dpr);
    this.canvas.height = Math.round(this.height * dpr);
    this.canvas.style.height = `${this.height}px`;
    // Set the transform so we draw in CSS pixels regardless of devicePixelRatio.
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  frameIndexFor(f, t, frameCount) {
    // Looping poses (idle/run) cycle continuously; one-shot poses play once.
    if (f.action === "idle" || f.action === "run") {
      return Math.floor((t / 120) % frameCount);
    }
    const p = Math.max(0, Math.min(1, (t - f.actionStart) / Math.max(1, f.actionDur)));
    return Math.min(frameCount - 1, Math.floor(p * frameCount));
  }

  draw(state, t) {
    const ctx = this.ctx;
    const W = this.width;
    const H = this.height;
    const groundY = H - 60;

    ctx.clearRect(0, 0, W, H);
    this.drawBackground(ctx, W, H);

    // Ground line.
    ctx.strokeStyle = "rgba(226,232,240,0.5)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(0, groundY);
    ctx.lineTo(W, groundY);
    ctx.stroke();

    this.drawDistance(ctx, state, W);

    // Distance (world units) -> pixel gap. Clamped so the fighters never overlap.
    const distance = Math.abs(state.fighters[0].x - state.fighters[1].x);
    const gap = Math.max(GAP_MIN, Math.min(GAP_MAX, this.mapDistanceToGap(distance)));
    const centerX = W / 2;

    // Red (team 0) always on the left, blue (team 1) always on the right.
    this.drawFighter(ctx, state.fighters[0], centerX - gap / 2, t, groundY);
    this.drawFighter(ctx, state.fighters[1], centerX + gap / 2, t, groundY);

    // Transient round banner (shown only for ROUND_BANNER_MS after a round ends).
    if (state.roundBanner && t < state.roundBanner.until) {
      this.drawRoundBanner(ctx, state.roundBanner, t, W);
    }

    // Final victory overlay (only once the match winner is known).
    if (state.winner !== null) {
      this.drawVictory(ctx, state, W, H);
    }
  }

  mapDistanceToGap(distance) {
    // Linear map of world distance (0..100) into the pixel gap range (GAP_MIN..GAP_MAX).
    const frac = Math.max(0, Math.min(1, distance / 100));
    return GAP_MIN + (GAP_MAX - GAP_MIN) * frac;
  }

  drawBackground(ctx, W, H) {
    const bg = ctx.createLinearGradient(0, 0, 0, H);
    bg.addColorStop(0, "#0b1220");
    bg.addColorStop(1, "#1c2a44");
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, W, H);
    if (this.bg) {
      ctx.globalAlpha = 0.55;
      ctx.drawImage(this.bg, 0, 0, W, H);
      ctx.globalAlpha = 1;
    }
  }

  drawDistance(ctx, state, W) {
    const d = Math.abs(state.fighters[0].x - state.fighters[1].x);
    const x = W / 2 - 100;
    const y = 12;
    const w = 200;
    ctx.fillStyle = "rgba(15,23,42,0.7)";
    ctx.fillRect(x, y, w, 8);
    const frac = Math.max(0, Math.min(1, d / 100));
    ctx.fillStyle = "#38bdf8";
    ctx.fillRect(x, y, w * frac, 8);
    ctx.strokeStyle = "rgba(226,232,240,0.6)";
    ctx.lineWidth = 1;
    ctx.strokeRect(x, y, w, 8);
    ctx.fillStyle = "#e2e8f0";
    ctx.font = "11px system-ui";
    ctx.textAlign = "center";
    ctx.fillText(`distance ${d.toFixed(0)}`, W / 2, y + 22);
  }

  drawFighter(ctx, f, sx, t, groundY) {
    // Red faces right (+x), blue faces left (-x). The sprite sheet faces right, so
    // we flip horizontally for the blue fighter.
    const facing = f.teamIndex === 0 ? 1 : -1;
    const pose = f.health <= 0 ? "death" : f.action;
    const frame = getFrame(f.teamIndex, pose);
    const displayH = spriteFor(f.teamIndex).displayHeight;
    const destW = displayH; // square frames
    const destH = displayH;

    // Hit feedback window: flash + impact burst + knockback (all decaying).
    const hitFrac = t < f.pulseUntil ? Math.max(0, (f.pulseUntil - t) / HIT_FLASH_MS) : 0;

    if (hitFrac > 0) {
      // Impact burst at the fighter's center (expands as the hit lands).
      const burstR = (1 - hitFrac) * 46 + 10;
      ctx.strokeStyle = `rgba(251,191,36,${hitFrac})`;
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.arc(sx, groundY - destH / 2, burstR, 0, Math.PI * 2);
      ctx.stroke();
      // Soft red flash behind the fighter.
      ctx.fillStyle = `rgba(248,113,113,${0.35 * hitFrac})`;
      ctx.beginPath();
      ctx.arc(sx, groundY - destH / 2, destW * 0.6, 0, Math.PI * 2);
      ctx.fill();
    }

    // Block guard: a green shield arc in front of the fighter.
    if (t < f.guardUntil) {
      ctx.strokeStyle = "#34d399";
      ctx.lineWidth = 6;
      ctx.beginPath();
      ctx.arc(sx + facing * destW * 0.25, groundY - destH / 2, destW * 0.55, -Math.PI / 2, Math.PI / 2);
      ctx.stroke();
    }

    // Knockback: push the fighter backward (away from the opponent) while hit.
    const knock = hitFrac * KNOCKBACK_PX * facing; // facing points toward the opponent
    // Dodge lean: a small lateral shift away from the incoming strike.
    const dodgeShift = t < f.dodgeUntil ? -facing * 12 : 0;

    if (frame) {
      const frameSize = frame.frameSize;
      const frameCount = frame.frameCount;
      const idx = this.frameIndexFor(f, t, frameCount);
      ctx.save();
      ctx.translate(sx - knock + dodgeShift, groundY);
      ctx.scale(facing, 1);
      // Draw one square source frame, bottom-aligned to the ground line.
      ctx.drawImage(
        frame.img,
        idx * frameSize, 0, frameSize, frameSize,
        -destW / 2, -destH, destW, destH
      );
      ctx.restore();
    } else {
      // Procedural fallback silhouette when a sprite is missing.
      ctx.save();
      ctx.translate(sx - knock + dodgeShift, groundY);
      ctx.fillStyle = f.teamIndex === 0 ? "#7dd3fc" : "#fbbf24";
      ctx.fillRect(-destW / 4, -destH, destW / 2, destH);
      ctx.beginPath();
      ctx.arc(0, -destH - 10, 14, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }

    // Health + stamina bars above the fighter.
    this.drawBars(ctx, f, sx, groundY - destH - 30);

    // Label.
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 12px system-ui";
    ctx.textAlign = "center";
    ctx.fillText(f.label, sx, groundY - destH - 52);
  }

  drawBars(ctx, f, sx, topY) {
    const w = 150;
    const x = sx - w / 2;
    // Health bar (green -> amber -> red as it depletes).
    ctx.fillStyle = "#1e293b";
    ctx.fillRect(x - 2, topY - 2, w + 4, 14);
    const hfrac = Math.max(0, Math.min(1, f.health / 100));
    ctx.fillStyle = hfrac > 0.5 ? "#34d399" : hfrac > 0.25 ? "#fbbf24" : "#f87171";
    ctx.fillRect(x, topY, w * hfrac, 10);
    // Stamina bar (blue).
    const sfrac = Math.max(0, Math.min(1, f.stamina / 100));
    ctx.fillStyle = "#1e293b";
    ctx.fillRect(x - 2, topY + 12, w + 4, 8);
    ctx.fillStyle = "#38bdf8";
    ctx.fillRect(x, topY + 14, w * sfrac, 4);
  }

  drawRoundBanner(ctx, banner, t, W) {
    // Fade out over the last 400ms of the banner window.
    const remaining = Math.max(0, banner.until - t);
    const alpha = Math.min(1, remaining / 400);
    const text = banner.text || "";
    const y = 56;
    ctx.font = "bold 22px system-ui";
    const tw = ctx.measureText(text).width + 40;
    ctx.fillStyle = `rgba(2,6,23,${0.7 * alpha})`;
    ctx.fillRect(W / 2 - tw / 2, y - 22, tw, 44);
    ctx.fillStyle = `rgba(255,255,255,${alpha})`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(text, W / 2, y);
  }

  drawVictory(ctx, state, W, H) {
    ctx.fillStyle = "rgba(2,6,23,0.6)";
    ctx.fillRect(0, 0, W, H);
    if (this.victory) {
      ctx.drawImage(this.victory, W / 2 - 60, H / 2 - 60, 120, 120);
    }
    const label = state.winner === 0 ? "RED WINS" : "BLUE WINS";
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 32px system-ui";
    ctx.textAlign = "center";
    ctx.fillText(label, W / 2, H / 2 - 80);
  }
}
