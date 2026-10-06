/*
 * replay.js — deterministic event-log → timeline engine for the fight.
 *
 * Compiles the fight's event stream into animation segments with cumulative start
 * times, then renders any point in time by replaying segments up to `t`. This gives
 * play / pause / seek / speed with a single applyProgress(t) method.
 *
 * Segment types (produced in `build`, applied in `applySegment`):
 *   - "move"   : a fighter's footwork. Interpolated between `from` and `to` over the
 *                segment duration so the gap between the fighters changes smoothly.
 *   - "attack" : a fighter throws a strike (pose = attack1/attack2/attack3).
 *   - "hit"    : a fighter is struck (pose = "hit", plus a knockback/flash window).
 *   - "block"  : a fighter raises its guard.
 *   - "dodge"  : a fighter slips an attack (pose = "jump" + a dodge window).
 *   - "state"  : an instant (0-duration) patch of health / stamina / rounds / winner,
 *                plus a transient round-won banner.
 */

import { TEAM_NAMES } from "./arena.js";

// Timing constants (ms).
const MOVE_MS_PER_UNIT = 22;  // how long a 1-unit footwork step takes to animate
const ATTACK_DUR = 460;       // duration of a kick animation
const HIT_DUR = 380;          // duration of the "take a hit" reaction
const BLOCK_DUR = 420;        // duration of a block guard
const DODGE_DUR = 420;        // duration of a dodge
const ROUND_BANNER_MS = 1500; // how long the "ROUND N — RED/BLUE" banner stays visible

// Home positions (world x) — must match core/rules.py HOME_POSITIONS.
const HOME = { 0: 20, 1: 80 };

// Technique action -> sprite pose key.
const ACTION_POSE = {
  FRONT_KICK: "attack1",
  PUNCH: "attack1",
  ROUNDHOUSE_KICK: "attack2",
  BACK_KICK: "attack3",
  AXE_KICK: "attack3",
};

export class MatchState {
  constructor(teams) {
    this.teams = teams;
    this.fighters = [];
    this.rounds = [0, 0];
    this.currentRound = 1;
    this.winner = null;
    // Transient "ROUND N — RED/BLUE" banner; cleared on the next round start.
    this.roundBanner = null;
    this.lastActor = null;

    teams.forEach((team, ti) => {
      this.fighters.push({
        teamIndex: ti,
        teamName: team.name,
        label: TEAM_NAMES[ti],
        x: HOME[ti],       // world position (0..100); drives the visual gap
        action: "idle",    // current pose key
        actionStart: 0,    // when the current pose segment began (for frame timing)
        actionDur: 400,    // duration of the current pose segment
        health: 100,
        stamina: 100,
        pulseUntil: -1,    // hit-flash + knockback window (timestamp)
        guardUntil: -1,    // block-guard window (timestamp)
        dodgeUntil: -1,    // dodge-lean window (timestamp)
      });
    });
  }
}

export class ReplayEngine {
  constructor(teams, events) {
    this.teams = teams;
    this.events = events || [];
    this.segments = this.build();
    this.duration = this.segments.length
      ? this.segments[this.segments.length - 1].end
      : 0;
    this.t = 0;
    this.speed = 1;
    this.playing = false;
    this.state = new MatchState(teams);
    this.applyProgress(0);
  }

  build() {
    const segments = [];
    let cursor = 0;
    // `push` appends a segment and advances the shared timeline cursor. `dur` is in ms.
    const push = (type, dur, data) => {
      segments.push({ type, start: cursor, dur, end: cursor + dur, ...data });
      cursor += dur;
    };

    for (const ev of this.events) {
      const p = ev.payload || {};
      // Every action event carries the acting team index at `payload.team`.
      const t = typeof p.team === "number" ? p.team : null;

      if (ev.event_type === "MATCH_STARTED") {
        // Initial positions/health/stamina/rounds arrive here (flattened payload).
        push("state", 0, { patch: { positions: p.positions, health: p.health, stamina: p.stamina, rounds: p.rounds_won } });
      } else if (ev.event_type === "ROUND_STARTED") {
        // Reset both fighters (positions back to home, full health/stamina) and
        // clear the previous round's banner.
        push("state", 0, {
          patch: {
            positions: p.positions,
            health: p.health,
            stamina: p.stamina,
            rounds: p.rounds_won,
            currentRound: p.current_round,
            reset: true,
          },
        });
      } else if (ev.event_type === "MOVEMENT" && t !== null) {
        const from = p.from_pos;
        const to = p.to_pos;
        const action = p.move === "JUMP" ? "jump" : p.move === "HOLD" ? "idle" : "run";
        const dur = Math.max(120, Math.abs(to - from) * MOVE_MS_PER_UNIT);
        push("move", dur, { teamIndex: t, from, to, action });
      } else if (ev.event_type === "ATTACK" && t !== null) {
        const pose = ACTION_POSE[p.action] || "attack1";
        push("attack", ATTACK_DUR, { teamIndex: t, pose });
      } else if (ev.event_type === "HIT" && t !== null) {
        push("hit", HIT_DUR, { teamIndex: t });
      } else if (ev.event_type === "BLOCK" && t !== null) {
        push("block", BLOCK_DUR, { teamIndex: t });
      } else if (ev.event_type === "DODGE" && t !== null) {
        push("dodge", DODGE_DUR, { teamIndex: t });
      } else if (ev.event_type === "DAMAGE" && t !== null) {
        push("state", 0, { patch: { teamHealth: { teamIndex: t, health: p.health } } });
      } else if (ev.event_type === "STAMINA" && t !== null) {
        push("state", 0, { patch: { teamStamina: { teamIndex: t, stamina: p.stamina } } });
      } else if (ev.event_type === "ROUND_WON") {
        // Update the round score and show a transient "ROUND N — RED/BLUE" banner.
        // NOTE: do NOT set `winner` here — the match winner only comes at MATCH_FINISHED.
        push("state", 0, {
          patch: {
            rounds: p.rounds_won,
            banner: { text: `ROUND ${p.round} — ${TEAM_NAMES[p.winner]}`, round: p.round },
          },
        });
      } else if (ev.event_type === "MATCH_FINISHED") {
        push("state", 0, { patch: { winner: p.winner, rounds: p.rounds_won } });
      }
    }
    return segments;
  }

