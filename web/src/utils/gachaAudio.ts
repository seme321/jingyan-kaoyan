/* ============================================================================
   PRTS GACHA WEB AUDIO SYNTHESIZER
   Zero-asset procedural Web Audio SFX for warp charge, burst, card reveal & UI
   ============================================================================ */

const MUTE_STORAGE_KEY = 'jingyan_gacha_muted';

type AudioRarity = 'R' | 'SR' | 'SSR';

let sharedCtx: AudioContext | null = null;
const activeStopCallbacks = new Set<() => void>();
const activeTimers = new Set<number>();

function getAudioContext(): AudioContext | null {
  try {
    if (typeof window === 'undefined') return null;
    const w = window as unknown as {
      AudioContext?: typeof AudioContext;
      webkitAudioContext?: typeof AudioContext;
    };
    const Ctor = w.AudioContext ?? w.webkitAudioContext;
    if (!Ctor) return null;
    if (!sharedCtx || sharedCtx.state === 'closed') {
      sharedCtx = new Ctor();
    }
    if (sharedCtx.state === 'suspended') {
      void sharedCtx.resume().catch(() => {
        // Ignore autoplay restriction errors
      });
    }
    return sharedCtx;
  } catch {
    return null;
  }
}

export function isGachaMuted(): boolean {
  try {
    return window.localStorage.getItem(MUTE_STORAGE_KEY) === '1';
  } catch {
    return false;
  }
}

export function setGachaMuted(muted: boolean): void {
  try {
    window.localStorage.setItem(MUTE_STORAGE_KEY, muted ? '1' : '0');
  } catch {
    // Ignore storage errors
  }
  if (muted) {
    stopWarpAudio();
  }
}

function registerNodeCleanup(node: AudioScheduledSourceNode, gain?: GainNode): void {
  const cleanup = () => {
    try {
      node.stop();
    } catch {
      // already stopped
    }
    try {
      node.disconnect();
      gain?.disconnect();
    } catch {
      // ignore disconnect errors
    }
    activeStopCallbacks.delete(cleanup);
  };
  activeStopCallbacks.add(cleanup);
  node.onended = () => {
    try {
      node.disconnect();
      gain?.disconnect();
    } catch {
      // ignore
    }
    activeStopCallbacks.delete(cleanup);
  };
}

function scheduleTimer(fn: () => void, delayMs: number): void {
  const id = window.setTimeout(() => {
    activeTimers.delete(id);
    fn();
  }, delayMs);
  activeTimers.add(id);
}

/**
 * Stop all ongoing warp/burst synthesized audio nodes and pending timers.
 */
export function stopWarpAudio(): void {
  try {
    for (const id of Array.from(activeTimers)) {
      window.clearTimeout(id);
      activeTimers.delete(id);
    }
    for (const stopFn of Array.from(activeStopCallbacks)) {
      stopFn();
    }
    activeStopCallbacks.clear();
  } catch {
    // non-blocking
  }
}

function playTone(
  ctx: AudioContext,
  options: {
    freq: number;
    endFreq?: number;
    type?: OscillatorType;
    gainPeak: number;
    attackSec?: number;
    durationSec: number;
    delaySec?: number;
  }
): void {
  try {
    const now = ctx.currentTime + (options.delaySec ?? 0);
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = options.type ?? 'sine';
    osc.frequency.setValueAtTime(options.freq, now);
    if (options.endFreq !== undefined) {
      osc.frequency.exponentialRampToValueAtTime(
        Math.max(20, options.endFreq),
        now + options.durationSec
      );
    }

    const attack = Math.min(options.attackSec ?? 0.02, options.durationSec * 0.4);
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.linearRampToValueAtTime(options.gainPeak, now + attack);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + options.durationSec);

    osc.connect(gain);
    gain.connect(ctx.destination);
    registerNodeCleanup(osc, gain);
    osc.start(now);
    osc.stop(now + options.durationSec + 0.03);
  } catch {
    // ignore
  }
}

/**
 * Play ~1.45s sci-fi hyperspace warp charge sound scaled by highest rarity.
 */
