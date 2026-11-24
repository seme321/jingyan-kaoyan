import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import {
  ArrowLeft,
  Check,
  Fish,
  SkipForward,
  Sparkles,
  Ticket,
  UserCheck,
  Volume2,
  VolumeX,
  X,
} from 'lucide-react';
import type { PackOpenResult, PullResultItem } from '../context/CompanionContext';
import { useStudy } from '../context/StudyContext';
import { LightConeCard } from './LightConeCard';
import { WarpTunnelCanvas } from './WarpTunnelCanvas';
import {
  isGachaMuted,
  playCardReveal,
  playUiTick,
  playWarpBurst,
  playWarpCharge,
  setGachaMuted,
  stopWarpAudio,
} from '../utils/gachaAudio';

interface PackOpeningModalProps {
  result: PackOpenResult | null;
  equippedCardId: string;
  canOpenAgain: boolean;
  onClose: () => void;
  onEquipCard: (cardId: string) => void;
  onOpenAgain: () => void;
}

type CinemaPhase = 'warp' | 'reveal' | 'summary';

const RARITY_STAR_COUNTS: Record<'R' | 'SR' | 'SSR', number> = {
  R: 3,
  SR: 4,
  SSR: 5,
};

function getPrefersReducedMotion(animatedBg: boolean | undefined): boolean {
  if (animatedBg === false) return true;
  if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }
  return false;
}

