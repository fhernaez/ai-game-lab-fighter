/*
 * replay.js — deterministic event-log → timeline engine for the fight.
 *
 * Compiles the fight's event stream into animation segments with cumulative start
 * times, then renders any point in time by replaying segments up to t. This gives
 * play / pause / seek / speed with a single applyProgress(t) method.
 */

import { TEAM_NAMES } from "./arena.js";

// Timing constants (ms).
const MOVE_MS_PER_UNIT = 22;  // how long a 1-unit footwork step takes to animate
const ATTACK_DUR = 460;       // duration of a kick animation
const HIT_DUR = 380;          // duration of the "take a hit" reaction
const BLOCK_DUR = 420;        // duration of a block guard
const DODGE_DUR = 420;        // duration of a dodge

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
    this.lastActor = null;

    teams.forEach((team, ti) => {
      this.fighters.push({
        teamIndex: ti,
        teamName: team.name,
        label: TEAM_NAMES[ti],
        x: HOME[ti],
        action: "idle",
        actionStart: 0,
        actionDur: 400,
        health: 100,
        stamina: 100,
        pulseUntil: -1,
        guardUntil: -1,
        dodgeUntil: -1,
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
    const push = (type, dur, data) => {
      segments.push({ type, start: cursor, dur, end: cursor + dur, ...data });
      cursor += dur;
    };

    for (const ev of this.events) {
      const p = ev.payload || {};
      const t = typeof p.team === "number" ? p.team : null;

      if (ev.event_type === "MATCH_STARTED") {
        push("state", 0, { patch: { positions: p.positions, health: p.health, stamina: p.stamina, rounds: p.rounds_won } });
      } else if (ev.event_type === "ROUND_STARTED") {
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
        push("state", 0, { patch: { rounds: p.rounds_won, winner: p.winner } });
      } else if (ev.event_type === "MATCH_FINISHED") {
        push("state", 0, { patch: { winner: p.winner, rounds: p.rounds_won } });
      }
    }
    return segments;
  }

  applySegment(seg) {
    const st = this.state;
    if (seg.type === "move") {
      const f = st.fighters[seg.teamIndex];
      if (!f) return;
      f.x = seg.to;
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
      f.pulseUntil = seg.end;
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
        st.fighters.forEach((f) => {
          f.action = "idle";
          f.actionStart = seg.start;
          f.actionDur = 400;
          f.pulseUntil = -1;
          f.guardUntil = -1;
          f.dodgeUntil = -1;
        });
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
      if (typeof p.winner === "number") st.winner = p.winner;
    }
  }

  applyProgress(t) {
    this.state = new MatchState(this.teams);
    for (const seg of this.segments) {
      if (seg.start > t) break;
      this.applySegment(seg);
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
