import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { Check, Fish, PackageOpen, RotateCw, Sparkles, Ticket, UserCheck, X } from 'lucide-react';
import type { PackOpenResult, PullResultItem } from '../context/CompanionContext';

interface PackOpeningModalProps {
  result: PackOpenResult | null;
  equippedCardId: string;
  canOpenAgain: boolean;
  onClose: () => void;
  onEquipCard: (cardId: string) => void;
  onOpenAgain: () => void;
}

export const PackOpeningModal: React.FC<PackOpeningModalProps> = ({
  result,
  equippedCardId,
  canOpenAgain,
  onClose,
  onEquipCard,
  onOpenAgain,
}) => {
  const [sealed, setSealed] = useState(true);
  const [revealedIdx, setRevealedIdx] = useState<boolean[]>([]);

  useEffect(() => {
    if (!result) return;
    setSealed(true);
    setRevealedIdx(result.pulls.map(() => false));
    const timer = window.setTimeout(() => setSealed(false), 380);
    return () => window.clearTimeout(timer);
  }, [result]);

  useEffect(() => {
    if (!result) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [result, onClose]);

  if (!result) return null;

  const allRevealed = revealedIdx.length > 0 && revealedIdx.every(Boolean);

  const flipCard = (idx: number) => {
    setRevealedIdx((prev) => prev.map((v, i) => (i === idx ? true : v)));
  };

  const revealAll = () => {
    setSealed(false);
    setRevealedIdx(result.pulls.map(() => true));
  };

  const highestRarity = result.pulls.some((p) => p.rarity === 'SSR')
    ? 'SSR'
    : result.pulls.some((p) => p.rarity === 'SR')
      ? 'SR'
      : 'R';

  return createPortal(
    <div className="modal-backdrop pack-modal-backdrop" onClick={onClose}>
      <div className="pack-modal-panel ak-brackets" onClick={(e) => e.stopPropagation()}>
        <div className="pack-modal-head">
          <div>
            <div className="page-kicker">PRTS SUPPLY // UNBOXING PROTOCOL</div>
            <h3 className="modal-title">
              <PackageOpen size={20} className="text-yellow" /> {result.packName} · 补给解封
            </h3>
          </div>
          <div className="pack-head-actions">
            {!allRevealed && (
              <button type="button" className="btn btn-tactical btn-sm" onClick={revealAll}>
                <Sparkles size={14} /> 一键全开
              </button>
            )}
            <button type="button" className="icon-btn" onClick={onClose} aria-label="关闭开包弹窗">
              <X size={18} />
            </button>
          </div>
        </div>

        {sealed ? (
          <div className="pack-seal-stage" onClick={() => setSealed(false)}>
            <div className={`pack-seal-crate rarity-${highestRarity}`}>
              <span className="hud-code">ENCRYPTED ARCHIVE // {result.pulls.length}X</span>
              <div className="pack-seal-title">正在解析角色档案信号…</div>
              <div className="pack-seal-bar">
                <i />
              </div>
              <span className="pack-seal-hint">点击加速解封</span>
            </div>
          </div>
        ) : (
          <>
            <div className={`pack-cards-grid cols-${result.pulls.length}`}>
              {result.pulls.map((pull: PullResultItem, idx: number) => {
                const isFlipped = revealedIdx[idx] ?? false;
                const isEquipped = equippedCardId === pull.cardId;
                return (
                  <div
                    key={`${pull.cardId}-${idx}`}
                    className={`gacha-card-slot rarity-${pull.rarity} ${isFlipped ? 'revealed' : ''}`}
                    style={{ '--card-accent': pull.color } as React.CSSProperties}
                    role={!isFlipped ? 'button' : undefined}
                    tabIndex={!isFlipped ? 0 : undefined}
                    aria-label={!isFlipped ? `翻开第 ${idx + 1} 张 ${pull.rarity} 档案` : undefined}
                    onClick={() => !isFlipped && flipCard(idx)}
                    onKeyDown={(e) => {
                      if (!isFlipped && (e.key === 'Enter' || e.key === ' ')) {
                        e.preventDefault();
                        flipCard(idx);
                      }
                    }}
                  >
                    {!isFlipped ? (
                      <div className="gacha-card-back">
                        <span className="gacha-rarity-pip">{pull.rarity}</span>
                        <div className="gacha-back-emblem">
                          <RotateCw size={22} />
                        </div>
                        <span className="gacha-back-hint">点击翻开</span>
                      </div>
                    ) : (
                      <div className="gacha-card-front">
                        <div className="gacha-front-top">
                          <span className={`rarity-tag rarity-${pull.rarity}`}>{pull.rarity}</span>
                          {pull.isNew ? (
                            <span className="new-tag">NEW!</span>
                          ) : (
                            <span className="dup-tag">已转化</span>
                          )}
                        </div>
                        <div className="gacha-front-art">
                          <img src={pull.sprite} alt={`${pull.charName} ${pull.variantLabel}`} />
                        </div>
                        <div className="gacha-front-info">
                          <div className="gacha-front-name">{pull.charName}</div>
                          <div className="gacha-front-variant">{pull.variantLabel}</div>
                          {!pull.isNew ? (
                            <div className="gacha-refund-row">
                              <span>+{pull.refundFish} 鱼干</span>
                              <span>+{pull.refundBond} 信赖</span>
                              <span>+{pull.refundVouchers} 凭证</span>
                            </div>
                          ) : (
                            <button
                              type="button"
                              className={`btn btn-sm ${isEquipped ? 'btn-secondary' : 'btn-primary'} gacha-equip-btn`}
                              onClick={(e) => {
                                e.stopPropagation();
                                onEquipCard(pull.cardId);
                              }}
                              disabled={isEquipped}
                            >
                              {isEquipped ? (
                                <>
                                  <Check size={13} /> 已委任
                                </>
                              ) : (
                                <>
                                  <UserCheck size={13} /> 设为看板娘
                                </>
                              )}
                            </button>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {allRevealed && (
              <div className="pack-summary-bar">
                <div className="pack-summary-stats">
                  <span>
                    本次新解锁{' '}
                    <strong className="text-yellow">
                      {result.pulls.filter((p) => p.isNew).length}
                    </strong>{' '}
                    张档案
                  </span>
                  {result.totalRefundFish > 0 && (
                    <span className="pack-summary-chip">
                      <Fish size={13} /> 重复转化 +{result.totalRefundFish} 小鱼干
                    </span>
                  )}
                  {result.totalRefundVouchers + result.bonusVouchers > 0 && (
                    <span className="pack-summary-chip">
                      <Ticket size={13} /> 寻访凭证 +
                      {result.totalRefundVouchers + result.bonusVouchers}
                    </span>
                  )}
                </div>
                <div className="pack-summary-actions">
                  {canOpenAgain && (
                    <button type="button" className="btn btn-tactical btn-sm" onClick={onOpenAgain}>
                      <Sparkles size={14} /> 再开一包
                    </button>
                  )}
                  <button type="button" className="btn btn-secondary btn-sm" onClick={onClose}>
                    收下档案
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>,
    document.body
  );
};