  applySegment(seg, local) {
    const st = this.state;
    if (seg.type === "move") {
      const f = st.fighters[seg.teamIndex];
      if (!f) return;
      // Interpolate the world position over the segment so the fighters glide
      // instead of teleporting. `local` is the 0..1 progress within the segment.
      f.x = seg.from + (seg.to - seg.from) * local;
      f.action = seg.action;
      f.actionStart = seg.start;
      f.actionDur = seg.dur;
    } else if (seg.type === "attack") {
      const f = st.fighters[seg.teamIndex];
      if (!f) return;
      f.action = seg.pose;
      f.actionStart = seg.start;
      f.actionDur = seg.dur;
      st.lastActor = seg.teamIndex;
    } else if (seg.type === "hit") {
      const f = st.fighters[seg.teamIndex];
      if (!f) return;
      f.action = "hit";
      f.actionStart = seg.start;
      f.actionDur = seg.dur;
      f.pulseUntil = seg.end; // renderer uses this for the flash + knockback
    } else if (seg.type === "block") {
      const f = st.fighters[seg.teamIndex];
      if (!f) return;
      f.action = "idle";
      f.actionStart = seg.start;
      f.actionDur = seg.dur;
      f.guardUntil = seg.end;
    } else if (seg.type === "dodge") {
      const f = st.fighters[seg.teamIndex];
      if (!f) return;
      f.action = "jump";
      f.actionStart = seg.start;
      f.actionDur = seg.dur;
      f.dodgeUntil = seg.end;
    } else if (seg.type === "state") {
      const p = seg.patch || {};
      if (p.reset) {
        // New round: reset both fighters to idle and clear all transient effects.
        st.fighters.forEach((f) => {
          f.action = "idle";
          f.actionStart = seg.start;
          f.actionDur = 400;
          f.pulseUntil = -1;
          f.guardUntil = -1;
          f.dodgeUntil = -1;
        });
        st.roundBanner = null;
      }
      if (Array.isArray(p.positions)) {
        st.fighters.forEach((f, i) => { f.x = p.positions[i] ?? f.x; });
      }
      if (Array.isArray(p.health)) {
        st.fighters.forEach((f, i) => { f.health = p.health[i] ?? f.health; });
      }
      if (Array.isArray(p.stamina)) {
        st.fighters.forEach((f, i) => { f.stamina = p.stamina[i] ?? f.stamina; });
      }
      if (Array.isArray(p.rounds)) st.rounds = p.rounds;
      if (typeof p.currentRound === "number") st.currentRound = p.currentRound;
      if (p.teamHealth) {
        const f = st.fighters[p.teamHealth.teamIndex];
        if (f) f.health = p.teamHealth.health;
      }
      if (p.teamStamina) {
        const f = st.fighters[p.teamStamina.teamIndex];
        if (f) f.stamina = p.teamStamina.stamina;
      }
      if (p.banner) {
        st.roundBanner = { text: p.banner.text, until: seg.start + ROUND_BANNER_MS };
      }
      if (typeof p.winner === "number") st.winner = p.winner;
    }
  }

  applyProgress(t) {
    // Rebuild the state from scratch and replay every segment whose start is <= t.
    // This keeps seeking deterministic (no accumulated drift).
    this.state = new MatchState(this.teams);
    for (const seg of this.segments) {
      if (seg.start > t) break;
      const local = Math.min(1, (t - seg.start) / Math.max(0.0001, seg.dur));
      this.applySegment(seg, local);
    }
    this.t = t;
    return this.state;
  }

  seek(t) {
    const clamped = Math.max(0, Math.min(this.duration, t));
    this.applyProgress(clamped);
    return clamped;
  }
}
