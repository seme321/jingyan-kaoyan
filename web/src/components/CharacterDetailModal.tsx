import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import {
  Check,
  ExternalLink,
  Fish,
  Gift,
  Heart,
  Lock,
  Maximize2,
  MessageSquareQuote,
  Sparkles,
  UserCheck,
  X,
} from 'lucide-react';
import type { CardVariant, CodexCharacter } from '../types';
import {
  BOND_PERKS,
  GIFT_ITEMS,
  VARIANT_LABELS,
  getBondLevelInfo,
} from '../data/companionConfig';

interface CharacterDetailModalProps {
  character: CodexCharacter | null;
  initialVariant?: CardVariant;
  ownedCards: Record<string, number>;
  bondXp: number;
  fishBalance: number;
  equippedCardId: string;
  onClose: () => void;
  onEquip: (cardId: string) => void;
  onGift: (charId: string, giftId: string) => { ok: boolean; message: string };
}

const VARIANT_ORDER: CardVariant[] = ['chibi', 'medium', 'standard'];

export const CharacterDetailModal: React.FC<CharacterDetailModalProps> = ({
  character,
  initialVariant = 'standard',
  ownedCards,
  bondXp,
  fishBalance,
  equippedCardId,
  onClose,
  onEquip,
  onGift,
}) => {
  const [variant, setVariant] = useState<CardVariant>(initialVariant);
  const [viewMode, setViewMode] = useState<'sprite' | 'sheet'>('sprite');
  const [tab, setTab] = useState<'profile' | 'quotes' | 'sources'>('profile');
  const [zoomSrc, setZoomSrc] = useState<string | null>(null);
  const [giftMsg, setGiftMsg] = useState<string | null>(null);
  const ownedCardsRef = useRef(ownedCards);
  ownedCardsRef.current = ownedCards;
  const giftTimerRef = useRef<number | null>(null);

  useEffect(() => {
    if (!character) return;
    const latestOwned = ownedCardsRef.current;
    // Prefer an owned variant if initialVariant isn't owned
    const ownedFirst =
      (latestOwned[character.variants[initialVariant].cardId] ?? 0) > 0
        ? initialVariant
        : VARIANT_ORDER.find((v) => (latestOwned[character.variants[v].cardId] ?? 0) > 0) ??
          initialVariant;
    setVariant(ownedFirst);
    setViewMode('sprite');
    setTab('profile');
    setGiftMsg(null);
    setZoomSrc(null);
  }, [character?.id, initialVariant]);

  useEffect(() => {
    return () => {
      if (giftTimerRef.current !== null) {
        window.clearTimeout(giftTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!character) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (zoomSrc) setZoomSrc(null);
        else onClose();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [character, zoomSrc, onClose]);

  if (!character) return null;

  const activeAsset = character.variants[variant];
  const ownedCount = ownedCards[activeAsset.cardId] ?? 0;
  const isVariantOwned = ownedCount > 0;
  const anyOwned = VARIANT_ORDER.some((v) => (ownedCards[character.variants[v].cardId] ?? 0) > 0);
  const isEquipped = equippedCardId === activeAsset.cardId;
  const bondInfo = getBondLevelInfo(bondXp);

  const handleGiftClick = (giftId: string) => {
    const res = onGift(character.id, giftId);
    setGiftMsg(res.message);
    if (giftTimerRef.current !== null) {
      window.clearTimeout(giftTimerRef.current);
    }
    giftTimerRef.current = window.setTimeout(() => {
      setGiftMsg(null);
      giftTimerRef.current = null;
    }, 2200);
  };

  return createPortal(
    <>
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="char-detail-modal ak-brackets"
        style={{ '--char-accent': character.color } as React.CSSProperties}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="char-detail-topbar">
          <div className="char-detail-id">
            <span className="hud-code">OPERATOR // {character.code}</span>
            <span className={`rarity-tag rarity-${activeAsset.rarity}`}>{activeAsset.rarity}</span>
            <span className="char-detail-vlabel">{VARIANT_LABELS[variant]}</span>
          </div>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="关闭角色档案">
            <X size={18} />
          </button>
        </div>

        <div className="char-detail-layout">
          {/* Left Visual Stage */}
          <div className="char-detail-visual">
            <div className="char-stage-controls">
              <div className="seg-group">
                {VARIANT_ORDER.map((v) => {
                  const asset = character.variants[v];
                  const has = (ownedCards[asset.cardId] ?? 0) > 0;
                  return (
                    <button
                      key={v}
                      type="button"
                      className={`seg-btn ${variant === v ? 'active' : ''}`}
                      onClick={() => setVariant(v)}
                    >
                      {v === 'chibi' ? 'Q版 R' : v === 'medium' ? '中间 SR' : '标准 SSR'}
                      {!has && ' 🔒'}
                    </button>
                  );
                })}
              </div>

              {isVariantOwned && (
                <div className="seg-group">
                  <button
                    type="button"
                    className={`seg-btn ${viewMode === 'sprite' ? 'active' : ''}`}
                    onClick={() => setViewMode('sprite')}
                  >
                    看板立绘
                  </button>
                  <button
                    type="button"
                    className={`seg-btn ${viewMode === 'sheet' ? 'active' : ''}`}
                    onClick={() => setViewMode('sheet')}
                  >
                    三视图设定
                  </button>
                </div>
              )}
            </div>

            <div className={`char-portrait-stage ${!isVariantOwned ? 'is-locked' : ''}`}>
              {isVariantOwned ? (
                <>
                  <img
                    src={viewMode === 'sprite' ? activeAsset.sprite : activeAsset.sheet}
                    alt={`${character.name} ${activeAsset.label}`}
                    className={viewMode === 'sprite' ? 'char-sprite-img' : 'char-sheet-img'}
                  />
                  <button
                    type="button"
                    className="codex-zoom-chip"
                    onClick={() =>
                      setZoomSrc(viewMode === 'sprite' ? activeAsset.sprite : activeAsset.sheet)
                    }
                    title="放大高清查看"
                  >
                    <Maximize2 size={11} /> ZOOM
                  </button>
                </>
              ) : (
                <div className="char-locked-overlay">
                  <img
                    src={activeAsset.sprite}
                    alt=""
                    className="char-sprite-img locked-silhouette"
                    aria-hidden="true"
                  />
                  <div className="char-locked-badge">
                    <Lock size={18} />
                    <strong>尚未解锁「{activeAsset.label}」形态</strong>
                    <span>前往卡包商店寻访或使用未收录自选档案解锁</span>
                  </div>
                </div>
              )}
            </div>

            <div className="char-visual-actions">
              {isVariantOwned ? (
                <button
                  type="button"
                  className={`btn ${isEquipped ? 'btn-secondary' : 'btn-tactical'} btn-full`}
                  disabled={isEquipped}
                  onClick={() => onEquip(activeAsset.cardId)}
                >
                  {isEquipped ? (
                    <>
                      <Check size={15} /> 当前正担任看板娘
                    </>
                  ) : (
                    <>
                      <UserCheck size={15} /> 委任此形态为主页看板娘
                    </>
                  )}
                </button>
              ) : (
                <div className="char-unowned-note">
                  持有数量：0（其他已解锁形态可正常切换查看与委任）
                </div>
              )}
            </div>
          </div>

          {/* Right Dossier Info */}
          <div className="char-detail-info">
            <div className="char-title-block">
              <div className="char-name-row">
                <h2 className="char-detail-name">{character.name}</h2>
                <span className="char-color-swatch" style={{ background: character.color }} />
              </div>
              <p className="char-detail-sub">{character.subtitle}</p>
              <div className="codex-tags">
                {character.tags.map((t) => (
                  <span key={t}>{t}</span>
                ))}
                {character.aliases.slice(0, 3).map((a) => (
                  <span key={a} className="alias-tag">
                    {a}
                  </span>
                ))}
              </div>
            </div>

            {/* Bond Progress Strip */}
            <div className="bond-strip">
              <div className="bond-strip-top">
                <span className="bond-lv">
                  <Heart size={14} className="text-coral" /> 默契信赖 <strong>Lv.{bondInfo.level}</strong>
                </span>
                <span className="hud-code">
                  {bondInfo.nextFloor !== null
                    ? `${bondInfo.xp} / ${bondInfo.nextFloor} EXP`
                    : `${bondInfo.xp} EXP (MAX)`}
                </span>
              </div>
              <div className="progress-bar-track">
                <div className="progress-seg mastered" style={{ width: `${bondInfo.progressPct}%` }} />
              </div>
              {anyOwned && (
                <div className="bond-gift-row">
                  <span className="bond-gift-lbl">
                    <Gift size={13} /> 投喂提升默契（当前 {fishBalance} 鱼干）：
                  </span>
                  <div className="bond-gift-btns">
                    {GIFT_ITEMS.map((g) => (
                      <button
                        key={g.id}
                        type="button"
                        className="btn btn-secondary btn-sm"
                        disabled={fishBalance < g.costFish}
                        onClick={() => handleGiftClick(g.id)}
                        title={g.desc}
                      >
                        {g.name} ({g.costFish}
                        <Fish size={11} />)
                      </button>
                    ))}
                  </div>
                  {giftMsg && <span className="bond-gift-feedback">{giftMsg}</span>}
                </div>
              )}
            </div>

            {/* Info Subtabs */}
            <div className="char-info-tabs" role="tablist">
              <button
                type="button"
                role="tab"
                aria-selected={tab === 'profile'}
                className={`seg-btn ${tab === 'profile' ? 'active' : ''}`}
                onClick={() => setTab('profile')}
              >
                角色档案
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={tab === 'quotes'}
                className={`seg-btn ${tab === 'quotes' ? 'active' : ''}`}
                onClick={() => setTab('quotes')}
              >
                考研陪读语录
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={tab === 'sources'}
                className={`seg-btn ${tab === 'sources' ? 'active' : ''}`}
                onClick={() => setTab('sources')}
              >
                来源与二创说明
              </button>
            </div>

            <div className="char-tab-body">
              {tab === 'profile' && (
                <div className="char-profile-copy">
                  <div className="char-quote-hook">「{character.hook}」</div>
                  <div className="char-kv">
                    <span className="char-k">二创角色定位</span>
                    <p>{character.projectRole}</p>
                  </div>
                  <div className="char-kv">
                    <span className="char-k">视觉特征观察</span>
                    <p>{character.visual}</p>
                  </div>
                  <div className="char-kv">
                    <span className="char-k">性格与背景设想</span>
                    <p>{character.projectBackground}</p>
                  </div>
                  <div className="char-kv">
                    <span className="char-k">说话风格</span>
                    <p>{character.speechStyle}</p>
                  </div>
                </div>
              )}

              {tab === 'quotes' && (
                <div className="char-quotes-list">
                  <div className="char-perk-summary">
                    {BOND_PERKS.map((pk) => {
                      const unlocked = bondInfo.level >= pk.level;
                      return (
                        <span
                          key={pk.level}
                          className={`perk-chip ${unlocked ? 'unlocked' : ''}`}
                        >
                          Lv.{pk.level} · {pk.label} {unlocked ? '✓' : '🔒'}
                        </span>
                      );
                    })}
                  </div>
                  <div className="char-quote-card">
                    <span className="hud-code">GREETING // 欢迎台词</span>
                    <p>{character.greetTemplate}</p>
                  </div>
                  {character.studyQuotes.map((q, i) => {
                    const lockedByBond = i >= 3 && bondInfo.level < 2;
                    return (
                      <div key={i} className={`char-quote-card ${lockedByBond ? 'locked' : ''}`}>
                        <span className="hud-code">
                          <MessageSquareQuote size={11} /> BRIEF #{i + 1}
                          {lockedByBond && ' · 信赖 Lv.2 解锁'}
                        </span>
                        <p>{lockedByBond ? '提升角色信赖至 Lv.2 后即可解锁本条专属备考提示～' : q}</p>
                      </div>
                    );
                  })}
                  <div className="char-quote-card">
                    <span className="hud-code">
                      <Sparkles size={11} /> 判题反馈（全站替换生效；信赖 Lv.4 激活「默契连携」光效）
                    </span>
                    <p>
                      <strong>答对：</strong>
                      {character.judgeOkQuote}
                      <br />
                      <strong>答错：</strong>
                      {character.judgeWarnQuote}
                    </p>
                  </div>
                </div>
              )}

              {tab === 'sources' && (
                <div className="char-sources-copy">
                  <p className="char-source-summary">{character.communitySummary}</p>
                  <div className="char-sources-list">
                    {character.sources.map((src) => (
                      <div key={src.id} className="char-source-item">
                        <div className="char-source-head">
                          <a
                            href={src.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-contact-link"
                          >
                            {src.title} <ExternalLink size={12} />
                          </a>
                          <span>
                            {src.author} · {src.date}
                          </span>
                        </div>
                        <p>{src.evidence}</p>
                        <small>{src.limits}</small>
                      </div>
                    ))}
                  </div>
                  <p className="char-source-disclaimer">
                    本页社区资料与来源核验整理参考自{' '}
                    <a
                      href="https://github.com/HABAI182/ai-girls-atlas"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-contact-link"
                    >
                      HABAI182 / AI Girls Atlas
                    </a>
                    （AI MUSE / AI_2Dgirls_Gallery 企划；研究说明按{' '}
                    <a
                      href="https://creativecommons.org/licenses/by/4.0/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-contact-link"
                    >
                      CC BY 4.0
                    </a>{' '}
                    署名，本站补充了考研水力学陪读语录）。角色设定图由企划维护者参考「Creeper-北极之光」提供的初始图生成，经本站单视角裁切、透明抠图与 WebP 适配，仅供非商业学习陪伴展示，不对图片主张统一 CC 或商业许可；各社区作者署名与许可边界以逐条来源为准，不代表对应 AI 厂商官方人设；如涉权益争议请联系站长 48 小时内更正或移除。
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>

      {zoomSrc && (
        <div className="lightbox-backdrop" onClick={() => setZoomSrc(null)}>
          <div className="lightbox-content codex-lightbox" onClick={(e) => e.stopPropagation()}>
            <div className="lightbox-toolbar">
              <span className="hud-code">
                {character.code} // {character.name} ({activeAsset.label})
              </span>
              <button
                type="button"
                className="lightbox-close"
                onClick={() => setZoomSrc(null)}
                aria-label="关闭高清预览"
              >
                <X size={18} />
              </button>
            </div>
            <img src={zoomSrc} alt={character.name} />
          </div>
        </div>
      )}
    </>,
    document.body
  );
};