export function playWarpCharge(rarity: AudioRarity): void {
  stopWarpAudio();
  if (isGachaMuted()) return;
  const ctx = getAudioContext();
  if (!ctx) return;

  try {
    const now = ctx.currentTime;
    const duration = 1.45;

    // 1. Deep-sea sub-bass rumble / turbine sweep
    playTone(ctx, {
      freq: 62,
      endFreq: rarity === 'SSR' ? 148 : rarity === 'SR' ? 124 : 98,
      type: 'triangle',
      gainPeak: 0.08,
      attackSec: 0.18,
      durationSec: duration,
    });

    // 2. Filtered noise hyperspace wind
    const sampleRate = ctx.sampleRate;
    const bufferLen = Math.floor(sampleRate * duration);
    const noiseBuf = ctx.createBuffer(1, bufferLen, sampleRate);
    const data = noiseBuf.getChannelData(0);
    for (let i = 0; i < bufferLen; i++) {
      data[i] = Math.random() * 2 - 1;
    }
    const noiseSrc = ctx.createBufferSource();
    noiseSrc.buffer = noiseBuf;

    const filter = ctx.createBiquadFilter();
    filter.type = 'bandpass';
    filter.Q.setValueAtTime(2.6, now);
    filter.frequency.setValueAtTime(240, now);
    filter.frequency.exponentialRampToValueAtTime(
      rarity === 'SSR' ? 2400 : rarity === 'SR' ? 1700 : 1200,
      now + duration
    );

    const noiseGain = ctx.createGain();
    noiseGain.gain.setValueAtTime(0.0001, now);
    noiseGain.gain.linearRampToValueAtTime(0.055, now + 0.35);
    noiseGain.gain.linearRampToValueAtTime(0.09, now + 1.2);
    noiseGain.gain.exponentialRampToValueAtTime(0.0001, now + duration);

    noiseSrc.connect(filter);
    filter.connect(noiseGain);
    noiseGain.connect(ctx.destination);
    registerNodeCleanup(noiseSrc, noiseGain);
    noiseSrc.start(now);
    noiseSrc.stop(now + duration + 0.03);

    // 3. Rising carrier pitch scaled by rarity
    const peakFreq = rarity === 'SSR' ? 1046.5 : rarity === 'SR' ? 820 : 580;
    playTone(ctx, {
      freq: 210,
      endFreq: peakFreq,
      type: 'sine',
      gainPeak: 0.065,
      attackSec: 0.25,
      durationSec: duration,
    });

    // 4. SR fifth harmony / SSR crystalline shimmer ticks
    if (rarity === 'SR' || rarity === 'SSR') {
      playTone(ctx, {
        freq: 315,
        endFreq: peakFreq * 1.5,
        type: 'sine',
        gainPeak: 0.032,
        attackSec: 0.45,
        durationSec: duration - 0.15,
        delaySec: 0.15,
      });
    }

    if (rarity === 'SSR') {
      const shimmerFreqs = [1318.5, 1567.98, 2093.0];
      shimmerFreqs.forEach((f, idx) => {
        scheduleTimer(() => {
          if (isGachaMuted()) return;
          const c = getAudioContext();
          if (!c) return;
          playTone(c, {
            freq: f,
            type: 'sine',
            gainPeak: 0.028,
            attackSec: 0.02,
            durationSec: 0.36,
          });
        }, 680 + idx * 190);
      });
    }
  } catch {
    // ignore
  }
}

/**
 * Play burst chord when warp reaches whiteout peak.
 */
export function playWarpBurst(rarity: AudioRarity): void {
  if (isGachaMuted()) return;
  const ctx = getAudioContext();
  if (!ctx) return;

  try {
    if (rarity === 'R') {
      // Crisp cyan crystal dual-tone (C5 + G5)
      playTone(ctx, { freq: 523.25, type: 'sine', gainPeak: 0.09, durationSec: 0.45 });
      playTone(ctx, { freq: 783.99, type: 'triangle', gainPeak: 0.06, durationSec: 0.52, delaySec: 0.04 });
      return;
    }

    if (rarity === 'SR') {
      // Radiant violet ascending 4-note arpeggio (D5 -> F#5 -> A5 -> D6)
      const notes = [587.33, 739.99, 880.0, 1174.66];
      notes.forEach((freq, idx) => {
        playTone(ctx, {
          freq,
          type: idx === 3 ? 'triangle' : 'sine',
          gainPeak: idx === 3 ? 0.09 : 0.07,
          attackSec: 0.015,
          durationSec: 0.58,
          delaySec: idx * 0.055,
        });
      });
      return;
    }

    // SSR: Golden harp / starlight cascade (C5 -> E5 -> G5 -> B5 -> D6 -> G6) + warm sub pad
    playTone(ctx, {
      freq: 130.81,
      type: 'triangle',
      gainPeak: 0.075,
      attackSec: 0.03,
      durationSec: 1.15,
    });
    const ssrNotes = [523.25, 659.25, 783.99, 987.77, 1174.66, 1567.98];
    ssrNotes.forEach((freq, idx) => {
      playTone(ctx, {
        freq,
        type: 'sine',
        gainPeak: idx >= 4 ? 0.08 : 0.065,
        attackSec: 0.012,
        durationSec: 0.9 - idx * 0.05,
        delaySec: idx * 0.045,
      });
    });
  } catch {
    // ignore
  }
}

/**
 * Play crisp crystal chime when stepping through card reveals.
 */
export function playCardReveal(rarity: AudioRarity, isNew: boolean): void {
  if (isGachaMuted()) return;
  const ctx = getAudioContext();
  if (!ctx) return;

  try {
    const base = rarity === 'SSR' ? 783.99 : rarity === 'SR' ? 659.25 : 523.25;
    playTone(ctx, {
      freq: base,
      type: 'sine',
      gainPeak: 0.065,
      attackSec: 0.01,
      durationSec: 0.34,
    });
    playTone(ctx, {
      freq: base * 1.5,
      type: 'triangle',
      gainPeak: 0.04,
      attackSec: 0.01,
      durationSec: 0.42,
      delaySec: 0.035,
    });
    if (isNew) {
      playTone(ctx, {
        freq: base * 2,
        type: 'sine',
        gainPeak: 0.048,
        attackSec: 0.012,
        durationSec: 0.56,
        delaySec: 0.075,
      });
    }
  } catch {
    // ignore
  }
}

/**
 * Subtle mechanical terminal tick for switching banners / previewing operators.
 */
export function playUiTick(): void {
  if (isGachaMuted()) return;
  const ctx = getAudioContext();
  if (!ctx) return;

  try {
    playTone(ctx, {
      freq: 920,
      endFreq: 540,
      type: 'triangle',
      gainPeak: 0.038,
      attackSec: 0.004,
      durationSec: 0.055,
    });
  } catch {
    // ignore
  }
}
