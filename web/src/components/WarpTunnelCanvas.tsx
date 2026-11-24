import React, { useEffect, useRef } from 'react';

export interface WarpTunnelCanvasProps {
  highestRarity: 'R' | 'SR' | 'SSR';
  reducedMotion: boolean;
  onBurstPeak: () => void;
}

interface StarStreak {
  angle: number;
  baseRadius: number;
  speed: number;
  length: number;
  thickness: number;
  hueShift: number;
  alpha: number;
}

interface FloatingGlyph {
  angle: number;
  dist: number;
  speed: number;
  size: number;
  rot: number;
}

const RARITY_COLORS: Record<
  'R' | 'SR' | 'SSR',
  { core: string; glow: string; secondary: string; bgTint: string }
> = {
  R: {
    core: '#38d2fc',
    glow: 'rgba(34, 199, 242, 0.85)',
    secondary: '#93c5fd',
    bgTint: 'rgba(18, 66, 108, 0.45)',
  },
  SR: {
    core: '#c084fc',
    glow: 'rgba(167, 139, 250, 0.9)',
    secondary: '#38d2fc',
    bgTint: 'rgba(62, 34, 112, 0.48)',
  },
  SSR: {
    core: '#fbbf24',
    glow: 'rgba(244, 196, 48, 0.95)',
    secondary: '#fef08a',
    bgTint: 'rgba(108, 72, 16, 0.5)',
  },
};

function drawDiamond(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  rx: number,
  ry: number
): void {
  ctx.beginPath();
  ctx.moveTo(cx, cy - ry);
  ctx.lineTo(cx + rx, cy);
  ctx.lineTo(cx, cy + ry);
  ctx.lineTo(cx - rx, cy);
  ctx.closePath();
}

