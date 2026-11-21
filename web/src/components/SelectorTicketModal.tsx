import React, { useEffect, useMemo, useState } from 'react';
import { createPortal } from 'react-dom';
import { Check, Fish, Ticket, X } from 'lucide-react';
import type { CardVariant, CodexCharacter } from '../types';
import { SELECTOR_COST_FISH, SELECTOR_COST_VOUCHERS, VARIANT_LABELS } from '../data/companionConfig';

interface SelectorTicketModalProps {
  open: boolean;
  characters: CodexCharacter[];
  ownedCards: Record<string, number>;
  fishBalance: number;
  vouchersBalance: number;
  onClose: () => void;
  onRedeem: (cardId: string, payWith: 'fish' | 'vouchers') => { ok: boolean; message: string };
}

export const SelectorTicketModal: React.FC<SelectorTicketModalProps> = ({
  open,
  characters,
  ownedCards,
  fishBalance,
  vouchersBalance,
  onClose,
  onRedeem,
}) => {
  const [variantFilter, setVariantFilter] = useState<'all' | CardVariant>('standard');
  const [selectedCardId, setSelectedCardId] = useState<string>('');
  const [feedback, setFeedback] = useState<{ ok: boolean; text: string } | null>(null);

  useEffect(() => {
    setSelectedCardId('');
  }, [variantFilter]);

  useEffect(() => {
    if (!open) {
      setSelectedCardId('');
      setFeedback(null);
      return;
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  const missingCards = useMemo(() => {
    const list: Array<{
      cardId: string;
      charName: string;
      variant: CardVariant;
      rarity: 'R' | 'SR' | 'SSR';
      avatar: string;
      color: string;
    }> = [];
    const variants: CardVariant[] =
      variantFilter === 'all' ? ['standard', 'medium', 'chibi'] : [variantFilter];

    for (const c of characters) {
      for (const v of variants) {
        const asset = c.variants[v];
        if ((ownedCards[asset.cardId] ?? 0) === 0) {
          list.push({
            cardId: asset.cardId,
            charName: c.name,
            variant: v,
            rarity: asset.rarity,
            avatar: asset.avatar,
            color: c.color,
          });
        }
      }
    }
    return list;
  }, [characters, ownedCards, variantFilter]);

  if (!open) return null;

  const canPayFish = fishBalance >= SELECTOR_COST_FISH;
  const canPayVoucher = vouchersBalance >= SELECTOR_COST_VOUCHERS;

  const handleConfirm = (payWith: 'fish' | 'vouchers') => {
    if (!selectedCardId) return;
    const res = onRedeem(selectedCardId, payWith);
    setFeedback({ ok: res.ok, text: res.message });
    if (res.ok) {
      setSelectedCardId('');
      window.setTimeout(() => {
        setFeedback(null);
        onClose();
      }, 900);
    }
  };

  return createPortal(
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-panel selector-modal-panel" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <div className="page-kicker">DIRECT RECRUIT // UNOWNED ARCHIVE SELECTOR</div>
            <h3 className="modal-title">未收录自选档案兑换</h3>
            <p className="modal-sub">
              使用 {SELECTOR_COST_FISH} 小鱼干 或 {SELECTOR_COST_VOUCHERS} 寻访凭证直接解锁任意一张尚未收录的卡片
            </p>
          </div>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="关闭自选兑换">
            <X size={18} />
          </button>
        </div>

        <div className="selector-toolbar">
          <div className="seg-group">
            <button
              type="button"
              className={`seg-btn ${variantFilter === 'standard' ? 'active' : ''}`}
              onClick={() => setVariantFilter('standard')}
            >
              标准版 SSR
            </button>
            <button
              type="button"
              className={`seg-btn ${variantFilter === 'medium' ? 'active' : ''}`}
              onClick={() => setVariantFilter('medium')}
            >
              中间体型 SR
            </button>
            <button
              type="button"
              className={`seg-btn ${variantFilter === 'chibi' ? 'active' : ''}`}
              onClick={() => setVariantFilter('chibi')}
            >
              Q版 R
            </button>
            <button
              type="button"
              className={`seg-btn ${variantFilter === 'all' ? 'active' : ''}`}
              onClick={() => setVariantFilter('all')}
            >
              全部未收录
            </button>
          </div>
          <span className="hud-code">待解锁 {missingCards.length} 张</span>
        </div>

        <div className="selector-grid">
          {missingCards.length === 0 ? (
            <div className="empty-mini" style={{ gridColumn: '1 / -1' }}>
              当前筛选形态已全部集齐，太强啦！
            </div>
          ) : (
            missingCards.map((item) => {
              const active = selectedCardId === item.cardId;
              return (
                <button
                  key={item.cardId}
                  type="button"
                  className={`selector-card ${active ? 'selected' : ''}`}
                  style={{ '--card-accent': item.color } as React.CSSProperties}
                  onClick={() => setSelectedCardId(item.cardId)}
                >
                  <img src={item.avatar} alt={item.charName} />
                  <div className="selector-card-meta">
                    <span className={`rarity-tag rarity-${item.rarity}`}>{item.rarity}</span>
                    <strong>{item.charName}</strong>
                    <small>{VARIANT_LABELS[item.variant]}</small>
                  </div>
                  {active && (
                    <span className="selector-check">
                      <Check size={13} />
                    </span>
                  )}
                </button>
              );
            })
          )}
        </div>

        {feedback && (
          <div className={`feedback-banner ${feedback.ok ? 'ok' : 'err'}`}>{feedback.text}</div>
        )}

        <div className="selector-foot">
          <button
            type="button"
            className="btn btn-primary"
            disabled={!selectedCardId || !canPayVoucher}
            onClick={() => handleConfirm('vouchers')}
          >
            <Ticket size={15} /> 用 {SELECTOR_COST_VOUCHERS} 凭证兑换（当前 {vouchersBalance}）
          </button>
          <button
            type="button"
            className="btn btn-tactical"
            disabled={!selectedCardId || !canPayFish}
            onClick={() => handleConfirm('fish')}
          >
            <Fish size={15} /> 用 {SELECTOR_COST_FISH} 小鱼干兑换（当前 {fishBalance}）
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
};
