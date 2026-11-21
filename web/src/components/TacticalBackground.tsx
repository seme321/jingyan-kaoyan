import React from 'react';
import { useStudy } from '../context/StudyContext';
import { useData } from '../context/DataContext';

interface FormulaToken {
  code?: string;
  formula: string;
  accent?: 'cyan' | 'yellow';
}

const FORMULA_TRACKS: Array<{
  id: string;
  direction: 'left' | 'right';
  durationSec: number;
  topPct: number;
  items: FormulaToken[];
}> = [
  {
    id: 'energy',
    direction: 'left',
    durationSec: 84,
    topPct: 16,
    items: [
      { code: 'EQ.01', formula: 'z₁ + p₁/γ + α₁v₁²/(2g) = z₂ + p₂/γ + α₂v₂²/(2g) + h_w', accent: 'cyan' },
      { formula: 'H = z + p/(ρg) + v²/(2g)' },
      { code: 'E_s', formula: 'E_s = h + αQ²/(2gA²)', accent: 'yellow' },
      { formula: 'BERNOULLI // ENERGY GRADE LINE (EGL)' },
      { formula: '∂u/∂x + ∂v/∂y + ∂w/∂z = 0' },
    ],
  },
  {
    id: 'hydrostatics',
    direction: 'right',
    durationSec: 96,
    topPct: 33,
    items: [
      { code: 'EQ.02', formula: 'p = p₀ + ρgh', accent: 'cyan' },
      { formula: 'P = ρ g h_c A' },
      { formula: 'y_D = y_c + I_c / (y_c A)' },
      { code: 'MOMENTUM', formula: '∑F = ρQ(β₂v₂ − β₁v₁)', accent: 'yellow' },
      { formula: 'P_z = ρ g V_p  //  PRESSURE PRISM' },
      { formula: 'dp/dz = −γ' },
    ],
  },
  {
    id: 'pipe',
    direction: 'left',
    durationSec: 108,
    topPct: 51,
    items: [
      { code: 'DARCY', formula: 'h_f = λ (l / d) (v² / 2g)', accent: 'cyan' },
      { code: 'RE_CR', formula: 'Re = v d / ν = 2320', accent: 'yellow' },
      { formula: 'τ = μ (du / dy) = ρν (du / dy)' },
      { formula: '1/√λ = −2 lg(Δ / 3.7d + 2.51 / (Re√λ))' },
      { formula: 'h_j = ζ v² / (2g)' },
      { formula: 'λ = 64 / Re  //  LAMINAR PIPE FLOW' },
    ],
  },
  {
    id: 'channel',
    direction: 'right',
    durationSec: 92,
    topPct: 68,
    items: [
      { code: 'MANNING', formula: 'v = C√(Ri) = (1/n) R^(2/3) i^(1/2)', accent: 'cyan' },
      { code: 'FR=1', formula: 'Fr = v / √(gh)', accent: 'yellow' },
      { formula: 'dh/ds = (i − J) / (1 − Fr²)' },
      { formula: 'h_c = ∛(αq² / g)' },
      { formula: 'h₂/h₁ = ½(√(1 + 8Fr₁²) − 1)  //  HYDRAULIC JUMP' },
    ],
  },
  {
    id: 'seepage',
    direction: 'left',
    durationSec: 102,
    topPct: 84,
    items: [
      { code: 'LAPLACE', formula: '∇²φ = ∂²φ/∂x² + ∂²φ/∂y² = 0', accent: 'cyan' },
      { formula: 'v = k J  //  DARCY SEEPAGE LAW' },
      { code: 'HAMMER', formula: 'Δp = ρ c Δv', accent: 'yellow' },
      { formula: 'Q = m b √(2g) H₀^(3/2)' },
      { formula: 'λ_v = λ_L^(1/2)  ·  λ_Q = λ_L^(5/2)  //  FROUDE SIMILARITY' },
    ],
  },
];

const LEFT_RULER_TICKS = ['+40.0m', '+30.0m', '+20.0m', '+10.0m', '00.0m', '−10.0m'];
const RIGHT_TELEMETRY = ['EGL // H₀', 'HGL // z+p/γ', 'Re 2320', 'Fr 1.00', '∇²φ = 0', 'g 9.81'];

