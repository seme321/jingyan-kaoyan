import React, { useRef, useState } from 'react';

export interface LightConeCardProps {
  name: string;
  code?: string;
  subtitle?: string;
  variantLabel: string;
  rarity: 'R' | 'SR' | 'SSR' | 'SP';
  color: string;
  sprite: string;
  tags?: string[];
  isNew?: boolean;
  isEquipped?: boolean;
  isLocked?: boolean;
  bloomOnMount?: boolean;
  size?: 'compact' | 'md' | 'hero';
  interactive?: boolean;
  footer?: React.ReactNode;
  onClick?: () => void;
  className?: string;
}

const STAR_COUNTS: Record<'R' | 'SR' | 'SSR' | 'SP', number> = {
  R: 3,
  SR: 4,
  SSR: 5,
  SP: 5,
};

export const LightConeCard: React.FC<LightConeCardProps> = ({
  name,
  code,
  subtitle,
  variantLabel,
  rarity,
  color,
  sprite,
  tags,
  isNew = false,
  isEquipped = false,
  isLocked = false,
  bloomOnMount = false,
  size = 'md',
  interactive = true,
  footer,
  onClick,
  className = '',
}) => {
  const stageRef = useRef<HTMLDivElement | null>(null);
  const [tilt, setTilt] = useState({ rx: 0, ry: 0, mx: 50, my: 50, hovering: false });

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!interactive || e.pointerType !== 'mouse' || !stageRef.current) return;
    const rect = stageRef.current.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    const px = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width));
    const py = Math.min(1, Math.max(0, (e.clientY - rect.top) / rect.height));
    const ry = (px - 0.5) * 24; // ±12deg
    const rx = (0.5 - py) * 20; // ±10deg
    setTilt({
      rx: Number(rx.toFixed(2)),
      ry: Number(ry.toFixed(2)),
      mx: Number((px * 100).toFixed(1)),
      my: Number((py * 100).toFixed(1)),
      hovering: true,
    });
  };

  const handlePointerLeave = () => {
    if (!interactive) return;
    setTilt({ rx: 0, ry: 0, mx: 50, my: 50, hovering: false });
  };

  const starCount = STAR_COUNTS[rarity];
  const displayVariantLabel =
    size === 'compact' ? variantLabel.split('·')[0].trim() : variantLabel;

  const stageStyle = {
    '--card-accent': color || '#22c7f2',
    '--rx': `${tilt.rx}deg`,
    '--ry': `${tilt.ry}deg`,
    '--mx': `${tilt.mx}%`,
    '--my': `${tilt.my}%`,
  } as React.CSSProperties;

  return (
    <div
      ref={stageRef}
      className={`lc-stage size-${size} rarity-${rarity} ${tilt.hovering ? 'is-hovering' : ''} ${
        onClick ? 'is-clickable' : ''
      } ${footer ? 'has-footer' : ''} ${className}`.trim()}
      style={stageStyle}
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
    >
      <div className="lc-card-3d">
        {/* Layer 0 & 1: Stacked translucent acrylic slabs for physical Light Cone depth */}
        <div className="lc-slab-back" aria-hidden="true" />
        <div className="lc-slab-mid" aria-hidden="true" />

        {/* Layer 2: Clipped artwork plate + volumetric pillars + aurora + holo foil */}
        <div className="lc-face">
          <div className="lc-face-clip">
            <div className="lc-blueprint-grid" aria-hidden="true" />
            <div className="lc-pillars" aria-hidden="true">
              <span className="lc-pillar p1" />
              <span className="lc-pillar p2" />
              <span className="lc-pillar p3" />
            </div>
            <div className="lc-aurora" aria-hidden="true" />
            <div className="lc-motes" aria-hidden="true">
              <span className="lc-mote m1" />
              <span className="lc-mote m2" />
              <span className="lc-mote m3" />
              <span className="lc-mote m4" />
            </div>

            <div className="lc-sprite-wrap">
              <img
                src={sprite}
                alt={isLocked ? `${name} 未解锁` : `${name} ${variantLabel}`}
                className={`lc-sprite ${isLocked ? 'locked-silhouette' : ''}`}
                loading="lazy"
              />
            </div>

            <div className="lc-holo" aria-hidden="true" />
            <div className="lc-glare" aria-hidden="true" />
            {bloomOnMount && <div className="lc-bloom-wash" aria-hidden="true" />}
          </div>

          {onClick && (
            <button
              type="button"
              className="lc-card-hitarea"
              onClick={onClick}
              aria-label={`查看 ${name} ${variantLabel} 特写`}
            />
          )}
        </div>

        {/* Layer 3: Floating PRTS x Light Cone HUD Chrome */}
        <div className="lc-chrome">
          <div className="lc-top-bar">
            <div className="lc-top-left">
              <span className={`rarity-tag rarity-${rarity}`}>{rarity}</span>
              {code && size !== 'compact' && <span className="lc-code">{code}</span>}
              <span className="lc-stars" aria-label={`${starCount} 星`}>
                {Array.from({ length: starCount }).map((_, idx) => (
                  <span key={idx} className="lc-star-glyph">
                    ✦
                  </span>
                ))}
              </span>
            </div>
            <div className="lc-top-right">
              {isNew && <span className="new-tag">NEW!</span>}
              {isEquipped && <span className="equipped-tag">看板中</span>}
            </div>
          </div>

          <div className="lc-nameplate">
            <div className="lc-name-row">
              <strong className="lc-name">{name}</strong>
              <span className="lc-variant-chip">{displayVariantLabel}</span>
            </div>
            {subtitle && size !== 'compact' && <div className="lc-subtitle">{subtitle}</div>}
            {tags && tags.length > 0 && size === 'hero' && (
              <div className="lc-tags">
                {tags.slice(0, 3).map((t) => (
                  <span key={t}>{t}</span>
                ))}
              </div>
            )}
            {footer && <div className="lc-footer">{footer}</div>}
          </div>
        </div>
      </div>
    </div>
  );
};
