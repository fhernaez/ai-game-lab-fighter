/*
 * renderer.js — side-view arena renderer.
 *
 * Draws the two fighters (sprite animation), their health/stamina bars, a distance
 * gauge, hit flashes, block guards, dodge leans, and the victory overlay. It is
 * driven entirely by the replayed MatchState and the current time `t`.
 */

import { worldToScreenX, spriteFor } from "./arena.js";
import { getFrame } from "./fighters.js";

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
    const rect = this.canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.width = rect.width || 960;
    this.height = Math.round(this.width * 0.55);
    this.canvas.width = Math.round(this.width * dpr);
    this.canvas.height = Math.round(this.height * dpr);
    this.canvas.style.height = `${this.height}px`;
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  frameIndexFor(f, t, frameCount) {
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

    // Distance gauge (top center).
    this.drawDistance(ctx, state, W);

    // Fighters (draw the one on the left first, then the right, so the nearer one
    // overlaps when they are close).
    const [a, b] = state.fighters[0].x <= state.fighters[1].x
      ? [state.fighters[0], state.fighters[1]]
      : [state.fighters[1], state.fighters[0]];
    this.drawFighter(ctx, a, state, t, groundY);
    this.drawFighter(ctx, b, state, t, groundY);

    // Victory overlay.
    if (state.winner !== null) {
      this.drawVictory(ctx, state, W, H);
    }
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

  drawFighter(ctx, f, state, t, groundY) {
    const sx = worldToScreenX(f.x, this.width);
    const opponent = state.fighters[1 - f.teamIndex];
    const facing = opponent.x >= f.x ? 1 : -1;
    const pose = f.health <= 0 ? "death" : f.action;
    const frame = getFrame(f.teamIndex, pose);
    const displayH = spriteFor(f.teamIndex).displayHeight;
    const destW = displayH;
    const destH = displayH;

    // Hit flash: a translucent red overlay behind the fighter when recently hit.
    if (t < f.pulseUntil) {
      ctx.fillStyle = "rgba(248,113,113,0.35)";
      ctx.beginPath();
      ctx.arc(sx, groundY - destH / 2, destW * 0.6, 0, Math.PI * 2);
      ctx.fill();
    }

    // Block guard: a colored shield arc in front of the fighter.
    if (t < f.guardUntil) {
      ctx.strokeStyle = "#34d399";
      ctx.lineWidth = 6;
      ctx.beginPath();
      const dir = facing;
      ctx.arc(sx + dir * destW * 0.25, groundY - destH / 2, destW * 0.55, -Math.PI / 2, Math.PI / 2);
      ctx.stroke();
    }

    // Dodge lean: shift the fighter slightly and draw a motion arc.
    const dodgeShift = t < f.dodgeUntil ? -facing * 12 : 0;

    if (frame) {
      const frameSize = frame.frameSize;
      const frameCount = frame.frameCount;
      const idx = this.frameIndexFor(f, t, frameCount);
      ctx.save();
      ctx.translate(sx + dodgeShift, groundY);
      ctx.scale(facing, 1);
      ctx.drawImage(
        frame.img,
        idx * frameSize, 0, frameSize, frameSize,
        -destW / 2, -destH, destW, destH
      );
      ctx.restore();
    } else {
      // Procedural fallback silhouette.
      ctx.save();
      ctx.translate(sx + dodgeShift, groundY);
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
    // Health bar (green -> red).
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