export const WarpTunnelCanvas: React.FC<WarpTunnelCanvasProps> = ({
  highestRarity,
  reducedMotion,
  onBurstPeak,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const onBurstPeakRef = useRef(onBurstPeak);
  onBurstPeakRef.current = onBurstPeak;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      const fallbackId = window.setTimeout(() => onBurstPeakRef.current(), 220);
      return () => window.clearTimeout(fallbackId);
    }

    let rafId = 0;
    let done = false;
    let width = 0;
    let height = 0;
    let dpr = 1;

    const resize = () => {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = Math.max(320, window.innerWidth);
      height = Math.max(320, window.innerHeight);
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
    };
    resize();
    window.addEventListener('resize', resize);

    const palette = RARITY_COLORS[highestRarity];

    if (reducedMotion) {
      // Calm static/gentle prism glow without rapid flashing
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const cx = width * 0.5;
      const cy = height * 0.5;
      const maxR = Math.hypot(cx, cy);
      const bg = ctx.createRadialGradient(cx, cy, 10, cx, cy, maxR);
      bg.addColorStop(0, palette.bgTint);
      bg.addColorStop(0.5, '#091224');
      bg.addColorStop(1, '#04070e');
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, width, height);

      ctx.save();
      ctx.strokeStyle = palette.core;
      ctx.lineWidth = 2;
      ctx.shadowColor = palette.glow;
      ctx.shadowBlur = 24;
      drawDiamond(ctx, cx, cy, 46, 62);
      ctx.stroke();
      ctx.restore();

      const timer = window.setTimeout(() => {
        if (!done) {
          done = true;
          onBurstPeakRef.current();
        }
      }, 320);
      return () => {
        window.clearTimeout(timer);
        window.removeEventListener('resize', resize);
      };
    }

    // Generate deterministic-feeling star streaks & prism motes
    const streaks: StarStreak[] = Array.from({ length: 136 }, (_, idx) => ({
      angle: (idx / 136) * Math.PI * 2 + (Math.random() - 0.5) * 0.14,
      baseRadius: 12 + Math.random() * 140,
      speed: 0.65 + Math.random() * 1.45,
      length: 28 + Math.random() * 95,
      thickness: 0.8 + Math.random() * 2.1,
      hueShift: Math.random(),
      alpha: 0.35 + Math.random() * 0.65,
    }));

    const motes: FloatingGlyph[] = Array.from({ length: 28 }, () => ({
      angle: Math.random() * Math.PI * 2,
      dist: 40 + Math.random() * 280,
      speed: 0.4 + Math.random() * 0.9,
      size: 3 + Math.random() * 5,
      rot: Math.random() * Math.PI,
    }));

    const TOTAL_MS = 1650;
    let startTs: number | null = null;

    const frame = (now: number) => {
      if (startTs === null) {
        startTs = now;
      }
      const elapsed = Math.max(0, now - startTs);
      const t = Math.min(1, Math.max(0, elapsed / TOTAL_MS));

      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      // Subtle camera shake during high-rarity slit breach (t in [0.54, 0.88])
      let shakeX = 0;
      let shakeY = 0;
      if (t > 0.56 && t < 0.88) {
        const shakeMag = highestRarity === 'SSR' ? 3.2 : highestRarity === 'SR' ? 1.8 : 0.8;
        const ramp = Math.sin(((t - 0.56) / 0.32) * Math.PI);
        shakeX = (Math.random() - 0.5) * 2 * shakeMag * ramp;
        shakeY = (Math.random() - 0.5) * 2 * shakeMag * ramp;
      }

      const cx = width * 0.5 + shakeX;
      const cy = height * 0.5 + shakeY;
      const maxR = Math.hypot(width, height) * 0.62;

      // 1. Deep-sea cosmic base backdrop
      const bgGrad = ctx.createRadialGradient(cx, cy, 8, cx, cy, maxR);
      if (t < 0.54) {
        bgGrad.addColorStop(0, '#0f2442');
        bgGrad.addColorStop(0.45, '#071020');
        bgGrad.addColorStop(1, '#03060d');
      } else {
        bgGrad.addColorStop(0, palette.bgTint);
        bgGrad.addColorStop(0.52, '#071124');
        bgGrad.addColorStop(1, '#03060d');
      }
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, width, height);

      // 2. Rotating PRTS polar blueprint coordinate rings
      const ringProgress = Math.min(1, t / 0.85);
      const ringScale = 0.65 + ringProgress * 0.9;
      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(t * 0.85);
      ctx.strokeStyle =
        t > 0.54 ? `rgba(255,255,255,0.18)` : `rgba(34, 199, 242, ${0.22 * (1 - t * 0.4)})`;
      ctx.lineWidth = 1.1;
      ctx.setLineDash([6, 12]);
      for (let r = 110; r <= 330; r += 110) {
        ctx.beginPath();
        ctx.arc(0, 0, r * ringScale, 0, Math.PI * 2);
        ctx.stroke();
      }
      ctx.rotate(-t * 1.45);
      ctx.strokeStyle = t > 0.54 ? palette.glow : 'rgba(56, 210, 252, 0.25)';
      ctx.setLineDash([2, 16]);
      ctx.beginPath();
      ctx.arc(0, 0, 175 * ringScale, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();

      // 3. Radial hyperspace starlight streaks accelerating outward
      const accel = Math.pow(t, 1.9);
      const streakMix = Math.max(0, (t - 0.42) / 0.58);
      ctx.save();
      ctx.globalCompositeOperation = 'lighter';
      for (const s of streaks) {
        const travel = (s.baseRadius + accel * maxR * 1.25 * s.speed) % (maxR * 1.12);
        const len = s.length * (0.45 + accel * 2.5) * s.speed;
        const x1 = cx + Math.cos(s.angle) * travel;
        const y1 = cy + Math.sin(s.angle) * travel;
        const x2 = cx + Math.cos(s.angle) * (travel + len);
        const y2 = cy + Math.sin(s.angle) * (travel + len);

        const grad = ctx.createLinearGradient(x1, y1, x2, y2);
        grad.addColorStop(0, 'rgba(255, 255, 255, 0)');
        if (streakMix < 0.25) {
          grad.addColorStop(0.55, `rgba(56, 210, 252, ${s.alpha * 0.75})`);
          grad.addColorStop(1, `rgba(225, 248, 255, ${s.alpha})`);
        } else {
          const useRarity = s.hueShift > 0.35;
          grad.addColorStop(0.5, useRarity ? palette.glow : 'rgba(56, 210, 252, 0.78)');
          grad.addColorStop(1, useRarity ? '#ffffff' : palette.secondary);
        }

        ctx.strokeStyle = grad;
        ctx.lineWidth = s.thickness * (1 + accel * 0.85);
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
      }

      // Floating diamond motes flying past
      for (const m of motes) {
        const dist = (m.dist + accel * maxR * 0.9 * m.speed) % (maxR * 0.95);
        const mx = cx + Math.cos(m.angle) * dist;
        const my = cy + Math.sin(m.angle) * dist;
        const sz = m.size * (0.5 + dist / maxR);
        ctx.save();
        ctx.translate(mx, my);
        ctx.rotate(m.rot + t * 2.5);
        ctx.fillStyle = t > 0.54 ? palette.core : '#7dd3fc';
        ctx.globalAlpha = 0.55;
        drawDiamond(ctx, 0, 0, sz, sz * 1.25);
        ctx.fill();
        ctx.restore();
      }
      ctx.restore();

      // 4. Center PRTS Prism Gate (0..0.54 charge -> 0.54..0.86 light leak -> 0.86..1.0 burst)
      ctx.save();
      ctx.globalCompositeOperation = 'lighter';
      const beaconScale = t < 0.54 ? 0.5 + (t / 0.54) * 0.75 : 1.25 + (t - 0.54) * 2.6;
      const rx = 38 * beaconScale;
      const ry = 54 * beaconScale;

      // Ambient center core bloom
      const coreRadius = (48 + t * 240) * (t > 0.54 ? 1 + (t - 0.54) * 2.2 : 1);
      const coreGrad = ctx.createRadialGradient(cx, cy, 2, cx, cy, coreRadius);
      if (t < 0.54) {
        coreGrad.addColorStop(0, 'rgba(220, 250, 255, 0.95)');
        coreGrad.addColorStop(0.35, 'rgba(34, 199, 242, 0.55)');
        coreGrad.addColorStop(1, 'rgba(34, 199, 242, 0)');
      } else {
        coreGrad.addColorStop(0, 'rgba(255, 255, 255, 1)');
        coreGrad.addColorStop(0.28, palette.glow);
        coreGrad.addColorStop(0.65, palette.bgTint);
        coreGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
      }
      ctx.fillStyle = coreGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, coreRadius, 0, Math.PI * 2);
      ctx.fill();

      // Double chamfered prism gate lines
      if (t < 0.92) {
        const gateAlpha = Math.max(0, 1 - Math.max(0, t - 0.78) / 0.14);
        ctx.globalAlpha = gateAlpha;
        ctx.strokeStyle = t > 0.54 ? palette.core : '#38d2fc';
        ctx.lineWidth = t > 0.54 ? 2.6 : 1.8;
        ctx.shadowColor = t > 0.54 ? palette.glow : '#22c7f2';
        ctx.shadowBlur = t > 0.54 ? 26 : 14;
        drawDiamond(ctx, cx, cy, rx, ry);
        ctx.stroke();

        ctx.strokeStyle = 'rgba(255,255,255,0.75)';
        ctx.lineWidth = 1.1;
        drawDiamond(ctx, cx, cy, rx * 0.68, ry * 0.68);
        ctx.stroke();
      }

      // Phase B: Door-slit light leak & 4-point starburst spikes
      if (t >= 0.52) {
        const leakP = Math.min(1, (t - 0.52) / 0.36);
        const slitW = width * (0.28 + leakP * 0.95);
        const slitH = 3 + leakP * (highestRarity === 'SSR' ? 42 : highestRarity === 'SR' ? 28 : 18);

        const slitGrad = ctx.createLinearGradient(cx - slitW * 0.5, cy, cx + slitW * 0.5, cy);
        slitGrad.addColorStop(0, 'rgba(255,255,255,0)');
        slitGrad.addColorStop(0.35, palette.core);
        slitGrad.addColorStop(0.5, '#ffffff');
        slitGrad.addColorStop(0.65, palette.core);
        slitGrad.addColorStop(1, 'rgba(255,255,255,0)');

        ctx.fillStyle = slitGrad;
        ctx.globalAlpha = 0.88;
        ctx.beginPath();
        ctx.ellipse(cx, cy, slitW * 0.5, slitH * 0.5, 0, 0, Math.PI * 2);
        ctx.fill();

        // Vertical cross flare spike (prominent for SR & SSR)
        if (highestRarity !== 'R') {
          const vLen = height * (0.35 + leakP * 0.65);
          const vGrad = ctx.createLinearGradient(cx, cy - vLen * 0.5, cx, cy + vLen * 0.5);
          vGrad.addColorStop(0, 'rgba(255,255,255,0)');
          vGrad.addColorStop(0.5, '#ffffff');
          vGrad.addColorStop(1, 'rgba(255,255,255,0)');
          ctx.fillStyle = vGrad;
          ctx.globalAlpha = 0.65 * leakP;
          ctx.beginPath();
          ctx.ellipse(
            cx,
            cy,
            highestRarity === 'SSR' ? 12 : 7,
            vLen * 0.5,
            0,
            0,
            Math.PI * 2
          );
          ctx.fill();
        }
      }
      ctx.restore();

      // 5. Phase C: Platinum whiteout flash peak (t in [0.85, 1.0])
      if (t >= 0.84) {
        const flashP = Math.min(1, (t - 0.84) / 0.16);
        const eased = flashP * flashP;
        const whiteGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, maxR * (0.35 + flashP * 1.1));
        whiteGrad.addColorStop(0, `rgba(255, 255, 255, ${Math.min(1, 0.75 + eased * 0.3)})`);
        whiteGrad.addColorStop(0.55, `rgba(244, 249, 255, ${eased * 0.96})`);
        whiteGrad.addColorStop(1, `rgba(235, 245, 255, ${eased * 0.9})`);
        ctx.fillStyle = whiteGrad;
        ctx.fillRect(0, 0, width, height);
      }

      if (t < 1) {
        rafId = window.requestAnimationFrame(frame);
      } else if (!done) {
        done = true;
        onBurstPeakRef.current();
      }
    };

    rafId = window.requestAnimationFrame(frame);

    return () => {
      window.cancelAnimationFrame(rafId);
      window.removeEventListener('resize', resize);
    };
  }, [highestRarity, reducedMotion]);

  return <canvas ref={canvasRef} className="warp-tunnel-canvas" aria-hidden="true" />;
};
