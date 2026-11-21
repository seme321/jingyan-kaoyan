import React, { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Award,
  CalendarCheck2,
  Check,
  CheckCircle2,
  Crown,
  Fish,
  Frame,
  Gift,
  Heart,
  Layers,
  Lock,
  PackageOpen,
  Search,
  ShoppingBag,
  Sparkles,
  Ticket,
  Trophy,
  UserCheck,
} from 'lucide-react';
import { useCompanion, type PackOpenResult } from '../context/CompanionContext';
import type { CardVariant, CodexCharacter, StageFrameId } from '../types';
import {
  BOND_PERKS,
  CHECKIN_REWARDS,
  DUPLICATE_REFUND,
  GIFT_ITEMS,
  PACK_DEFS,
  RARITY_ORDER,
  SELECTOR_COST_FISH,
  SELECTOR_COST_VOUCHERS,
  STAGE_FRAMES,
  getBondLevelInfo,
  type PackId,
} from '../data/companionConfig';
import { PackOpeningModal } from '../components/PackOpeningModal';
import { CharacterDetailModal } from '../components/CharacterDetailModal';
import { SelectorTicketModal } from '../components/SelectorTicketModal';

type CompanionTab = 'missions' | 'shop' | 'codex' | 'stage';

export const CompanionPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const rawTab = searchParams.get('tab');
  const activeTab: CompanionTab =
    rawTab === 'shop' || rawTab === 'codex' || rawTab === 'stage' ? rawTab : 'missions';

  const {
    catalog,
    companion,
    activeMascot,
    dailyMissions,
    weeklyMissions,
    achievements,
    claimableCount,
    unlockedCodexCount,
    displayCheckInStreak,
    dailyCheckIn,
    claimDailyMission,
    claimWeeklyMission,
    claimAchievement,
    claimAllRewards,
    openPack,
    redeemSelector,
    giftCharacter,
    equipMascot,
    setApplyGlobally,
    buyFrame,
    equipFrame,
    getBondKey,
  } = useCompanion();

  // Shop state
  const [targetVariant, setTargetVariant] = useState<CardVariant>('standard');
  const [lastPackMeta, setLastPackMeta] = useState<{ packId: PackId; variant: CardVariant }>({
    packId: 'starter',
    variant: 'standard',
  });
  const [packResult, setPackResult] = useState<PackOpenResult | null>(null);
  const [shopFeedback, setShopFeedback] = useState<string | null>(null);
  const [selectorOpen, setSelectorOpen] = useState(false);

  // Codex filter state
  const [codexVariantFilter, setCodexVariantFilter] = useState<'all' | CardVariant>('all');
  const [codexLockFilter, setCodexLockFilter] = useState<'all' | 'unlocked' | 'locked'>('all');
  const [codexQuery, setCodexQuery] = useState('');
  const [detailTarget, setDetailTarget] = useState<{
    char: CodexCharacter;
    variant: CardVariant;
  } | null>(null);

  // Stage quick gift feedback
  const [stageMsg, setStageMsg] = useState<string | null>(null);

  const switchTab = (next: CompanionTab) => {
    setSearchParams({ tab: next }, { replace: true });
  };

  useEffect(() => {
    if (!shopFeedback) return;
    const t = window.setTimeout(() => setShopFeedback(null), 2600);
    return () => window.clearTimeout(t);
  }, [shopFeedback]);

  const handleOpenPack = (packId: PackId, variantChoice: CardVariant = targetVariant) => {
    const res = openPack(packId, variantChoice);
    if (!res.ok) {
      setShopFeedback(res.message ?? '兑换失败');
      return;
    }
    if (res.result) {
      setLastPackMeta({ packId, variant: variantChoice });
      setPackResult(res.result);
    }
  };

  const canOpenLastAgain = useMemo(() => {
    const def = PACK_DEFS.find((p) => p.id === lastPackMeta.packId);
    return Boolean(def && companion.fish >= def.costFish);
  }, [companion.fish, lastPackMeta.packId]);

  const encounteredCharCount = useMemo(() => {
    if (!catalog) return 0;
    return catalog.characters.filter((c) =>
      (['standard', 'medium', 'chibi'] as CardVariant[]).some(
        (v) => (companion.ownedCards[c.variants[v].cardId] ?? 0) > 0
      )
    ).length;
  }, [catalog, companion.ownedCards]);

  const codexCards = useMemo(() => {
    if (!catalog) return [];
    const kw = codexQuery.trim().toLowerCase();

    return catalog.characters
      .map((c) => {
        const ownedVariants: CardVariant[] = (['standard', 'medium', 'chibi'] as CardVariant[]).filter(
          (v) => (companion.ownedCards[c.variants[v].cardId] ?? 0) > 0
        );
        const equippedVariant = companion.equippedCardId.startsWith(`${c.id}:`)
          ? (companion.equippedCardId.split(':')[1] as CardVariant)
          : null;
        const displayVariant: CardVariant =
          codexVariantFilter !== 'all'
            ? codexVariantFilter
            : equippedVariant && ownedVariants.includes(equippedVariant)
              ? equippedVariant
              : ownedVariants[0] ?? 'standard';
        const asset = c.variants[displayVariant];
        const isUnlocked =
          codexVariantFilter === 'all'
            ? ownedVariants.length > 0
            : (companion.ownedCards[asset.cardId] ?? 0) > 0;
        return {
          char: c,
          displayVariant,
          asset,
          ownedVariants,
          isUnlocked,
        };
      })
      .filter((item) => {
        if (codexLockFilter === 'unlocked' && !item.isUnlocked) return false;
        if (codexLockFilter === 'locked' && item.isUnlocked) return false;
        if (!kw) return true;
        const c = item.char;
        return (
          c.name.toLowerCase().includes(kw) ||
          c.subtitle.toLowerCase().includes(kw) ||
          c.visual.toLowerCase().includes(kw) ||
          c.aliases.some((a) => a.toLowerCase().includes(kw)) ||
          c.tags.some((t) => t.toLowerCase().includes(kw))
        );
      });
  }, [
    catalog,
    codexLockFilter,
    codexQuery,
    codexVariantFilter,
    companion.equippedCardId,
    companion.ownedCards,
  ]);

  // All unlocked equippable cards for Stage quick switch
  const unlockedRoster = useMemo(() => {
    const items: Array<{
      cardId: string;
      name: string;
      sub: string;
      rarity: 'SP' | 'SSR' | 'SR' | 'R';
      avatar: string;
      color: string;
      bondLevel: number;
    }> = [];

    if (catalog) {
      for (const sp of catalog.spCards) {
        const xp = companion.bonds[getBondKey(sp.id)] ?? 0;
        items.push({
          cardId: sp.id,
          name: sp.name.replace(/（.*?）/, ''),
          sub: sp.id === 'sp:dafeyu' ? '经典四姿态' : '协研特绘',
          rarity: 'SP',
          avatar: sp.avatar,
          color: sp.color,
          bondLevel: getBondLevelInfo(xp).level,
        });
      }
      for (const c of catalog.characters) {
        for (const v of ['standard', 'medium', 'chibi'] as CardVariant[]) {
          const asset = c.variants[v];
          if ((companion.ownedCards[asset.cardId] ?? 0) > 0) {
            const xp = companion.bonds[c.id] ?? 0;
            items.push({
              cardId: asset.cardId,
              name: c.name,
              sub: asset.label,
              rarity: asset.rarity,
              avatar: asset.avatar,
              color: c.color,
              bondLevel: getBondLevelInfo(xp).level,
            });
          }
        }
      }
    }
    return items.sort((a, b) => RARITY_ORDER[b.rarity] - RARITY_ORDER[a.rarity]);
  }, [catalog, companion.bonds, companion.ownedCards, getBondKey]);

  const activeBondInfo = getBondLevelInfo(activeMascot.bondXp);
  const nextCheckInDayIdx = companion.daily.checkedIn
    ? Math.max(0, (displayCheckInStreak - 1) % 7)
    : displayCheckInStreak % 7;

  return (
    <div className="page-container">
      {/* Top Companion Command Header */}
      <section className="page-header-card companion-hud-header">
        <div className="companion-hud-top">
          <div className="companion-active-mini">
            <img
              src={activeMascot.avatar}
              alt={activeMascot.name}
              className="companion-mini-avatar"
              style={{ borderColor: activeMascot.color }}
            />
            <div>
              <div className="page-kicker">SUPPLY & OPERATOR HUB // 养成与补给中心</div>
              <h1 className="page-title">
                <Fish size={22} className="text-yellow" /> 补给站 · 角色图鉴与看板娘养成
              </h1>
              <p className="page-desc">
                当前看板娘：<strong>{activeMascot.name}</strong>（{activeMascot.rarity} ·{' '}
                {activeMascot.variantLabel} · 信赖 Lv.{activeMascot.bondLevel}）｜
                刷题赚取小鱼干，开启卡包收集全部 42 张角色图鉴并随时替换看板娘
              </p>
            </div>
          </div>

          <div className="companion-currency-strip">
            <div className="currency-pill fish">
              <Fish size={16} />
              <div>
                <span>小鱼干</span>
                <strong>{companion.fish}</strong>
              </div>
            </div>
            <div className="currency-pill voucher">
              <Ticket size={16} />
              <div>
                <span>寻访凭证</span>
                <strong>{companion.vouchers}</strong>
              </div>
            </div>
            <div className="currency-pill codex">
              <Layers size={16} />
              <div>
                <span>图鉴进度</span>
                <strong>{unlockedCodexCount} / 42</strong>
              </div>
            </div>
          </div>
        </div>

        <div className="companion-nav-tabs" role="tablist" aria-label="养成中心模块">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'missions'}
            className={`companion-tab-btn ${activeTab === 'missions' ? 'active' : ''}`}
            onClick={() => switchTab('missions')}
          >
            <CalendarCheck2 size={15} />
            <span>每日任务与成就</span>
            {claimableCount > 0 && <span className="tab-badge">{claimableCount}</span>}
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'shop'}
            className={`companion-tab-btn ${activeTab === 'shop' ? 'active' : ''}`}
            onClick={() => switchTab('shop')}
          >
            <ShoppingBag size={15} />
            <span>小鱼干兑换商店</span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'codex'}
            className={`companion-tab-btn ${activeTab === 'codex' ? 'active' : ''}`}
            onClick={() => switchTab('codex')}
          >
            <Sparkles size={15} />
            <span>角色图鉴 ({unlockedCodexCount}/42)</span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'stage'}
            className={`companion-tab-btn ${activeTab === 'stage' ? 'active' : ''}`}
            onClick={() => switchTab('stage')}
          >
            <Heart size={15} />
            <span>看板娘委任与养成</span>
          </button>
        </div>
      </section>

      {/* TAB 1: DAILY MISSIONS, CHECKIN & ACHIEVEMENTS */}
      {activeTab === 'missions' && (
        <div className="companion-tab-content">
          {claimableCount > 0 && (
            <div className="claim-all-banner">
              <div>
                <strong>有 {claimableCount} 项补给奖励等待领取</strong>
                <span>一次领取所有已完成的签到、每日/周常任务与成就奖励</span>
              </div>
              <button
                type="button"
                className="btn btn-tactical"
                onClick={() => claimAllRewards()}
              >
                <Sparkles size={15} /> 一键全部领取
              </button>
            </div>
          )}

          {/* 7-Day Check-In Panel */}
          <section className="card-panel">
            <div className="panel-head-flex">
              <div>
                <h2 className="panel-title">
                  <CalendarCheck2 size={18} className="text-yellow" /> 每日研友签到补给（7 日循环）
                </h2>
                <p className="panel-sub-copy">
                  当前连续签到：<strong>{displayCheckInStreak}</strong> 天
                  {displayCheckInStreak === 0 && companion.checkInStreak > 0 && !companion.daily.checkedIn
                    ? '（今日签到开启新一轮 7 日连签）'
                    : ''}
                  {' '}· 今日微掉落额度：
                  <strong>{companion.daily.microDropEarned} / 50</strong> 小鱼干 · 伴学经验：
                  <strong>{companion.daily.bondDropEarned} / 20</strong> EXP
                </p>
              </div>
              <button
                type="button"
                className={`btn ${companion.daily.checkedIn ? 'btn-secondary' : 'btn-tactical'}`}
                disabled={companion.daily.checkedIn}
                onClick={() => dailyCheckIn()}
              >
                {companion.daily.checkedIn ? (
                  <>
                    <Check size={15} /> 今日已签到
                  </>
                ) : (
                  <>
                    <Fish size={15} /> 立即签到 (+{CHECKIN_REWARDS[nextCheckInDayIdx]} 鱼干)
                  </>
                )}
              </button>
            </div>

            <div className="checkin-strip">
              {CHECKIN_REWARDS.map((reward, idx) => {
                const cycleLen = displayCheckInStreak % 7;
                const filledCount =
                  companion.daily.checkedIn && cycleLen === 0 && displayCheckInStreak > 0
                    ? 7
                    : cycleLen;
                const isPast = idx < filledCount;
                const isTodaySlot = !companion.daily.checkedIn && idx === nextCheckInDayIdx;
                return (
                  <div
                    key={idx}
                    className={`checkin-day ${isPast ? 'done' : ''} ${isTodaySlot ? 'ready' : ''} ${
                      idx === 6 || idx === 2 ? 'bonus' : ''
                    }`}
                  >
                    <span className="checkin-day-lbl">DAY {idx + 1}</span>
                    <div className="checkin-val">
                      <Fish size={14} /> +{reward}
                    </div>
                    <span className="checkin-status">
                      {isPast ? '已领' : isTodaySlot ? '可签到' : idx === 6 ? '周大奖' : '待解锁'}
                    </span>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Daily & Weekly Missions */}
          <div className="missions-two-col">
            <section className="card-panel">
              <div className="panel-head-flex">
                <h2 className="panel-title">
                  <Sparkles size={18} className="text-sky" /> 每日备考任务（00:00 重置）
                </h2>
                <span className="hud-code">DAILY // {companion.daily.date}</span>
              </div>

              <div className="missions-stack">
                {dailyMissions.map((m) => {
                  const pct = Math.min(100, Math.round((m.current / m.target) * 100));
                  return (
                    <div key={m.id} className={`mission-row ${m.claimed ? 'claimed' : ''}`}>
                      <div className="mission-info">
                        <div className="mission-title-line">
                          <strong>{m.title}</strong>
                          <span className="mission-reward">
                            <Fish size={12} /> +{m.rewardFish}
                          </span>
                        </div>
                        <p className="mission-desc">{m.desc}</p>
                        <div className="mission-prog-wrap">
                          <div className="progress-bar-track">
                            <div
                              className={`progress-seg ${m.done ? 'mastered' : 'partial'}`}
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                          <span className="mission-prog-txt">{m.progressText}</span>
                        </div>
                      </div>

                      <div className="mission-action">
                        {m.claimed ? (
                          <span className="mission-done-chip">
                            <CheckCircle2 size={14} /> 已领取
                          </span>
                        ) : m.done ? (
                          <button
                            type="button"
                            className="btn btn-tactical btn-sm"
                            onClick={() => claimDailyMission(m.id)}
                          >
                            领取 +{m.rewardFish}
                          </button>
                        ) : m.link ? (
                          <Link to={m.link} className="btn btn-secondary btn-sm">
                            {m.linkLabel}
                          </Link>
                        ) : (
                          <span className="hud-code">进行中</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>

            <section className="card-panel">
              <div className="panel-head-flex">
                <h2 className="panel-title">
                  <Trophy size={18} className="text-yellow" /> 每周挑战（周一 00:00 重置）
                </h2>
                <span className="hud-code">WEEKLY // {companion.weekly.weekKey}</span>
              </div>

              <div className="missions-stack">
                {weeklyMissions.map((m) => {
                  const pct = Math.min(100, Math.round((m.current / m.target) * 100));
                  return (
                    <div key={m.id} className={`mission-row ${m.claimed ? 'claimed' : ''}`}>
                      <div className="mission-info">
                        <div className="mission-title-line">
                          <strong>{m.title}</strong>
                          <span className="mission-reward">
                            <Fish size={12} /> +{m.rewardFish}
                          </span>
                        </div>
                        <p className="mission-desc">{m.desc}</p>
                        <div className="mission-prog-wrap">
                          <div className="progress-bar-track">
                            <div
                              className={`progress-seg ${m.done ? 'mastered' : 'partial'}`}
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                          <span className="mission-prog-txt">{m.progressText}</span>
                        </div>
                      </div>

                      <div className="mission-action">
                        {m.claimed ? (
                          <span className="mission-done-chip">
                            <CheckCircle2 size={14} /> 已领取
                          </span>
                        ) : m.done ? (
                          <button
                            type="button"
                            className="btn btn-tactical btn-sm"
                            onClick={() => claimWeeklyMission(m.id)}
                          >
                            领取 +{m.rewardFish}
                          </button>
                        ) : m.link ? (
                          <Link to={m.link} className="btn btn-secondary btn-sm">
                            {m.linkLabel}
                          </Link>
                        ) : (
                          <span className="hud-code">累计中</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          </div>

          {/* One-time Milestones */}
          <section className="card-panel">
            <div className="panel-head-flex">
              <div>
                <h2 className="panel-title">
                  <Award size={18} className="text-purple" /> 全站里程碑成就（跨板块自动累计）
                </h2>
                <p className="panel-sub-copy">
                  历史已做题与模考记录已自动计入，首次上线即可直接领取对应阶段小鱼干奖励！
                </p>
              </div>
              <span className="hud-code">
                已达成 {achievements.filter((a) => a.done).length} / {achievements.length}
              </span>
            </div>

            <div className="achievements-grid">
              {achievements.map((a) => {
                const pct = Math.min(100, Math.round((a.current / a.target) * 100));
                return (
                  <div
                    key={a.id}
                    className={`achievement-card ${a.done ? 'done' : ''} ${a.claimed ? 'claimed' : ''}`}
                  >
                    <div className="ach-top">
                      <strong>{a.title}</strong>
                      <span className="mission-reward">
                        <Fish size={12} /> +{a.rewardFish}
                      </span>
                    </div>
                    <p className="ach-desc">{a.desc}</p>
                    <div className="ach-foot">
                      <div className="ach-bar-box">
                        <div className="progress-bar-track">
                          <div
                            className={`progress-seg ${a.done ? 'mastered' : 'partial'}`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <span>
                          {a.current} / {a.target}
                        </span>
                      </div>
                      {a.claimed ? (
                        <span className="mission-done-chip">已领</span>
                      ) : a.done ? (
                        <button
                          type="button"
                          className="btn btn-tactical btn-sm"
                          onClick={() => claimAchievement(a.id)}
                        >
                          领取
                        </button>
                      ) : (
                        <span className="hud-code">{pct}%</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        </div>
      )}

      {/* TAB 2: EXCHANGE SHOP & GACHA PACKS */}
      {activeTab === 'shop' && (
        <div className="companion-tab-content">
          {shopFeedback && <div className="feedback-banner err">{shopFeedback}</div>}

          <div className="shop-pity-bar card-panel">
            <div>
              <span className="hud-code">PITY TELEMETRY // 寻访保底</span>
              <div className="pity-copy">
                距下一次 10 抽必出 <strong>SSR 标准版</strong> 还差{' '}
                <strong className="text-yellow">{Math.max(1, 10 - companion.pityCounter)}</strong> 抽
                （当前累计未出 SSR：{companion.pityCounter} / 9）
              </div>
            </div>
            <div className="pity-right">
              <span className="hud-code">
                已开包 {companion.totalPacksOpened} 次 · 凭证 {companion.vouchers} 张
              </span>
            </div>
          </div>

          <div className="packs-grid">
            {PACK_DEFS.map((pack) => {
              const affordable = companion.fish >= pack.costFish;
              return (
                <article key={pack.id} className={`pack-shop-card pack-${pack.id} ak-brackets`}>
                  <div className="pack-card-top">
                    <span className="hud-code">{pack.badge}</span>
                    <span className="pack-count-pill">{pack.cardCount} 张 / 包</span>
                  </div>
                  <h3 className="pack-card-title">{pack.name}</h3>
                  <p className="pack-card-sub">{pack.subtitle}</p>

                  <div className="pack-guarantee-box">
                    <strong>{pack.guaranteeLabel}</strong>
                    <span>{pack.ratesLabel}</span>
                  </div>

                  {pack.id === 'variant' && (
                    <div className="pack-variant-picker">
                      <span className="hud-code">选择本次定向 UP 形态：</span>
                      <div className="seg-group">
                        {(['chibi', 'medium', 'standard'] as CardVariant[]).map((v) => (
                          <button
                            key={v}
                            type="button"
                            className={`seg-btn ${targetVariant === v ? 'active' : ''}`}
                            onClick={() => setTargetVariant(v)}
                          >
                            {v === 'chibi' ? 'Q版 R' : v === 'medium' ? '中间 SR' : '标准 SSR'}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="pack-card-foot">
                    <div className="pack-price">
                      <Fish size={16} className="text-yellow" />
                      <strong>{pack.costFish}</strong>
                      <span>小鱼干</span>
                    </div>
                    <button
                      type="button"
                      className={`btn ${affordable ? 'btn-tactical' : 'btn-secondary'}`}
                      disabled={!affordable}
                      onClick={() => handleOpenPack(pack.id, targetVariant)}
                    >
                      <PackageOpen size={15} /> {affordable ? '立即兑换开包' : '小鱼干不足'}
                    </button>
                  </div>
                </article>
              );
            })}

            {/* Unowned Selector Ticket */}
            <article className="pack-shop-card pack-selector ak-brackets">
              <div className="pack-card-top">
                <span className="hud-code">DIRECT RECRUIT // 定向自选</span>
                <span className="pack-count-pill">100% 未收录</span>
              </div>
              <h3 className="pack-card-title">未收录角色自选档案</h3>
              <p className="pack-card-sub">
                拒绝卡 41/42！直接从任意尚未解锁的 42 张图鉴中挑选 1 张带回家。
              </p>
              <div className="pack-guarantee-box">
                <strong>支持 450 小鱼干 或 15 寻访凭证兑换</strong>
                <span>重复抽卡自动返还小鱼干、信赖与寻访凭证</span>
              </div>
              <div className="pack-card-foot">
                <div className="pack-price">
                  <Ticket size={16} className="text-sky" />
                  <strong>{SELECTOR_COST_VOUCHERS}</strong>
                  <span>凭证 / {SELECTOR_COST_FISH} 鱼干</span>
                </div>
                <button
                  type="button"
                  className="btn btn-primary"
                  disabled={unlockedCodexCount >= 42}
                  onClick={() => setSelectorOpen(true)}
                >
                  {unlockedCodexCount >= 42 ? '已全图鉴制霸' : '挑选未收录档案'}
                </button>
              </div>
            </article>
          </div>

          {/* Stage Frames Shop */}
          <section className="card-panel">
            <div className="panel-head-flex">
              <div>
                <h2 className="panel-title">
                  <Frame size={18} className="text-sky" /> 主页看板娘展台装饰框
                </h2>
                <p className="panel-sub-copy">
                  解锁个性化 PRTS 战术边框，装点首页右侧看板娘展台视觉氛围
                </p>
              </div>
            </div>
            <div className="frames-shop-grid">
              {STAGE_FRAMES.map((fr) => {
                const owned = companion.ownedFrames.includes(fr.id);
                const equipped = companion.equippedFrame === fr.id;
                return (
                  <div
                    key={fr.id}
                    className={`frame-shop-item frame-${fr.id} ${equipped ? 'equipped' : ''}`}
                  >
                    <div className="frame-item-head">
                      <strong>{fr.name}</strong>
                      {equipped ? (
                        <span className="status-chip ready">EQUIPPED</span>
                      ) : owned ? (
                        <span className="status-chip planned">OWNED</span>
                      ) : (
                        <span className="mission-reward">
                          <Fish size={12} /> {fr.costFish}
                        </span>
                      )}
                    </div>
                    <p>{fr.desc}</p>
                    <button
                      type="button"
                      className={`btn btn-sm ${
                        equipped ? 'btn-secondary' : owned ? 'btn-primary' : 'btn-tactical'
                      }`}
                      disabled={equipped || (!owned && companion.fish < fr.costFish)}
                      onClick={() =>
                        owned ? equipFrame(fr.id as StageFrameId) : buyFrame(fr.id as StageFrameId)
                      }
                    >
                      {equipped ? '使用中' : owned ? '立即装备' : `解锁 (${fr.costFish} 鱼干)`}
                    </button>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Economy Transparency Box */}
          <section className="card-panel economy-note-panel">
            <span className="hud-code">SUPPLY PROTOCOL // 重复卡转化与保底细则</span>
            <div className="economy-rules-row">
              <span>
                重复 <strong>R (Q版)</strong> → +{DUPLICATE_REFUND.R.fish} 鱼干 / +
                {DUPLICATE_REFUND.R.bond} 信赖 / +{DUPLICATE_REFUND.R.vouchers} 凭证
              </span>
              <span>
                重复 <strong>SR (中间体型)</strong> → +{DUPLICATE_REFUND.SR.fish} 鱼干 / +
                {DUPLICATE_REFUND.SR.bond} 信赖 / +{DUPLICATE_REFUND.SR.vouchers} 凭证
              </span>
              <span>
                重复 <strong>SSR (标准版)</strong> → +{DUPLICATE_REFUND.SSR.fish} 鱼干 / +
                {DUPLICATE_REFUND.SSR.bond} 信赖 / +{DUPLICATE_REFUND.SSR.vouchers} 凭证
              </span>
            </div>
          </section>
        </div>
      )}

      {/* TAB 3: CHARACTER CODEX (14x3 + 2 SP) */}
      {activeTab === 'codex' && (
        <div className="companion-tab-content">
          {/* SP Cards Section */}
          {catalog && (
            <section className="card-panel">
              <div className="panel-head-flex">
                <div>
                  <span className="hud-code">SPECIAL COMMEMORATION // 本站初始及协研纪念角色</span>
                  <h2 className="panel-title">
                    <Crown size={18} className="text-yellow" /> SP 特别限定看板娘（默认已解锁）
                  </h2>
                </div>
              </div>
              <div className="sp-cards-grid">
                {catalog.spCards.map((sp) => {
                  const isEquipped = companion.equippedCardId === sp.id;
                  const bondLv = getBondLevelInfo(companion.bonds[getBondKey(sp.id)] ?? 0).level;
                  return (
                    <article
                      key={sp.id}
                      className={`sp-codex-card ${isEquipped ? 'equipped' : ''}`}
                      style={{ '--card-accent': sp.color } as React.CSSProperties}
                    >
                      <div className="sp-art-box">
                        <img src={sp.sprite} alt={sp.name} />
                      </div>
                      <div className="sp-meta-box">
                        <div className="sp-meta-top">
                          <span className="rarity-tag rarity-SP">SP</span>
                          <span className="hud-code">{sp.code}</span>
                          <span className="bond-mini-tag">Lv.{bondLv}</span>
                        </div>
                        <h3>{sp.name}</h3>
                        <p className="sp-role">{sp.role}</p>
                        <p className="sp-bio">{sp.bio}</p>
                        <div className="sp-actions">
                          <button
                            type="button"
                            className={`btn btn-sm ${isEquipped ? 'btn-secondary' : 'btn-tactical'}`}
                            disabled={isEquipped}
                            onClick={() => equipMascot(sp.id)}
                          >
                            {isEquipped ? (
                              <>
                                <Check size={14} /> 当前看板娘
                              </>
                            ) : (
                              <>
                                <UserCheck size={14} /> 委任为主页看板
                              </>
                            )}
                          </button>
                          <Link to="/about?section=codex" className="btn btn-ghost btn-sm">
                            鸣谢详情 →
                          </Link>
                        </div>
                      </div>
                    </article>
                  );
                })}
              </div>
            </section>
          )}

          {/* Main 14 x 3 Collectible Gallery */}
          <section className="card-panel">
            <div className="codex-progress-strip">
              <div className="codex-progress-meta">
                <span>
                  已相遇 <strong>{encounteredCharCount}</strong> / 14 位角色 · 全形态收录{' '}
                  <strong>{unlockedCodexCount}</strong> / 42 张
                </span>
                <span className="hud-code">
                  COLLECTION // {Math.round((unlockedCodexCount / 42) * 100)}%
                </span>
              </div>
              <div className="progress-bar-track">
                <div
                  className="progress-seg mastered"
                  style={{ width: `${Math.round((unlockedCodexCount / 42) * 100)}%` }}
                />
              </div>
            </div>

            <div className="codex-filter-bar">
              <div className="codex-filter-left">
                <div className="seg-group" role="group" aria-label="按体型筛选">
                  <button
                    type="button"
                    className={`seg-btn ${codexVariantFilter === 'all' ? 'active' : ''}`}
                    onClick={() => setCodexVariantFilter('all')}
                  >
                    全角色 (14)
                  </button>
                  <button
                    type="button"
                    className={`seg-btn ${codexVariantFilter === 'chibi' ? 'active' : ''}`}
                    onClick={() => setCodexVariantFilter('chibi')}
                  >
                    Q版 · R
                  </button>
                  <button
                    type="button"
                    className={`seg-btn ${codexVariantFilter === 'medium' ? 'active' : ''}`}
                    onClick={() => setCodexVariantFilter('medium')}
                  >
                    中间体型 · SR
                  </button>
                  <button
                    type="button"
                    className={`seg-btn ${codexVariantFilter === 'standard' ? 'active' : ''}`}
                    onClick={() => setCodexVariantFilter('standard')}
                  >
                    标准版 · SSR
                  </button>
                </div>

                <div className="seg-group" role="group" aria-label="按解锁状态筛选">
                  <button
                    type="button"
                    className={`seg-btn ${codexLockFilter === 'all' ? 'active' : ''}`}
                    onClick={() => setCodexLockFilter('all')}
                  >
                    全部
                  </button>
                  <button
                    type="button"
                    className={`seg-btn ${codexLockFilter === 'unlocked' ? 'active' : ''}`}
                    onClick={() => setCodexLockFilter('unlocked')}
                  >
                    已解锁
                  </button>
                  <button
                    type="button"
                    className={`seg-btn ${codexLockFilter === 'locked' ? 'active' : ''}`}
                    onClick={() => setCodexLockFilter('locked')}
                  >
                    未解锁
                  </button>
                </div>
              </div>

              <div className="search-input-wrap">
                <Search size={15} />
                <input
                  type="text"
                  placeholder="搜索角色、别名（如白龙娘/海螺娘）、特征…"
                  value={codexQuery}
                  onChange={(e) => setCodexQuery(e.target.value)}
                />
              </div>
            </div>

            {!catalog ? (
              <div className="empty-mini">正在加载角色图鉴档案…</div>
            ) : codexCards.length === 0 ? (
              <div className="empty-mini">没有符合当前筛选条件的角色档案。</div>
            ) : (
              <div className="codex-gallery-grid">
                {codexCards.map(({ char, displayVariant, asset, ownedVariants, isUnlocked }) => {
                  const isEquipped = companion.equippedCardId === asset.cardId;
                  const bondLv = getBondLevelInfo(companion.bonds[char.id] ?? 0).level;
                  return (
                    <article
                      key={char.id}
                      className={`codex-gallery-card ${isUnlocked ? 'unlocked' : 'locked'} ${
                        isEquipped ? 'equipped' : ''
                      }`}
                      style={{ '--card-accent': char.color } as React.CSSProperties}
                      onClick={() => setDetailTarget({ char, variant: displayVariant })}
                    >
                      <div className="codex-gallery-art">
                        <img
                          src={asset.sprite}
                          alt={isUnlocked ? char.name : `${char.name} 未解锁`}
                          className={!isUnlocked ? 'locked-silhouette' : ''}
                          loading="lazy"
                        />
                        <div className="codex-card-badges">
                          <span className={`rarity-tag rarity-${asset.rarity}`}>
                            {asset.rarity}
                          </span>
                          {isEquipped && <span className="equipped-tag">看板中</span>}
                          {!isUnlocked && (
                            <span className="locked-tag">
                              <Lock size={11} /> LOCKED
                            </span>
                          )}
                        </div>
                        {/* 3 Variant Unlock Pips */}
                        <div className="codex-variant-pips" title="Q版 / 中间体型 / 标准版 解锁进度">
                          {(['chibi', 'medium', 'standard'] as CardVariant[]).map((v) => {
                            const hasV = ownedVariants.includes(v);
                            return (
                              <span key={v} className={`v-pip ${hasV ? 'on' : ''}`}>
                                {v === 'chibi' ? 'Q' : v === 'medium' ? '中' : '标'}
                              </span>
                            );
                          })}
                        </div>
                      </div>

                      <div className="codex-gallery-body">
                        <div className="codex-gallery-head">
                          <span className="hud-code">{char.code}</span>
                          {isUnlocked && <span className="bond-mini-tag">信赖 Lv.{bondLv}</span>}
                        </div>
                        <h3>{char.name}</h3>
                        <p className="codex-gallery-sub">{char.subtitle}</p>
                        <div className="codex-tags">
                          {char.tags.map((t) => (
                            <span key={t}>{t}</span>
                          ))}
                        </div>
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </section>
        </div>
      )}

      {/* TAB 4: MASCOT STAGE & BOND NURTURING */}
      {activeTab === 'stage' && (
        <div className="companion-tab-content">
          <div className="stage-management-grid">
            {/* Active Mascot Live Preview & Feeding */}
            <section
              className={`card-panel active-stage-card frame-${companion.equippedFrame} ${
                activeBondInfo.level >= 10
                  ? 'bond-tier-10'
                  : activeBondInfo.level >= 6
                    ? 'bond-tier-6'
                    : ''
              }`}
              style={{ '--operator-accent': activeMascot.color } as React.CSSProperties}
            >
              <div className="panel-head-flex">
                <div>
                  <span className="hud-code">
                    ACTIVE ASSISTANT // {activeMascot.code} · {activeMascot.rarity}
                    {activeBondInfo.level >= 10 && ' · ✦ 上岸誓约'}
                    {activeBondInfo.level >= 6 && activeBondInfo.level < 10 && ' · ✦ 默契流光'}
                  </span>
                  <h2 className="panel-title">
                    {activeMascot.name}（{activeMascot.variantLabel}）
                    {activeBondInfo.level >= 10 && (
                      <span className="oath-chip">✦ 上岸誓约</span>
                    )}
                  </h2>
                </div>
                <Link to="/" className="btn btn-secondary btn-sm">
                  返回首页查看效果 →
                </Link>
              </div>

              <div className="stage-preview-row">
                <div className="stage-preview-visual">
                  <img src={activeMascot.sprite} alt={activeMascot.name} className="mascot-float" />
                </div>

                <div className="stage-preview-stats">
                  <div className="bond-strip">
                    <div className="bond-strip-top">
                      <span className="bond-lv">
                        <Heart size={15} className="text-coral" /> 默契信赖{' '}
                        <strong>Lv.{activeBondInfo.level}</strong>
                      </span>
                      <span className="hud-code">
                        {activeBondInfo.nextFloor !== null
                          ? `${activeBondInfo.xp} / ${activeBondInfo.nextFloor} EXP`
                          : `${activeBondInfo.xp} EXP (MAX)`}
                      </span>
                    </div>
                    <div className="progress-bar-track">
                      <div
                        className="progress-seg mastered"
                        style={{ width: `${activeBondInfo.progressPct}%` }}
                      />
                    </div>
                  </div>

                  <div className="stage-perks-grid">
                    {BOND_PERKS.map((pk) => {
                      const unlocked = activeBondInfo.level >= pk.level;
                      return (
                        <div key={pk.level} className={`perk-chip ${unlocked ? 'unlocked' : ''}`}>
                          <strong>Lv.{pk.level}</strong>
                          <span>{pk.label}</span>
                          <em>{unlocked ? '已激活' : '未解锁'}</em>
                        </div>
                      );
                    })}
                  </div>

                  <div className="stage-feed-box">
                    <span className="hud-code">
                      投喂「{activeMascot.name}」提升默契（余额 {companion.fish} 小鱼干）
                    </span>
                    <div className="bond-gift-btns">
                      {GIFT_ITEMS.map((g) => (
                        <button
                          key={g.id}
                          type="button"
                          className="btn btn-secondary btn-sm"
                          disabled={companion.fish < g.costFish}
                          onClick={() => {
                            const r = giftCharacter(activeMascot.cardId, g.id);
                            setStageMsg(r.message);
                            window.setTimeout(() => setStageMsg(null), 2000);
                          }}
                          title={g.desc}
                        >
                          <Gift size={13} /> {g.name} ({g.costFish}鱼干 · +{g.bondGain}EXP)
                        </button>
                      ))}
                    </div>
                    {stageMsg && <span className="bond-gift-feedback">{stageMsg}</span>}
                  </div>
                </div>
              </div>

              {/* Global Scope Toggle */}
              <div className="stage-scope-row">
                <div>
                  <div className="setting-label">看板娘替换作用范围</div>
                  <div className="setting-desc">
                    开启「全站同步替换」后，刷题判题提示条、加载页、模考结算页也会一并换为当前委任角色
                  </div>
                </div>
                <div className="seg-group">
                  <button
                    type="button"
                    className={`seg-btn ${companion.applyGlobally ? 'active' : ''}`}
                    onClick={() => setApplyGlobally(true)}
                  >
                    全站同步替换（推荐）
                  </button>
                  <button
                    type="button"
                    className={`seg-btn ${!companion.applyGlobally ? 'active' : ''}`}
                    onClick={() => setApplyGlobally(false)}
                  >
                    仅替换首页展台
                  </button>
                </div>
              </div>
            </section>

            {/* Quick Switch Roster */}
            <section className="card-panel">
              <div className="panel-head-flex">
                <div>
                  <h2 className="panel-title">
                    <UserCheck size={18} className="text-sky" /> 已解锁看板娘快捷切换 ({unlockedRoster.length})
                  </h2>
                  <p className="panel-sub-copy">点击任意已解锁卡片立即更换站内陪伴角色</p>
                </div>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => switchTab('shop')}
                >
                  去卡包商店解锁更多 →
                </button>
              </div>

              <div className="roster-switch-grid">
                {unlockedRoster.map((item) => {
                  const active = companion.equippedCardId === item.cardId;
                  return (
                    <button
                      key={item.cardId}
                      type="button"
                      className={`roster-switch-card ${active ? 'active' : ''}`}
                      style={{ '--card-accent': item.color } as React.CSSProperties}
                      onClick={() => equipMascot(item.cardId)}
                    >
                      <img src={item.avatar} alt={item.name} />
                      <div className="roster-switch-meta">
                        <div className="roster-top-tags">
                          <span className={`rarity-tag rarity-${item.rarity}`}>{item.rarity}</span>
                          <span className="bond-mini-tag">Lv.{item.bondLevel}</span>
                        </div>
                        <strong>{item.name}</strong>
                        <small>{item.sub}</small>
                      </div>
                      {active && (
                        <span className="roster-active-mark">
                          <Check size={14} />
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </section>
          </div>
        </div>
      )}

      {/* Modals */}
      <PackOpeningModal
        result={packResult}
        equippedCardId={companion.equippedCardId}
        canOpenAgain={canOpenLastAgain}
        onClose={() => setPackResult(null)}
        onEquipCard={(cid) => equipMascot(cid)}
        onOpenAgain={() => handleOpenPack(lastPackMeta.packId, lastPackMeta.variant)}
      />

      <CharacterDetailModal
        character={detailTarget?.char ?? null}
        initialVariant={detailTarget?.variant ?? 'standard'}
        ownedCards={companion.ownedCards}
        bondXp={detailTarget ? companion.bonds[detailTarget.char.id] ?? 0 : 0}
        fishBalance={companion.fish}
        equippedCardId={companion.equippedCardId}
        onClose={() => setDetailTarget(null)}
        onEquip={(cid) => equipMascot(cid)}
        onGift={(charId, giftId) => giftCharacter(charId, giftId)}
      />

      <SelectorTicketModal
        open={selectorOpen}
        characters={catalog?.characters ?? []}
        ownedCards={companion.ownedCards}
        fishBalance={companion.fish}
        vouchersBalance={companion.vouchers}
        onClose={() => setSelectorOpen(false)}
        onRedeem={(cid, payWith) => redeemSelector(cid, payWith)}
      />
    </div>
  );
};
