/*
 * main.js — bootstrap: wire the renderer, replay engine, controls, and live client.
 */

import { Renderer } from "./renderer.js";
import { ReplayEngine } from "./replay.js";
import { LiveClient } from "./live.js";
import { loadFighterSprites } from "./fighters.js";

const $ = (id) => document.getElementById(id);
const LIVE = new Set(["queued", "accepted", "ready", "running"]);

function fmtTime(ms) {
  const s = Math.max(0, Math.floor(ms / 1000));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

function setStatus(statusEl, status) {
  if (!statusEl) return;
  if (status === "queued" || status === "accepted" || status === "ready") {
    statusEl.textContent = "Waiting to start…";
  } else if (status === "running") {
    statusEl.textContent = "▶ Fight running…";
  } else if (status === "finished") {
    statusEl.textContent = "Finished";
  } else if (status === "failed" || status === "cancelled") {
    statusEl.textContent = "Fight " + status + ".";
  } else if (status === "reconnecting") {
    statusEl.textContent = "⚠ Reconnecting…";
  } else {
    statusEl.textContent = "";
  }
}

function buildScoreboard(scoreboardEl, teams) {
  const names = Array.from(new Set((teams || []).map((t) => t.name)));
  scoreboardEl.innerHTML = "";
  names.forEach((name, i) => {
    const div = document.createElement("div");
    div.className = "team";
    div.dataset.team = name;
    div.innerHTML = `<div class="muted">${name} <span class="muted">(${i === 0 ? "RED" : "BLUE"})</span></div>
      <div class="score">rounds 0 · 0</div>`;
    scoreboardEl.appendChild(div);
  });
}

function updateScoreboard(scoreboardEl, state) {
  const names = Array.from(new Set(state.teams.map((t) => t.name)));
  names.forEach((name, i) => {
    const node = scoreboardEl.querySelector(`[data-team="${name}"] .score`);
    if (!node) return;
    const rounds = (state.rounds && state.rounds[i]) || 0;
    node.textContent = `rounds ${rounds} · ${state.rounds[1 - i]}`;
  });
}

function logEvent(logEl, ev) {
  const item = document.createElement("div");
  item.className = "item";
  const p = ev.payload || {};
  let detail = "";
  if (ev.event_type === "DECISION") {
    detail = `${p.message || ""} <span class="muted">(${p.move} · ${p.action}${p.action === "BLOCK" || p.action === "DODGE" ? "" : " " + p.height} power=${Number(p.power || 0).toFixed(2)})</span>`;
    if (p.error) detail += `<br><span class="etype">⚠ ${p.error}</span>`;
  } else if (ev.event_type === "MOVEMENT") {
    detail = `move ${p.move} · ${Number(p.from_pos).toFixed(0)} → ${Number(p.to_pos).toFixed(0)}`;
  } else if (ev.event_type === "ATTACK") {
    detail = `${p.action} ${p.height || ""} — ${p.result}${p.damage ? ` · ${Number(p.damage).toFixed(0)} dmg` : ""}`;
  } else if (ev.event_type === "HIT") {
    detail = `took ${Number(p.damage).toFixed(0)} damage`;
  } else if (ev.event_type === "BLOCK") {
    detail = `blocks · ${Math.round(Number(p.reduction) * 100)}% reduction`;
  } else if (ev.event_type === "DODGE") {
    detail = `dodges the strike`;
  } else if (ev.event_type === "DAMAGE") {
    detail = `health → ${Number(p.health).toFixed(0)}`;
  } else if (ev.event_type === "STAMINA") {
    detail = `stamina → ${Number(p.stamina).toFixed(0)}`;
  } else if (ev.event_type === "ROUND_WON") {
    detail = `round ${p.round} won by team ${p.winner}`;
  } else if (ev.event_type === "MATCH_FINISHED") {
    detail = `winner: team ${p.winner}`;
  } else if (ev.event_type === "ROUND_STARTED") {
    detail = `round ${p.round}`;
  }
  item.innerHTML = `<span class="etype">${ev.event_type}</span> <span class="muted">${ev.actor_id || ""}${typeof p.team === "number" ? " · team " + p.team : ""}</span><br>${detail}`;
  logEl.appendChild(item);
  while (logEl.children.length > 150) logEl.removeChild(logEl.firstChild);
  logEl.scrollTop = logEl.scrollHeight;
}

(async () => {
  const root = $("match-root");
  if (!root) return;
  const matchId = root.dataset.matchId;

  const canvas = $("arena-canvas");
  const scoreboardEl = $("scoreboard");
  const logEl = $("event-log");
  const statusEl = $("match-status");
  const playBtn = $("sim-play");
  const speedSel = $("sim-speed");
  const scrub = $("sim-scrub");
  const timeEl = $("sim-time");
  const stepBack = $("sim-step-back");
  const stepFwd = $("sim-step-fwd");

  const renderer = new Renderer(canvas);
  window.addEventListener("resize", () => renderer.resize());

  // Load sprites + background/victory images (non-fatal if missing).
  loadFighterSprites().catch(() => {});
  const bg = new Image();
  bg.onload = () => renderer.setBackground(bg);
  bg.src = "/static/img/fighters/background.jpg";
  const victory = new Image();
  victory.onload = () => renderer.setVictory(victory);
  victory.src = "/static/img/fighters/victory.png";

  const stateRes = await (await fetch(`/api/matches/${matchId}/state`)).json();
  const teams = stateRes.teams || [];
  buildScoreboard(scoreboardEl, teams);
  setStatus(statusEl, stateRes.status);

  const eventsRes = await (await fetch(`/api/matches/${matchId}/events`)).json();
  const allEvents = eventsRes.events || [];

  const engine = new ReplayEngine(teams, allEvents);
  allEvents.forEach((ev) => logEvent(logEl, ev));

  engine.speed = parseFloat(speedSel.value || "1");
  scrub.max = engine.duration || 1;

  let playing = false;
  const setPlaying = (p) => {
    playing = p;
    playBtn.textContent = p ? "Pause" : "Play";
  };

  const updateScrub = () => {
    scrub.value = Math.round(engine.t);
    timeEl.textContent = `${fmtTime(engine.t)} / ${fmtTime(engine.duration)}`;
  };

  playBtn.addEventListener("click", () => {
    if (!engine.duration) return;
    if (playing) setPlaying(false);
    else {
      if (engine.t >= engine.duration) {
        engine.seek(0);
      }
      setPlaying(true);
    }
  });
  speedSel.addEventListener("change", () => {
    engine.speed = parseFloat(speedSel.value || "1");
  });
  scrub.addEventListener("input", () => {
    engine.seek(parseFloat(scrub.value));
  });
  stepBack.addEventListener("click", () => {
    engine.seek(engine.t - 400);
  });
  stepFwd.addEventListener("click", () => {
    engine.seek(engine.t + 400);
  });

  const live = new LiveClient(matchId, {
    onEvents: (events) => {
      events.forEach((e) => engine.events.push(e));
      engine.segments = engine.build();
      engine.duration = engine.segments.length
        ? engine.segments[engine.segments.length - 1].end
        : 0;
      scrub.max = engine.duration || 1;
      events.forEach((e) => logEvent(logEl, e));
    },
    onStatus: (status) => setStatus(statusEl, status),
    onError: () => setStatus(statusEl, "reconnecting"),
  });

  let last = performance.now();
  function frame(now) {
    const dt = now - last;
    last = now;
    if (playing) {
      const nt = Math.min(engine.duration, engine.t + dt * engine.speed);
      engine.applyProgress(nt);
      if (nt >= engine.duration) setPlaying(false);
    }
    renderer.draw(engine.state, engine.t);
    updateScoreboard(scoreboardEl, engine.state);
    updateScrub();
    requestAnimationFrame(frame);
  }
  // Auto-play on load; the user can pause/resume via the button.
  setPlaying(true);
  requestAnimationFrame(frame);

  live.poll();
})();