export const PackOpeningModal: React.FC<PackOpeningModalProps> = ({
  result,
  equippedCardId,
  canOpenAgain,
  onClose,
  onEquipCard,
  onOpenAgain,
}) => {
  const { state } = useStudy();
  const reducedMotion = getPrefersReducedMotion(state.settings.animatedBg);

  const [phase, setPhase] = useState<CinemaPhase>('warp');
  const phaseRef = useRef<CinemaPhase>('warp');
  phaseRef.current = phase;
  const [revealIdx, setRevealIdx] = useState(0);
  const [sessionSeq, setSessionSeq] = useState(0);
  const [flashToken, setFlashToken] = useState(0);
  const [inspectPull, setInspectPull] = useState<PullResultItem | null>(null);
  const [muted, setMuted] = useState<boolean>(() => isGachaMuted());

  const highestRarity: 'R' | 'SR' | 'SSR' = useMemo(() => {
    if (!result) return 'R';
    if (result.pulls.some((p) => p.rarity === 'SSR')) return 'SSR';
    if (result.pulls.some((p) => p.rarity === 'SR')) return 'SR';
    return 'R';
  }, [result]);

  useEffect(() => {
    if (!result) {
      stopWarpAudio();
      return;
    }
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    phaseRef.current = 'warp';
    setPhase('warp');
    setRevealIdx(0);
    setInspectPull(null);
    setSessionSeq((s) => s + 1);
    setFlashToken((t) => t + 1);
    playWarpCharge(highestRarity);

    return () => {
      document.body.style.overflow = prevOverflow;
      stopWarpAudio();
    };
  }, [result, highestRarity]);

  const enterRevealFromWarp = useCallback(() => {
    if (!result || phaseRef.current !== 'warp') return;
    phaseRef.current = 'reveal';
    stopWarpAudio();
    playWarpBurst(highestRarity);
    setPhase('reveal');
    setRevealIdx(0);
    setFlashToken((t) => t + 1);
  }, [result, highestRarity]);

  const skipToSummary = useCallback(() => {
    phaseRef.current = 'summary';
    stopWarpAudio();
    playUiTick();
    setInspectPull(null);
    setPhase('summary');
  }, []);

  const handleClose = useCallback(() => {
    stopWarpAudio();
    onClose();
  }, [onClose]);

  const handleAdvanceReveal = useCallback(() => {
    if (!result) return;
    if (inspectPull) {
      playUiTick();
      setInspectPull(null);
      return;
    }
    if (revealIdx < result.pulls.length - 1) {
      const nextIdx = revealIdx + 1;
      const nextPull = result.pulls[nextIdx];
      setRevealIdx(nextIdx);
      setFlashToken((t) => t + 1);
      if (nextPull) {
        if (nextPull.rarity === 'SSR') {
          playWarpBurst('SSR');
        } else {
          playCardReveal(nextPull.rarity, nextPull.isNew);
        }
      }
    } else {
      phaseRef.current = 'summary';
      playUiTick();
      setPhase('summary');
    }
  }, [inspectPull, result, revealIdx]);

  const toggleMute = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setMuted((prev) => {
      const next = !prev;
      setGachaMuted(next);
      return next;
    });
  }, []);

  useEffect(() => {
    if (!result) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (inspectPull) {
          setInspectPull(null);
        } else if (phase === 'summary') {
          handleClose();
        } else {
          skipToSummary();
        }
        return;
      }

      const target = e.target as HTMLElement | null;
      if (target && target.closest('button, a, input, select, textarea')) return;

      if (e.key === ' ' || e.key === 'Enter' || e.key === 'ArrowRight') {
        e.preventDefault();
        if (phase === 'warp') {
          enterRevealFromWarp();
        } else if (phase === 'reveal' || inspectPull) {
          handleAdvanceReveal();
        }
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [
    enterRevealFromWarp,
    handleAdvanceReveal,
    handleClose,
    inspectPull,
    phase,
    result,
    skipToSummary,
  ]);

  if (!result) return null;

  const activeRevealPull = inspectPull ?? (phase === 'reveal' ? result.pulls[revealIdx] ?? null : null);
  const newCount = result.pulls.filter((p) => p.isNew).length;
  const totalVouchersGained = result.totalRefundVouchers + result.bonusVouchers;

  return createPortal(
    <div
      className={`warp-cinema-backdrop phase-${inspectPull ? 'reveal' : phase} rarity-${highestRarity}`}
      role="dialog"
      aria-modal="true"
      aria-label={`${result.packName} 跃迁解封`}
    >
      {/* Persistent Top Cinema Control Bar */}
      <header className="warp-cinema-topbar">
        <div className="warp-topbar-left">
          <span className="warp-protocol-badge">PRTS WARP // {result.packName}</span>
          {phase === 'reveal' && !inspectPull && (
            <div className="warp-progress-pips" aria-label={`第 ${revealIdx + 1} 张，共 ${result.pulls.length} 张`}>
              {result.pulls.map((p, idx) => (
                <span
                  key={`${p.cardId}-${idx}`}
                  className={`warp-pip rarity-${p.rarity} ${
                    idx === revealIdx ? 'current' : idx < revealIdx ? 'seen' : ''
                  }`}
                />
              ))}
              <span className="warp-pip-count">
                {revealIdx + 1} / {result.pulls.length}
              </span>
            </div>
          )}
          {inspectPull && (
            <span className="warp-inspect-chip">档案特写预览 · {inspectPull.charName}</span>
          )}
        </div>

        <div className="warp-topbar-actions">
          <button
            type="button"
            className="warp-pill-btn icon-only"
            onClick={toggleMute}
            aria-label={muted ? '开启跃迁音效' : '静音跃迁音效'}
            title={muted ? '开启跃迁音效' : '静音跃迁音效'}
          >
            {muted ? <VolumeX size={15} /> : <Volume2 size={15} />}
          </button>

          {inspectPull ? (
            <button
              type="button"
              className="warp-pill-btn"
              onClick={(e) => {
                e.stopPropagation();
                playUiTick();
                setInspectPull(null);
              }}
            >
              <ArrowLeft size={14} /> 返回总览
            </button>
          ) : phase !== 'summary' ? (
            <button
              type="button"
              className="warp-pill-btn"
              onClick={(e) => {
                e.stopPropagation();
                skipToSummary();
              }}
            >
              跳过 <SkipForward size={14} />
            </button>
          ) : (
            <button
              type="button"
              className="warp-pill-btn icon-only"
              onClick={handleClose}
              aria-label="关闭跃迁结算"
            >
              <X size={16} />
            </button>
          )}
        </div>
      </header>

      {/* PHASE 1: Canvas 2D Hyperspace Starlight Tunnel */}
      {phase === 'warp' && !inspectPull && (
        <div
          className="warp-stage-shell"
          onClick={enterRevealFromWarp}
          role="button"
          tabIndex={0}
          aria-label="点击加速进入揭示画面"
        >
          <WarpTunnelCanvas
            key={sessionSeq}
            highestRarity={highestRarity}
            reducedMotion={reducedMotion}
            onBurstPeak={enterRevealFromWarp}
          />
          <div className="warp-stage-caption">
            <span className="warp-signal-line">
              DEEP-SEA ARCHIVE SIGNAL LOCKED · {result.pulls.length}X
              {highestRarity === 'SSR' && ' · HIGH-ENERGY GOLD SIGNAL'}
            </span>
            <span className="warp-tap-hint">点击任意处加速跃迁</span>
          </div>
        </div>
      )}

      {/* PHASE 2: Fullscreen Character / Light Cone Reveal Theater (or Summary Inspect) */}
      {activeRevealPull && (
        <div
          key={`reveal-${activeRevealPull.cardId}-${revealIdx}-${flashToken}`}
          className={`warp-reveal-stage rarity-${activeRevealPull.rarity}`}
          style={{ '--card-accent': activeRevealPull.color } as React.CSSProperties}
          onClick={handleAdvanceReveal}
        >
          {/* Ambient Cosmic Depth + Volumetric Pillars + Aurora Arc */}
          <div className="warp-reveal-bg" aria-hidden="true">
            <div className="warp-reveal-aurora" />
            <div className="warp-reveal-pillars">
              <span className="wrp p1" />
              <span className="wrp p2" />
              <span className="wrp p3" />
            </div>
            <div className="warp-reveal-reticle" />
          </div>

          {/* Whiteout / Platinum Flash Dissolve Overlay */}
          {!reducedMotion && <div className="warp-whiteout-flash" aria-hidden="true" />}

          <div className="warp-reveal-content">
            {/* Left Floating Nameplate HUD + Vertical Glowing Lead Line */}
            <div className="warp-reveal-hud">
              <div className="warp-hud-badges">
                <span className="warp-archive-pill">ARCHIVE // {activeRevealPull.code}</span>
                <span className={`rarity-tag rarity-${activeRevealPull.rarity}`}>
                  {activeRevealPull.rarity}
                </span>
                {activeRevealPull.isNew ? (
                  <span className="new-tag">NEW!</span>
                ) : (
                  <span className="warp-dup-pill">已收录 · 自动转化</span>
                )}
              </div>

              <div className="warp-nameplate-block">
                <div className="warp-nameplate-stem" aria-hidden="true">
                  <i className="stem-node" />
                  <span className="stem-line" />
                </div>

                <div className="warp-nameplate-main">
                  <div className="warp-char-title-row">
                    <h2 className="warp-char-name">{activeRevealPull.charName}</h2>
                    <span className="warp-variant-pill">{activeRevealPull.variantLabel}</span>
                  </div>

                  <div
                    className="warp-stars-row"
                    aria-label={`${RARITY_STAR_COUNTS[activeRevealPull.rarity]} 星`}
                  >
                    {Array.from({ length: RARITY_STAR_COUNTS[activeRevealPull.rarity] }).map(
                      (_, sIdx) => (
                        <span
                          key={sIdx}
                          className="warp-star-item"
                          style={{ '--star-idx': sIdx } as React.CSSProperties}
                        >
                          ✦
                        </span>
                      )
                    )}
                  </div>

                  {activeRevealPull.subtitle && (
                    <p className="warp-char-sub">{activeRevealPull.subtitle}</p>
                  )}

                  {activeRevealPull.tags.length > 0 && (
                    <div className="warp-char-tags">
                      {activeRevealPull.tags.slice(0, 3).map((tag) => (
                        <span key={tag}>{tag}</span>
                      ))}
                    </div>
                  )}

                  {activeRevealPull.hook && (
                    <blockquote className="warp-char-hook">「{activeRevealPull.hook}」</blockquote>
                  )}

                  <div className="warp-hud-actions">
                    <button
                      type="button"
                      className={`btn btn-sm ${
                        equippedCardId === activeRevealPull.cardId
                          ? 'btn-secondary'
                          : 'btn-tactical'
                      }`}
                      disabled={equippedCardId === activeRevealPull.cardId}
                      onClick={(e) => {
                        e.stopPropagation();
                        onEquipCard(activeRevealPull.cardId);
                      }}
                    >
                      {equippedCardId === activeRevealPull.cardId ? (
                        <>
                          <Check size={14} /> 已委任看板娘
                        </>
                      ) : (
                        <>
                          <UserCheck size={14} /> 设为看板娘
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Center-Right Visual Showcase: Oversized Cutout for SSR, 3D LightConeCard for R/SR */}
            <div className="warp-reveal-visual">
              {activeRevealPull.rarity === 'SSR' ? (
                <div className="warp-reveal-ssr-stage">
                  <div className="warp-ssr-prism-frame" aria-hidden="true" />
                  <div className="warp-ssr-halo" aria-hidden="true" />
                  <img
                    src={activeRevealPull.sprite}
                    alt={`${activeRevealPull.charName} ${activeRevealPull.variantLabel}`}
                    className="warp-ssr-cutout"
                  />
                </div>
              ) : (
                <div className="warp-reveal-lc-wrap">
                  <LightConeCard
                    name={activeRevealPull.charName}
                    code={activeRevealPull.code}
                    subtitle={activeRevealPull.subtitle}
                    variantLabel={activeRevealPull.variantLabel}
                    rarity={activeRevealPull.rarity}
                    color={activeRevealPull.color}
                    sprite={activeRevealPull.sprite}
                    tags={activeRevealPull.tags}
                    isNew={activeRevealPull.isNew}
                    isEquipped={equippedCardId === activeRevealPull.cardId}
                    bloomOnMount={!reducedMotion}
                    interactive={!reducedMotion}
                    size="hero"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Bottom-Right Conversion / Unlock Toast */}
          <div className="warp-reveal-toast">
            {activeRevealPull.isNew ? (
              <span className="toast-new">
                <Sparkles size={14} /> 首次收录 · 角色图鉴档案已激活
              </span>
            ) : (
              <span className="toast-dup">
                重复转化 · +{activeRevealPull.refundFish} 小鱼干 · +{activeRevealPull.refundBond}{' '}
                信赖 · +{activeRevealPull.refundVouchers} 凭证
              </span>
            )}
          </div>

          {/* Bottom Center Continue Prompt */}
          <div className="warp-reveal-prompt">
            {inspectPull
              ? '点击任意处返回本次跃迁总览'
              : revealIdx < result.pulls.length - 1
                ? `点击任意处继续 (${revealIdx + 1} / ${result.pulls.length})`
                : '点击任意处查看本次跃迁总览'}
          </div>
        </div>
      )}

      {/* PHASE 3: Multi-Pull Light Cone Summary Grid */}
      {phase === 'summary' && !inspectPull && (
        <div className="warp-summary-backdrop" onClick={handleClose}>
          <div className="warp-summary-panel ak-brackets" onClick={(e) => e.stopPropagation()}>
            <div className="warp-summary-head">
              <div>
                <div className="page-kicker">WARP COMPLETE // 档案解封总览</div>
                <h3 className="warp-summary-title">
                  {result.packName} · {result.pulls.length} 连跃迁结果
                  <span className={`rarity-tag rarity-${highestRarity}`}>
                    最高 {highestRarity}
                  </span>
                </h3>
              </div>
              <span className="warp-summary-tip">悬停欣赏 3D 光锥折光 · 点击卡面可重温特写</span>
            </div>

            <div className={`warp-summary-grid cols-${result.pulls.length}`}>
              {result.pulls.map((pull, idx) => {
                const isEquipped = equippedCardId === pull.cardId;
                return (
                  <div key={`${pull.cardId}-${idx}`} className="warp-summary-slot">
                    <LightConeCard
                      name={pull.charName}
                      code={pull.code}
                      variantLabel={pull.variantLabel}
                      rarity={pull.rarity}
                      color={pull.color}
                      sprite={pull.sprite}
                      isNew={pull.isNew}
                      isEquipped={isEquipped}
                      bloomOnMount={!reducedMotion}
                      interactive={!reducedMotion}
                      size="compact"
                      onClick={() => {
                        playCardReveal(pull.rarity, pull.isNew);
                        setFlashToken((t) => t + 1);
                        setInspectPull(pull);
                      }}
                      footer={
                        <div className="warp-slot-footer">
                          {!pull.isNew && (
                            <div className="gacha-refund-row">
                              <span>+{pull.refundFish} 鱼干</span>
                              <span>+{pull.refundBond} 信赖</span>
                              <span>+{pull.refundVouchers} 凭证</span>
                            </div>
                          )}
                          <button
                            type="button"
                            className={`btn btn-sm ${
                              isEquipped ? 'btn-secondary' : 'btn-tactical'
                            } gacha-equip-btn`}
                            disabled={isEquipped}
                            onClick={(e) => {
                              e.stopPropagation();
                              onEquipCard(pull.cardId);
                            }}
                          >
                            {isEquipped ? (
                              <>
                                <Check size={12} /> 已委任
                              </>
                            ) : (
                              <>
                                <UserCheck size={12} /> 设为看板娘
                              </>
                            )}
                          </button>
                        </div>
                      }
                    />
                  </div>
                );
              })}
            </div>

            <div className="pack-summary-bar">
              <div className="pack-summary-stats">
                <span>
                  本次新解锁 <strong className="text-yellow">{newCount}</strong> 张档案
                </span>
                {result.totalRefundFish > 0 && (
                  <span className="pack-summary-chip">
                    <Fish size={13} /> 重复转化 +{result.totalRefundFish} 小鱼干
                  </span>
                )}
                {totalVouchersGained > 0 && (
                  <span className="pack-summary-chip">
                    <Ticket size={13} /> 寻访凭证 +{totalVouchersGained}
                  </span>
                )}
              </div>

              <div className="pack-summary-actions">
                {canOpenAgain && (
                  <button
                    type="button"
                    className="btn btn-tactical btn-sm"
                    onClick={() => {
                      playUiTick();
                      onOpenAgain();
                    }}
                  >
                    <Sparkles size={14} /> 再开一包
                  </button>
                )}
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={handleClose}
                >
                  收下档案
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>,
    document.body
  );
};