export const TacticalBackground: React.FC = () => {
  const { state } = useStudy();
  const { currentCourse } = useData();
  const animated = state.settings.animatedBg !== false;

  return (
    <div className={`tactical-bg ${animated ? 'is-animated' : 'is-static'}`} aria-hidden="true">
      {/* Layer 1: Ambient Hydraulic Streamlines & Potential Flow-Net SVG */}
      <svg className="tactical-flowlines" viewBox="0 0 1440 900" preserveAspectRatio="none">
        <defs>
          <linearGradient id="fl-pulse-cyan" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="var(--primary)" stopOpacity="0" />
            <stop offset="50%" stopColor="var(--primary)" stopOpacity="0.95" />
            <stop offset="100%" stopColor="var(--primary)" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="fl-pulse-yellow" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="var(--yellow)" stopOpacity="0" />
            <stop offset="50%" stopColor="var(--yellow)" stopOpacity="0.9" />
            <stop offset="100%" stopColor="var(--yellow)" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Flow-net equipotential corner arcs */}
        <g className="flownet-arcs">
          <circle cx="1440" cy="0" r="240" />
          <circle cx="1440" cy="0" r="360" />
          <circle cx="1440" cy="0" r="480" />
          <circle cx="0" cy="900" r="220" />
          <circle cx="0" cy="900" r="340" />
        </g>

        {/* Base steady streamlines */}
        <path className="fl-solid" d="M-40 140 C 260 90, 520 235, 880 155 C 1140 100, 1320 190, 1480 125" />
        <path className="fl-drift" d="M-40 315 C 310 265, 610 395, 960 305 C 1180 250, 1340 330, 1480 280" />
        <path className="fl-drift slow" d="M-40 500 C 290 455, 630 585, 980 485 C 1210 420, 1350 510, 1480 465" />
        <path className="fl-yellow" d="M-40 660 C 320 620, 640 755, 1020 645 C 1220 590, 1360 665, 1480 625" />
        <path className="fl-solid" d="M-40 810 C 280 770, 580 885, 960 795 C 1210 735, 1360 815, 1480 770" />

        {/* Luminous tracer pulses gliding along streamlines */}
        <path
          className="fl-tracer cyan"
          d="M-40 315 C 310 265, 610 395, 960 305 C 1180 250, 1340 330, 1480 280"
        />
        <path
          className="fl-tracer cyan delay-1"
          d="M-40 500 C 290 455, 630 585, 980 485 C 1210 420, 1350 510, 1480 465"
        />
        <path
          className="fl-tracer yellow delay-2"
          d="M-40 660 C 320 620, 640 755, 1020 645 C 1220 590, 1360 665, 1480 625"
        />
      </svg>

      {/* Layer 2: Scrolling Hydraulics Formula Telemetry Ribbons */}
      <div className="formula-ribbon-field">
        {FORMULA_TRACKS.map((track) => (
          <div
            key={track.id}
            className={`formula-ribbon dir-${track.direction}`}
            style={{
              top: `${track.topPct}%`,
              ['--ribbon-dur' as string]: `${track.durationSec}s`,
            }}
          >
            <div className="formula-ribbon-inner">
              {[0, 1].map((dup) => (
                <div key={dup} className="formula-ribbon-group">
                  {track.items.map((item, i) => (
                    <span key={i} className="formula-ribbon-item">
                      {item.code && (
                        <span className={`fr-code ${item.accent ?? ''}`}>[{item.code}]</span>
                      )}
                      <span className={`fr-expr ${item.accent ? `hl-${item.accent}` : ''}`}>
                        {item.formula}
                      </span>
                      <span className="fr-sep">//</span>
                    </span>
                  ))}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Layer 3: Wide-Viewport Side Elevation Rulers & Tactical Coordinate Rail */}
      <div className="bg-side-ruler left">
        <span className="ruler-head">HEAD [m]</span>
        <div className="ruler-ticks">
          {LEFT_RULER_TICKS.map((label) => (
            <span key={label} className="ruler-tick">
              <i />
              {label}
            </span>
          ))}
        </div>
        <span className="ruler-foot">{currentCourse.id.toUpperCase()}</span>
      </div>

      <div className="bg-side-ruler right">
        <span className="ruler-head">FLUID.OS</span>
        <div className="ruler-ticks">
          {RIGHT_TELEMETRY.map((label) => (
            <span key={label} className="ruler-tick">
              {label}
              <i />
            </span>
          ))}
        </div>
        <span className="ruler-foot">SYS.ONLINE</span>
      </div>
    </div>
  );
};
