import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import type {
  CardRarity,
  CardVariant,
  CodexCatalog,
  CodexCharacter,
  CodexSpCard,
  CompanionState,
  DailyCompanionProgress,
  StageFrameId,
  WeeklyCompanionProgress,
} from '../types';
import { useStudy } from './StudyContext';
import {
  ACHIEVEMENTS,
  CHECKIN_REWARDS,
  DAILY_MISSIONS,
  DUPLICATE_REFUND,
  GIFT_ITEMS,
  PACK_DEFS,
  SELECTOR_COST_FISH,
  SELECTOR_COST_VOUCHERS,
  STAGE_FRAMES,
  VARIANT_LABELS,
  WEEKLY_MISSIONS,
  getBondLevelInfo,
  type PackId,
} from '../data/companionConfig';

export interface RewardToast {
  id: string;
  title: string;
  subtitle?: string;
  fishDelta?: number;
  tone?: 'info' | 'gold' | 'ok';
}

export interface MissionProgressItem {
  id: string;
  title: string;
  desc: string;
  current: number;
  target: number;
  progressText: string;
  rewardFish: number;
  done: boolean;
  claimed: boolean;
  link?: string;
  linkLabel?: string;
}

export interface AchievementProgressItem {
  id: string;
  title: string;
  desc: string;
  category: 'study' | 'mock' | 'codex';
  current: number;
  target: number;
  rewardFish: number;
  done: boolean;
  claimed: boolean;
}

export interface PullResultItem {
  cardId: string;
  charId: string;
  charName: string;
  subtitle: string;
  variant: CardVariant;
  variantLabel: string;
  rarity: 'R' | 'SR' | 'SSR';
  color: string;
  sprite: string;
  avatar: string;
  isNew: boolean;
  refundFish: number;
  refundBond: number;
  refundVouchers: number;
}

export interface PackOpenResult {
  packId: PackId;
  packName: string;
  pulls: PullResultItem[];
  bonusVouchers: number;
  totalRefundFish: number;
  totalRefundVouchers: number;
}

export interface ActiveMascotInfo {
  cardId: string;
  bondKey: string;
  isDefaultDafeyu: boolean;
  isSp: boolean;
  code: string;
  name: string;
  subtitle: string;
  rarity: CardRarity;
  variantLabel: string;
  color: string;
  sprite: string;
  avatar: string;
  bondXp: number;
  bondLevel: number;
  greetTemplate: string;
  judgeOkQuote: string;
  judgeWarnQuote: string;
  studyQuotes: string[];
}

interface CompanionContextValue {
  catalog: CodexCatalog | null;
  companion: CompanionState;
  activeMascot: ActiveMascotInfo;
  dailyMissions: MissionProgressItem[];
  weeklyMissions: MissionProgressItem[];
  achievements: AchievementProgressItem[];
  claimableCount: number;
  unlockedCodexCount: number;
  displayCheckInStreak: number;
  toasts: RewardToast[];
  dismissToast: (id: string) => void;
  pushToast: (toast: Omit<RewardToast, 'id'>) => void;
  getBondKey: (cardId: string) => string;
  getCardCount: (cardId: string) => number;
  dailyCheckIn: () => { ok: boolean; reward: number; streak: number };
  claimDailyMission: (id: string) => boolean;
  claimWeeklyMission: (id: string) => boolean;
  claimAchievement: (id: string) => boolean;
  claimAllRewards: () => { claimed: number; fishGained: number };
  openPack: (
    packId: PackId,
    targetVariant?: CardVariant
  ) => { ok: boolean; message?: string; result?: PackOpenResult };
  redeemSelector: (
    cardId: string,
    payWith: 'fish' | 'vouchers'
  ) => { ok: boolean; message: string };
  giftCharacter: (charOrCardId: string, giftId: string) => { ok: boolean; message: string };
  interactWithMascot: () => { granted: boolean; fishGain: number; bondGain: number };
  equipMascot: (cardId: string) => void;
  setApplyGlobally: (val: boolean) => void;
  buyFrame: (frameId: StageFrameId) => { ok: boolean; message: string };
  equipFrame: (frameId: StageFrameId) => void;
  trackFormulaFlip: (formulaId: string) => void;
}

const DEFAULT_DF_INFO: ActiveMascotInfo = {
  cardId: 'sp:dafeyu',
  bondKey: 'dafeyu',
  isDefaultDafeyu: true,
  isSp: true,
  code: 'DF-01',
  name: '大肥鱼',
  subtitle: '鲸研首发看板娘 · 海洋系护航',
  rarity: 'SP',
  variantLabel: '经典四姿态',
  color: '#22c7f2',
  sprite: './mascot/hero.webp',
  avatar: './mascot/hero.webp',
  bondXp: 0,
  bondLevel: 1,
  greetTemplate: '你好呀，我是大肥鱼！今天也一起把考研真题一点点啃下来吧～',
  judgeOkQuote: '判断正确！本题已归档为已掌握，继续保持节奏～',
  judgeWarnQuote: '判断失误！已自动同步至错题本，展开下方精解核查陷阱吧。',
  studyQuotes: [
    '伯努利方程先定基准面、再找渐变流断面，水头损失一项都别漏！',
    '静水总压力曲面算水平与铅垂分力，压力体虚实一定先画箭头判断方向～',
    '明渠非均匀流 12 条水面线：先判坡度（缓/陡），再看水深落在 1/2/3 哪一区！',
    '刷错的题会自动同步进错题本，考前清零错题本就能稳稳上岸！',
  ],
};

function getLocalDateKey(d = new Date()): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function getPrevLocalDateKey(d = new Date()): string {
  const prev = new Date(d);
  prev.setDate(prev.getDate() - 1);
  return getLocalDateKey(prev);
}

function getWeekKey(d = new Date()): string {
  const monday = new Date(d);
  const diff = (monday.getDay() + 6) % 7;
  monday.setDate(monday.getDate() - diff);
  return getLocalDateKey(monday);
}

function createEmptyDaily(date: string): DailyCompanionProgress {
  return {
    date,
    checkedIn: false,
    practicedQids: [],
    masteredQids: [],
    bigQuestionQids: [],
    wrongClearedQids: [],
    noteQids: [],
    formulaFlippedIds: [],
    microDropQids: [],
    microDropEarned: 0,
    bondDropQids: [],
    bondDropEarned: 0,
    mascotInteracted: false,
    claimedMissions: [],
  };
}

function createEmptyWeekly(weekKey: string): WeeklyCompanionProgress {
  return {
    weekKey,
    practicedQids: [],
    mockCount: 0,
    activeDays: [],
    claimedMissions: [],
  };
}

export function resolveBondKey(cardId: string): string {
  if (cardId.startsWith('sp:')) return cardId.slice(3);
  return cardId.split(':')[0] || cardId;
}

function createInitialCompanionState(): CompanionState {
  const today = getLocalDateKey();
  const weekKey = getWeekKey();
  return {
    version: 1,
    fish: 80,
    vouchers: 0,
    totalPacksOpened: 0,
    pityCounter: 0,
    checkInStreak: 0,
    lastCheckInDate: '',
    ownedCards: {
      'sp:dafeyu': 1,
      'sp:gemini': 1,
    },
    bonds: {
      dafeyu: 0,
      gemini: 0,
    },
    equippedCardId: 'sp:dafeyu',
    applyGlobally: true,
    ownedFrames: ['default'],
    equippedFrame: 'default',
    daily: createEmptyDaily(today),
    weekly: createEmptyWeekly(weekKey),
    claimedAchievements: [],
  };
}

function normalizeCompanionPeriods(raw: CompanionState | undefined): CompanionState {
  const base = raw ?? createInitialCompanionState();
  const today = getLocalDateKey();
  const weekKey = getWeekKey();
  const daily =
    base.daily && base.daily.date === today ? base.daily : createEmptyDaily(today);
  const weekly =
    base.weekly && base.weekly.weekKey === weekKey ? base.weekly : createEmptyWeekly(weekKey);
  const ownedCards: Record<string, number> = {
    'sp:dafeyu': 1,
    'sp:gemini': 1,
    ...(base.ownedCards ?? {}),
  };
  const ownedFrames: StageFrameId[] = Array.isArray(base.ownedFrames) && base.ownedFrames.length > 0
    ? base.ownedFrames
    : ['default'];
  return {
    ...createInitialCompanionState(),
    ...base,
    ownedCards,
    bonds: base.bonds ?? {},
    ownedFrames,
    daily,
    weekly,
    claimedAchievements: Array.isArray(base.claimedAchievements) ? base.claimedAchievements : [],
  };
}

function appendUnique(list: string[], item: string): string[] {
  return list.includes(item) ? list : [...list, item];
}

function pickWeighted<T>(items: Array<{ item: T; weight: number }>): T {
  const total = items.reduce((s, x) => s + x.weight, 0);
  let r = Math.random() * total;
  for (const x of items) {
    r -= x.weight;
    if (r <= 0) return x.item;
  }
  return items[items.length - 1].item;
}

const CompanionContext = createContext<CompanionContextValue | null>(null);

export const CompanionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { allCourses, companionState, setCompanionState, subscribeStudyEvent } = useStudy();
  const [catalog, setCatalog] = useState<CodexCatalog | null>(null);
  const [toasts, setToasts] = useState<RewardToast[]>([]);

  // Load codex.json lazily
  useEffect(() => {
    let cancelled = false;
    fetch('./data/codex.json')
      .then((r) => (r.ok ? r.json() : null))
      .then((data: CodexCatalog | null) => {
        if (!cancelled && data && Array.isArray(data.characters)) {
          setCatalog(data);
        }
      })
      .catch(() => {
        // non-blocking
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Ensure companion slice is initialized & rolled over on first mount
  useEffect(() => {
    const today = getLocalDateKey();
    const weekKey = getWeekKey();
    if (
      !companionState ||
      companionState.daily?.date !== today ||
      companionState.weekly?.weekKey !== weekKey
    ) {
      setCompanionState((prev) => normalizeCompanionPeriods(prev));
    }
  }, [companionState, setCompanionState]);

  const companion = useMemo(
    () => normalizeCompanionPeriods(companionState),
    [companionState]
  );
  const companionRef = useRef(companion);
  companionRef.current = companion;
  const claimedGuardRef = useRef<Set<string>>(new Set());

  const isStreakAlive =
    companion.daily.checkedIn || companion.lastCheckInDate === getPrevLocalDateKey();
  const displayCheckInStreak = isStreakAlive ? companion.checkInStreak : 0;

  const prevMicroRef = useRef({
    date: companion.daily.date,
    earned: companion.daily.microDropEarned,
    count: companion.daily.microDropQids.length,
  });

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const pushToast = useCallback((toast: Omit<RewardToast, 'id'>) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
    setToasts((prev) => [...prev.slice(-2), { ...toast, id }]);
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3800);
  }, []);

  // Observe micro-drop increases reactively (automatically coalesces batch grading)
  useEffect(() => {
    const { date, microDropEarned, microDropQids } = companion.daily;
    const count = microDropQids.length;
    if (date !== prevMicroRef.current.date) {
      prevMicroRef.current = { date, earned: microDropEarned, count };
      return;
    }
    const delta = microDropEarned - prevMicroRef.current.earned;
    const qDelta = Math.max(1, count - prevMicroRef.current.count);
    if (delta > 0) {
      prevMicroRef.current = { date, earned: microDropEarned, count };
      pushToast({
        title: `刷题补给掉落 (${qDelta} 题)`,
        subtitle: '继续保持！累计可前往「补给站」兑换卡包',
        fishDelta: delta,
        tone: 'ok',
      });
    }
  }, [
    companion.daily.date,
    companion.daily.microDropEarned,
    companion.daily.microDropQids.length,
    pushToast,
  ]);

  // Subscribe to study events across all courses
  useEffect(() => {
    return subscribeStudyEvent((ev) => {
      const today = getLocalDateKey();

      setCompanionState((prevRaw) => {
        const cur = normalizeCompanionPeriods(prevRaw);
        const daily = { ...cur.daily };
        const weekly = { ...cur.weekly, activeDays: appendUnique(cur.weekly.activeDays, today) };
        let fish = cur.fish;
        const bonds = { ...cur.bonds };

        if (ev.type === 'attempt') {
          const key = `${ev.courseId}:${ev.qid}`;
          daily.practicedQids = appendUnique(daily.practicedQids, key);
          weekly.practicedQids = appendUnique(weekly.practicedQids, key);
          if (ev.status === 'mastered') {
            daily.masteredQids = appendUnique(daily.masteredQids, key);
          }
          if (ev.isBigQuestion) {
            daily.bigQuestionQids = appendUnique(daily.bigQuestionQids, key);
          }

          const eligibleMicro =
            (ev.prevStatus === 'unseen' || ev.prevStatus === 'wrong') &&
            (ev.status === 'mastered' || ev.status === 'partial');
          if (
            eligibleMicro &&
            !daily.microDropQids.includes(key) &&
            daily.microDropEarned < 50
          ) {
            daily.microDropQids = [...daily.microDropQids, key];
            daily.microDropEarned += 5;
            fish += 5;
          }

          if (!daily.bondDropQids.includes(key) && daily.bondDropEarned < 20) {
            daily.bondDropQids = [...daily.bondDropQids, key];
            daily.bondDropEarned += 2;
            const bk = resolveBondKey(cur.equippedCardId);
            bonds[bk] = (bonds[bk] ?? 0) + 2;
          }
        } else if (ev.type === 'wrong_cleared') {
          const key = `${ev.courseId}:${ev.qid}`;
          daily.wrongClearedQids = appendUnique(daily.wrongClearedQids, key);
        } else if (ev.type === 'note_saved') {
          const key = `${ev.courseId}:${ev.qid}`;
          daily.noteQids = appendUnique(daily.noteQids, key);
        } else if (ev.type === 'mock_saved') {
          weekly.mockCount += 1;
        }

        return {
          ...cur,
          fish,
          bonds,
          daily,
          weekly,
        };
      });
    });
  }, [setCompanionState, subscribeStudyEvent]);

  const trackFormulaFlip = useCallback(
    (formulaId: string) => {
      setCompanionState((prevRaw) => {
        const cur = normalizeCompanionPeriods(prevRaw);
        if (cur.daily.formulaFlippedIds.includes(formulaId)) return cur;
        return {
          ...cur,
          daily: {
            ...cur.daily,
            formulaFlippedIds: [...cur.daily.formulaFlippedIds, formulaId],
          },
          weekly: {
            ...cur.weekly,
            activeDays: appendUnique(cur.weekly.activeDays, cur.daily.date),
          },
        };
      });
    },
    [setCompanionState]
  );

  // Mission evaluations
  const dailyMissions = useMemo<MissionProgressItem[]>(() => {
    const d = companion.daily;
    const claimedSet = new Set(d.claimedMissions);

    const m1Done = d.practicedQids.length >= 5;
    const m2Done = d.masteredQids.length >= 3 || d.bigQuestionQids.length >= 1;
    const m3Done = d.wrongClearedQids.length >= 2 || d.noteQids.length >= 1;
    const m4Done = d.formulaFlippedIds.length >= 5;
    const firstFourDone = [m1Done, m2Done, m3Done, m4Done].filter(Boolean).length;

    return DAILY_MISSIONS.map((def) => {
      if (def.id === 'daily_practice_5') {
        const cur = Math.min(5, d.practicedQids.length);
        return {
          ...def,
          current: cur,
          progressText: `${cur} / 5 题`,
          done: m1Done,
          claimed: claimedSet.has(def.id),
        };
      }
      if (def.id === 'daily_master_or_big') {
        return {
          ...def,
          current: m2Done ? 1 : 0,
          progressText: m2Done
            ? '已达成'
            : `掌握 ${Math.min(3, d.masteredQids.length)}/3 题 或 大题 ${Math.min(1, d.bigQuestionQids.length)}/1`,
          done: m2Done,
          claimed: claimedSet.has(def.id),
        };
      }
      if (def.id === 'daily_wrong_or_note') {
        return {
          ...def,
          current: m3Done ? 1 : 0,
          progressText: m3Done
            ? '已达成'
            : `斩错题 ${Math.min(2, d.wrongClearedQids.length)}/2 或 笔记 ${Math.min(1, d.noteQids.length)}/1`,
          done: m3Done,
          claimed: claimedSet.has(def.id),
        };
      }
      if (def.id === 'daily_formula_5') {
        const cur = Math.min(5, d.formulaFlippedIds.length);
        return {
          ...def,
          current: cur,
          progressText: `${cur} / 5 组`,
          done: m4Done,
          claimed: claimedSet.has(def.id),
        };
      }
      const cur = Math.min(3, firstFourDone);
      return {
        ...def,
        current: cur,
        progressText: `${cur} / 3 项`,
        done: firstFourDone >= 3,
        claimed: claimedSet.has(def.id),
      };
    });
  }, [companion.daily]);

  const weeklyMissions = useMemo<MissionProgressItem[]>(() => {
    const w = companion.weekly;
    const claimedSet = new Set(w.claimedMissions);
    return WEEKLY_MISSIONS.map((def) => {
      if (def.id === 'weekly_practice_40') {
        const cur = Math.min(40, w.practicedQids.length);
        return {
          ...def,
          current: cur,
          progressText: `${cur} / 40 题`,
          done: w.practicedQids.length >= 40,
          claimed: claimedSet.has(def.id),
        };
      }
      if (def.id === 'weekly_mock_1') {
        const cur = Math.min(1, w.mockCount);
        return {
          ...def,
          current: cur,
          progressText: `${cur} / 1 场`,
          done: w.mockCount >= 1,
          claimed: claimedSet.has(def.id),
        };
      }
      const cur = Math.min(5, w.activeDays.length);
      return {
        ...def,
        current: cur,
        progressText: `${cur} / 5 天`,
        done: w.activeDays.length >= 5,
        claimed: claimedSet.has(def.id),
      };
    });
  }, [companion.weekly]);

  const unlockedCodexCount = useMemo(
    () =>
      Object.entries(companion.ownedCards).filter(
        ([cid, cnt]) => !cid.startsWith('sp:') && cnt > 0
      ).length,
    [companion.ownedCards]
  );

  const achievements = useMemo<AchievementProgressItem[]>(() => {
    let practicedTotal = 0;
    let masteredTotal = 0;
    let mockTotal = 0;
    Object.values(allCourses).forEach((slice) => {
      if (!slice) return;
      mockTotal += Array.isArray(slice.mockHistory) ? slice.mockHistory.length : 0;
      Object.values(slice.records ?? {}).forEach((rec) => {
        if (rec.status !== 'unseen') practicedTotal++;
        if (rec.status === 'mastered') masteredTotal++;
      });
    });

    const claimedSet = new Set(companion.claimedAchievements);
    return ACHIEVEMENTS.map((def) => {
      let raw = 0;
      if (def.id === 'ach_first_q') raw = practicedTotal;
      else if (def.category === 'study') raw = masteredTotal;
      else if (def.category === 'mock') raw = mockTotal;
      else if (def.category === 'codex') raw = unlockedCodexCount;

      const cur = Math.min(def.target, raw);
      return {
        ...def,
        current: cur,
        done: raw >= def.target,
        claimed: claimedSet.has(def.id),
      };
    });
  }, [allCourses, companion.claimedAchievements, unlockedCodexCount]);

  const claimableCount = useMemo(() => {
    let cnt = companion.daily.checkedIn ? 0 : 1;
    cnt += dailyMissions.filter((m) => m.done && !m.claimed).length;
    cnt += weeklyMissions.filter((m) => m.done && !m.claimed).length;
    cnt += achievements.filter((a) => a.done && !a.claimed).length;
    return cnt;
  }, [achievements, companion.daily.checkedIn, dailyMissions, weeklyMissions]);

  // Actions
  const dailyCheckIn = useCallback(() => {
    const today = getLocalDateKey();
    const yesterday = getPrevLocalDateKey();
    const snapshot = normalizeCompanionPeriods(companionRef.current);
    const guardKey = `checkin:${today}`;
    if (snapshot.daily.checkedIn || claimedGuardRef.current.has(guardKey)) {
      return { ok: false, reward: 0, streak: snapshot.checkInStreak };
    }
    claimedGuardRef.current.add(guardKey);
    const nextStreak =
      snapshot.lastCheckInDate === yesterday ? snapshot.checkInStreak + 1 : 1;
    const reward = CHECKIN_REWARDS[(nextStreak - 1) % CHECKIN_REWARDS.length];
    companionRef.current = {
      ...snapshot,
      fish: snapshot.fish + reward,
      checkInStreak: nextStreak,
      lastCheckInDate: today,
      daily: { ...snapshot.daily, checkedIn: true },
    };

    setCompanionState((prevRaw) => {
      const cur = normalizeCompanionPeriods(prevRaw);
      if (cur.daily.checkedIn) return cur;
      return {
        ...cur,
        fish: cur.fish + reward,
        checkInStreak: nextStreak,
        lastCheckInDate: today,
        daily: { ...cur.daily, checkedIn: true },
        weekly: {
          ...cur.weekly,
          activeDays: appendUnique(cur.weekly.activeDays, today),
        },
      };
    });

    pushToast({
      title: `每日签到成功 · 连续第 ${nextStreak} 天`,
      subtitle: '保持每日刷题节奏，第 7 天可领 +100 鱼干大奖',
      fishDelta: reward,
      tone: 'gold',
    });
    return { ok: true, reward, streak: nextStreak };
  }, [pushToast, setCompanionState]);

  const claimDailyMission = useCallback(
    (id: string): boolean => {
      const target = dailyMissions.find((m) => m.id === id);
      const snapshot = normalizeCompanionPeriods(companionRef.current);
      const guardKey = `daily:${snapshot.daily.date}:${id}`;
      if (
        !target ||
        !target.done ||
        target.claimed ||
        snapshot.daily.claimedMissions.includes(id) ||
        claimedGuardRef.current.has(guardKey)
      ) {
        return false;
      }
      claimedGuardRef.current.add(guardKey);
      companionRef.current = {
        ...snapshot,
        fish: snapshot.fish + target.rewardFish,
        daily: {
          ...snapshot.daily,
          claimedMissions: [...snapshot.daily.claimedMissions, id],
        },
      };
      setCompanionState((prevRaw) => {
        const cur = normalizeCompanionPeriods(prevRaw);
        if (cur.daily.claimedMissions.includes(id)) return cur;
        return {
          ...cur,
          fish: cur.fish + target.rewardFish,
          daily: {
            ...cur.daily,
            claimedMissions: [...cur.daily.claimedMissions, id],
          },
        };
      });
      pushToast({
        title: `每日任务完成：${target.title}`,
        fishDelta: target.rewardFish,
        tone: 'gold',
      });
      return true;
    },
    [dailyMissions, pushToast, setCompanionState]
  );

  const claimWeeklyMission = useCallback(
    (id: string): boolean => {
      const target = weeklyMissions.find((m) => m.id === id);
      const snapshot = normalizeCompanionPeriods(companionRef.current);
      const guardKey = `weekly:${snapshot.weekly.weekKey}:${id}`;
      if (
        !target ||
        !target.done ||
        target.claimed ||
        snapshot.weekly.claimedMissions.includes(id) ||
        claimedGuardRef.current.has(guardKey)
      ) {
        return false;
      }
      claimedGuardRef.current.add(guardKey);
      companionRef.current = {
        ...snapshot,
        fish: snapshot.fish + target.rewardFish,
        weekly: {
          ...snapshot.weekly,
          claimedMissions: [...snapshot.weekly.claimedMissions, id],
        },
      };
      setCompanionState((prevRaw) => {
        const cur = normalizeCompanionPeriods(prevRaw);
        if (cur.weekly.claimedMissions.includes(id)) return cur;
        return {
          ...cur,
          fish: cur.fish + target.rewardFish,
          weekly: {
            ...cur.weekly,
            claimedMissions: [...cur.weekly.claimedMissions, id],
          },
        };
      });
      pushToast({
        title: `周常挑战达成：${target.title}`,
        fishDelta: target.rewardFish,
        tone: 'gold',
      });
      return true;
    },
    [pushToast, setCompanionState, weeklyMissions]
  );

  const claimAchievement = useCallback(
    (id: string): boolean => {
      const target = achievements.find((a) => a.id === id);
      const snapshot = normalizeCompanionPeriods(companionRef.current);
      const guardKey = `ach:${id}`;
      if (
        !target ||
        !target.done ||
        target.claimed ||
        snapshot.claimedAchievements.includes(id) ||
        claimedGuardRef.current.has(guardKey)
      ) {
        return false;
      }
      claimedGuardRef.current.add(guardKey);
      companionRef.current = {
        ...snapshot,
        fish: snapshot.fish + target.rewardFish,
        claimedAchievements: [...snapshot.claimedAchievements, id],
      };
      setCompanionState((prevRaw) => {
        const cur = normalizeCompanionPeriods(prevRaw);
        if (cur.claimedAchievements.includes(id)) return cur;
        return {
          ...cur,
          fish: cur.fish + target.rewardFish,
          claimedAchievements: [...cur.claimedAchievements, id],
        };
      });
      pushToast({
        title: `里程碑解锁：${target.title}`,
        fishDelta: target.rewardFish,
        tone: 'gold',
      });
      return true;
    },
    [achievements, pushToast, setCompanionState]
  );

  const claimAllRewards = useCallback(() => {
    const today = getLocalDateKey();
    const yesterday = getPrevLocalDateKey();
    const snapshot = normalizeCompanionPeriods(companionRef.current);
    const checkinKey = `checkin:${today}`;
    const willCheckIn = !snapshot.daily.checkedIn && !claimedGuardRef.current.has(checkinKey);
    const nextStreak = willCheckIn
      ? snapshot.lastCheckInDate === yesterday
        ? snapshot.checkInStreak + 1
        : 1
      : snapshot.checkInStreak;
    const checkInReward = willCheckIn
      ? CHECKIN_REWARDS[(nextStreak - 1) % CHECKIN_REWARDS.length]
      : 0;

    const readyDaily = dailyMissions.filter(
      (m) =>
        m.done &&
        !m.claimed &&
        !snapshot.daily.claimedMissions.includes(m.id) &&
        !claimedGuardRef.current.has(`daily:${snapshot.daily.date}:${m.id}`)
    );
    const readyWeekly = weeklyMissions.filter(
      (m) =>
        m.done &&
        !m.claimed &&
        !snapshot.weekly.claimedMissions.includes(m.id) &&
        !claimedGuardRef.current.has(`weekly:${snapshot.weekly.weekKey}:${m.id}`)
    );
    const readyAch = achievements.filter(
      (a) =>
        a.done &&
        !a.claimed &&
        !snapshot.claimedAchievements.includes(a.id) &&
        !claimedGuardRef.current.has(`ach:${a.id}`)
    );

    const claimed =
      (willCheckIn ? 1 : 0) + readyDaily.length + readyWeekly.length + readyAch.length;
    const fishGained =
      checkInReward +
      readyDaily.reduce((s, m) => s + m.rewardFish, 0) +
      readyWeekly.reduce((s, m) => s + m.rewardFish, 0) +
      readyAch.reduce((s, a) => s + a.rewardFish, 0);

    if (claimed === 0) return { claimed: 0, fishGained: 0 };

    if (willCheckIn) claimedGuardRef.current.add(checkinKey);
    readyDaily.forEach((m) => claimedGuardRef.current.add(`daily:${snapshot.daily.date}:${m.id}`));
    readyWeekly.forEach((m) =>
      claimedGuardRef.current.add(`weekly:${snapshot.weekly.weekKey}:${m.id}`)
    );
    readyAch.forEach((a) => claimedGuardRef.current.add(`ach:${a.id}`));

    companionRef.current = {
      ...snapshot,
      fish: snapshot.fish + fishGained,
      checkInStreak: nextStreak,
      lastCheckInDate: willCheckIn ? today : snapshot.lastCheckInDate,
      daily: {
        ...snapshot.daily,
        checkedIn: snapshot.daily.checkedIn || willCheckIn,
        claimedMissions: [...snapshot.daily.claimedMissions, ...readyDaily.map((m) => m.id)],
      },
      weekly: {
        ...snapshot.weekly,
        claimedMissions: [...snapshot.weekly.claimedMissions, ...readyWeekly.map((m) => m.id)],
      },
      claimedAchievements: [...snapshot.claimedAchievements, ...readyAch.map((a) => a.id)],
    };

    setCompanionState((prevRaw) => {
      const cur = normalizeCompanionPeriods(prevRaw);
      let nextFish = cur.fish;
      let streakOut = cur.checkInStreak;
      let lastCheckOut = cur.lastCheckInDate;
      const daily = { ...cur.daily, claimedMissions: [...cur.daily.claimedMissions] };
      const weekly = { ...cur.weekly, claimedMissions: [...cur.weekly.claimedMissions] };
      const claimedAchievements = [...cur.claimedAchievements];

      if (willCheckIn && !daily.checkedIn) {
        streakOut = cur.lastCheckInDate === yesterday ? cur.checkInStreak + 1 : 1;
        lastCheckOut = today;
        const r = CHECKIN_REWARDS[(streakOut - 1) % CHECKIN_REWARDS.length];
        nextFish += r;
        daily.checkedIn = true;
        weekly.activeDays = appendUnique(weekly.activeDays, today);
      }

      for (const m of readyDaily) {
        if (!daily.claimedMissions.includes(m.id)) {
          daily.claimedMissions.push(m.id);
          nextFish += m.rewardFish;
        }
      }
      for (const m of readyWeekly) {
        if (!weekly.claimedMissions.includes(m.id)) {
          weekly.claimedMissions.push(m.id);
          nextFish += m.rewardFish;
        }
      }
      for (const a of readyAch) {
        if (!claimedAchievements.includes(a.id)) {
          claimedAchievements.push(a.id);
          nextFish += a.rewardFish;
        }
      }

      return {
        ...cur,
        fish: nextFish,
        checkInStreak: streakOut,
        lastCheckInDate: lastCheckOut,
        daily,
        weekly,
        claimedAchievements,
      };
    });

    pushToast({
      title: `一键领取 ${claimed} 项奖励`,
      fishDelta: fishGained,
      tone: 'gold',
    });
    return { claimed, fishGained };
  }, [achievements, dailyMissions, pushToast, setCompanionState, weeklyMissions]);

  const openPack = useCallback(
    (
      packId: PackId,
      targetVariant: CardVariant = 'standard'
    ): { ok: boolean; message?: string; result?: PackOpenResult } => {
      if (!catalog || catalog.characters.length === 0) {
        return { ok: false, message: '角色图鉴数据仍在加载中，请稍候再试。' };
      }
      const packDef = PACK_DEFS.find((p) => p.id === packId);
      if (!packDef) return { ok: false, message: '未知卡包类型' };

      const curSnapshot = normalizeCompanionPeriods(companionRef.current);
      if (curSnapshot.fish < packDef.costFish) {
        return {
          ok: false,
          message: `小鱼干不足（需要 ${packDef.costFish}，当前 ${curSnapshot.fish}）`,
        };
      }

      // Build candidate pools by variant/rarity
      const poolByVariant: Record<CardVariant, Array<{ char: CodexCharacter; variant: CardVariant }>> = {
        chibi: catalog.characters.map((char) => ({ char, variant: 'chibi' })),
        medium: catalog.characters.map((char) => ({ char, variant: 'medium' })),
        standard: catalog.characters.map((char) => ({ char, variant: 'standard' })),
      };

      const tempOwned = { ...curSnapshot.ownedCards };
      let pity = curSnapshot.pityCounter;

      // Determine rarities / variants for each slot
      const slotVariants: CardVariant[] = [];
      for (let i = 0; i < packDef.cardCount; i++) {
        if (packId === 'variant' && targetVariant === 'chibi') {
          slotVariants.push('chibi');
          continue;
        }

        // Check 10-pull SSR hard pity
        if (pity >= 9) {
          slotVariants.push('standard');
          pity = 0;
          continue;
        }

        let weights: Array<{ item: CardVariant; weight: number }>;
        if (packId === 'starter') {
          weights = [
            { item: 'chibi', weight: 60 },
            { item: 'medium', weight: 32 },
            { item: 'standard', weight: 8 },
          ];
        } else if (packId === 'deluxe') {
          weights = [
            { item: 'chibi', weight: 35 },
            { item: 'medium', weight: 45 },
            { item: 'standard', weight: 20 },
          ];
        } else if (targetVariant === 'medium') {
          weights = [
            { item: 'chibi', weight: 25 },
            { item: 'medium', weight: 65 },
            { item: 'standard', weight: 10 },
          ];
        } else {
          // standard UP
          weights = [
            { item: 'chibi', weight: 34 },
            { item: 'medium', weight: 28 },
            { item: 'standard', weight: 38 },
          ];
        }

        const pickedVar = pickWeighted(weights);
        slotVariants.push(pickedVar);
        if (pickedVar === 'standard') pity = 0;
        else pity += 1;
      }

      // Apply pack guarantees cleanly
      if (packId === 'starter' && !slotVariants.some((v) => v === 'medium' || v === 'standard')) {
        slotVariants[slotVariants.length - 1] = 'medium';
      } else if (packId === 'deluxe' && !slotVariants.includes('standard')) {
        slotVariants[slotVariants.length - 1] = 'standard';
        pity = 0;
      } else if (packId === 'variant' && targetVariant === 'medium' && !slotVariants.some((v) => v === 'medium' || v === 'standard')) {
        slotVariants[slotVariants.length - 1] = 'medium';
      } else if (packId === 'variant' && targetVariant === 'standard' && !slotVariants.some((v) => v === 'medium' || v === 'standard')) {
        slotVariants[slotVariants.length - 1] = 'medium';
      }

      const pulls: PullResultItem[] = [];
      let totalRefundFish = 0;
      let totalRefundVouchers = 0;
      const bondIncrements: Record<string, number> = {};
      const cardIncrements: Record<string, number> = {};

      for (const v of slotVariants) {
        const candidates = poolByVariant[v];
        const unownedWeight = packId === 'variant' && targetVariant === 'chibi' ? 6.0 : 3.5;
        const chosen = pickWeighted(
          candidates.map((entry) => {
            const cardId = entry.char.variants[entry.variant].cardId;
            const isOwned = (tempOwned[cardId] ?? 0) > 0;
            return { item: entry, weight: isOwned ? 1.0 : unownedWeight };
          })
        );

        const asset = chosen.char.variants[chosen.variant];
        const wasOwned = (tempOwned[asset.cardId] ?? 0) > 0;
        tempOwned[asset.cardId] = (tempOwned[asset.cardId] ?? 0) + 1;
        cardIncrements[asset.cardId] = (cardIncrements[asset.cardId] ?? 0) + 1;

        let refundFish = 0;
        let refundBond = 0;
        let refundVouchers = 0;
        if (wasOwned) {
          const ref = DUPLICATE_REFUND[asset.rarity];
          refundFish = ref.fish;
          refundBond = ref.bond;
          refundVouchers = ref.vouchers;
          totalRefundFish += refundFish;
          totalRefundVouchers += refundVouchers;
          bondIncrements[chosen.char.id] = (bondIncrements[chosen.char.id] ?? 0) + refundBond;
        }

        pulls.push({
          cardId: asset.cardId,
          charId: chosen.char.id,
          charName: chosen.char.name,
          subtitle: chosen.char.subtitle,
          variant: chosen.variant,
          variantLabel: VARIANT_LABELS[chosen.variant],
          rarity: asset.rarity,
          color: chosen.char.color,
          sprite: asset.sprite,
          avatar: asset.avatar,
          isNew: !wasOwned,
          refundFish,
          refundBond,
          refundVouchers,
        });
      }

      const bonusVouchers = packId === 'variant' && targetVariant === 'chibi' ? 1 : 0;

      // Update synchronous snapshot for rapid double-click guard
      const nextBondsSnap = { ...curSnapshot.bonds };
      Object.entries(bondIncrements).forEach(([bk, inc]) => {
        nextBondsSnap[bk] = (nextBondsSnap[bk] ?? 0) + inc;
      });
      companionRef.current = {
        ...curSnapshot,
        fish: curSnapshot.fish - packDef.costFish + totalRefundFish,
        vouchers: curSnapshot.vouchers + totalRefundVouchers + bonusVouchers,
        totalPacksOpened: curSnapshot.totalPacksOpened + 1,
        pityCounter: pity,
        ownedCards: tempOwned,
        bonds: nextBondsSnap,
      };

      setCompanionState((prevRaw) => {
        const cur = normalizeCompanionPeriods(prevRaw);
        if (cur.fish < packDef.costFish) return cur;
        const nextOwned = { ...cur.ownedCards };
        Object.entries(cardIncrements).forEach(([cid, inc]) => {
          nextOwned[cid] = (nextOwned[cid] ?? 0) + inc;
        });
        const nextBonds = { ...cur.bonds };
        Object.entries(bondIncrements).forEach(([bk, inc]) => {
          nextBonds[bk] = (nextBonds[bk] ?? 0) + inc;
        });
        return {
          ...cur,
          fish: cur.fish - packDef.costFish + totalRefundFish,
          vouchers: cur.vouchers + totalRefundVouchers + bonusVouchers,
          totalPacksOpened: cur.totalPacksOpened + 1,
          pityCounter: pity,
          ownedCards: nextOwned,
          bonds: nextBonds,
        };
      });

      const packName =
        packId === 'variant'
          ? `${packDef.name}（${VARIANT_LABELS[targetVariant].split(' ')[0]}）`
          : packDef.name;

      return {
        ok: true,
        result: {
          packId,
          packName,
          pulls,
          bonusVouchers,
          totalRefundFish,
          totalRefundVouchers,
        },
      };
    },
    [catalog, setCompanionState]
  );

  const redeemSelector = useCallback(
    (cardId: string, payWith: 'fish' | 'vouchers'): { ok: boolean; message: string } => {
      if (!catalog) return { ok: false, message: '图鉴尚未加载完成' };
      const cur = normalizeCompanionPeriods(companionRef.current);
      if ((cur.ownedCards[cardId] ?? 0) > 0) {
        return { ok: false, message: '该卡片已收录，无需重复兑换' };
      }
      if (payWith === 'fish' && cur.fish < SELECTOR_COST_FISH) {
        return { ok: false, message: `小鱼干不足（需要 ${SELECTOR_COST_FISH}）` };
      }
      if (payWith === 'vouchers' && cur.vouchers < SELECTOR_COST_VOUCHERS) {
        return { ok: false, message: `寻访凭证不足（需要 ${SELECTOR_COST_VOUCHERS}）` };
      }

      const [charId, variant] = cardId.split(':') as [string, CardVariant];
      const char = catalog.characters.find((c) => c.id === charId);
      if (!char || !char.variants[variant]) {
        return { ok: false, message: '无效卡片编号' };
      }

      companionRef.current = {
        ...cur,
        fish: payWith === 'fish' ? cur.fish - SELECTOR_COST_FISH : cur.fish,
        vouchers: payWith === 'vouchers' ? cur.vouchers - SELECTOR_COST_VOUCHERS : cur.vouchers,
        ownedCards: { ...cur.ownedCards, [cardId]: 1 },
      };

      setCompanionState((prevRaw) => {
        const prev = normalizeCompanionPeriods(prevRaw);
        if ((prev.ownedCards[cardId] ?? 0) > 0) return prev;
        if (payWith === 'fish' && prev.fish < SELECTOR_COST_FISH) return prev;
        if (payWith === 'vouchers' && prev.vouchers < SELECTOR_COST_VOUCHERS) return prev;
        return {
          ...prev,
          fish: payWith === 'fish' ? prev.fish - SELECTOR_COST_FISH : prev.fish,
          vouchers: payWith === 'vouchers' ? prev.vouchers - SELECTOR_COST_VOUCHERS : prev.vouchers,
          ownedCards: { ...prev.ownedCards, [cardId]: 1 },
        };
      });

      pushToast({
        title: `定向解锁成功：${char.name}（${char.variants[variant].label}）`,
        subtitle: '可在「角色图鉴」设为看板娘！',
        tone: 'gold',
      });
      return { ok: true, message: `已成功解锁「${char.name} · ${char.variants[variant].label}」` };
    },
    [catalog, pushToast, setCompanionState]
  );

  const giftCharacter = useCallback(
    (charOrCardId: string, giftId: string): { ok: boolean; message: string } => {
      const gift = GIFT_ITEMS.find((g) => g.id === giftId);
      if (!gift) return { ok: false, message: '礼物不存在' };
      const cur = normalizeCompanionPeriods(companionRef.current);
      if (cur.fish < gift.costFish) {
        return { ok: false, message: `小鱼干不足（需要 ${gift.costFish}）` };
      }

      const bondKey = resolveBondKey(charOrCardId);
      const prevXp = cur.bonds[bondKey] ?? 0;
      const prevLv = getBondLevelInfo(prevXp).level;
      const nextXp = prevXp + gift.bondGain;
      const nextLv = getBondLevelInfo(nextXp).level;

      companionRef.current = {
        ...cur,
        fish: cur.fish - gift.costFish,
        bonds: { ...cur.bonds, [bondKey]: nextXp },
      };

      setCompanionState((prevRaw) => {
        const prev = normalizeCompanionPeriods(prevRaw);
        if (prev.fish < gift.costFish) return prev;
        return {
          ...prev,
          fish: prev.fish - gift.costFish,
          bonds: {
            ...prev.bonds,
            [bondKey]: (prev.bonds[bondKey] ?? 0) + gift.bondGain,
          },
        };
      });

      pushToast({
        title: `投喂「${gift.name}」成功`,
        subtitle:
          nextLv > prevLv
            ? `信赖度 +${gift.bondGain} · 升级至 Lv.${nextLv}！`
            : `信赖度 +${gift.bondGain}`,
        tone: nextLv > prevLv ? 'gold' : 'ok',
      });
      return { ok: true, message: `信赖度 +${gift.bondGain}` };
    },
    [pushToast, setCompanionState]
  );

  const interactWithMascot = useCallback(() => {
    const cur = normalizeCompanionPeriods(companionRef.current);
    const guardKey = `interact:${cur.daily.date}`;
    if (cur.daily.mascotInteracted || claimedGuardRef.current.has(guardKey)) {
      return { granted: false, fishGain: 0, bondGain: 0 };
    }
    claimedGuardRef.current.add(guardKey);
    const fishGain = 10;
    const bondGain = 5;
    const bk = resolveBondKey(cur.equippedCardId);

    companionRef.current = {
      ...cur,
      fish: cur.fish + fishGain,
      bonds: { ...cur.bonds, [bk]: (cur.bonds[bk] ?? 0) + bondGain },
      daily: { ...cur.daily, mascotInteracted: true },
    };

    setCompanionState((prevRaw) => {
      const prev = normalizeCompanionPeriods(prevRaw);
      if (prev.daily.mascotInteracted) return prev;
      const prevBk = resolveBondKey(prev.equippedCardId);
      return {
        ...prev,
        fish: prev.fish + fishGain,
        bonds: { ...prev.bonds, [prevBk]: (prev.bonds[prevBk] ?? 0) + bondGain },
        daily: { ...prev.daily, mascotInteracted: true },
      };
    });

    pushToast({
      title: '每日看板娘互动',
      subtitle: `默契信赖 +${bondGain}`,
      fishDelta: fishGain,
      tone: 'ok',
    });
    return { granted: true, fishGain, bondGain };
  }, [pushToast, setCompanionState]);

  const equipMascot = useCallback(
    (cardId: string) => {
      const snapshot = normalizeCompanionPeriods(companionRef.current);
      if ((snapshot.ownedCards[cardId] ?? 0) <= 0 || snapshot.equippedCardId === cardId) {
        return;
      }

      let displayName = cardId;
      if (catalog) {
        if (cardId.startsWith('sp:')) {
          const sp = catalog.spCards.find((s) => s.id === cardId);
          if (sp) displayName = sp.name.replace(/（.*?）/, '');
        } else {
          const [cid, variant] = cardId.split(':') as [string, CardVariant];
          const ch = catalog.characters.find((c) => c.id === cid);
          const vLabel = ch?.variants?.[variant]?.label;
          if (ch) displayName = vLabel ? `${ch.name} · ${vLabel}` : ch.name;
        }
      }

      companionRef.current = { ...snapshot, equippedCardId: cardId };

      setCompanionState((prevRaw) => {
        const cur = normalizeCompanionPeriods(prevRaw);
        if ((cur.ownedCards[cardId] ?? 0) <= 0 || cur.equippedCardId === cardId) return cur;
        return { ...cur, equippedCardId: cardId };
      });

      pushToast({
        title: `已委任「${displayName}」为看板娘`,
        subtitle: snapshot.applyGlobally ? '已同步至全站看板娘位置' : '已切换首页看板娘展台',
        tone: 'ok',
      });
    },
    [catalog, pushToast, setCompanionState]
  );

  const setApplyGlobally = useCallback(
    (val: boolean) => {
      setCompanionState((prevRaw) => {
        const cur = normalizeCompanionPeriods(prevRaw);
        return { ...cur, applyGlobally: val };
      });
    },
    [setCompanionState]
  );

  const buyFrame = useCallback(
    (frameId: StageFrameId): { ok: boolean; message: string } => {
      const def = STAGE_FRAMES.find((f) => f.id === frameId);
      if (!def) return { ok: false, message: '展台边框不存在' };
      const cur = normalizeCompanionPeriods(companionRef.current);
      if (cur.ownedFrames.includes(frameId)) {
        companionRef.current = { ...cur, equippedFrame: frameId };
        setCompanionState((prevRaw) => ({
          ...normalizeCompanionPeriods(prevRaw),
          equippedFrame: frameId,
        }));
        return { ok: true, message: `已切换展台边框为「${def.name}」` };
      }
      if (cur.fish < def.costFish) {
        return { ok: false, message: `小鱼干不足（需要 ${def.costFish}）` };
      }
      companionRef.current = {
        ...cur,
        fish: cur.fish - def.costFish,
        ownedFrames: [...cur.ownedFrames, frameId],
        equippedFrame: frameId,
      };
      setCompanionState((prevRaw) => {
        const prev = normalizeCompanionPeriods(prevRaw);
        if (prev.ownedFrames.includes(frameId)) {
          return { ...prev, equippedFrame: frameId };
        }
        if (prev.fish < def.costFish) return prev;
        return {
          ...prev,
          fish: prev.fish - def.costFish,
          ownedFrames: [...prev.ownedFrames, frameId],
          equippedFrame: frameId,
        };
      });
      pushToast({
        title: `解锁并装备展台边框：${def.name}`,
        tone: 'gold',
      });
      return { ok: true, message: `已解锁并装备「${def.name}」` };
    },
    [pushToast, setCompanionState]
  );

  const equipFrame = useCallback(
    (frameId: StageFrameId) => {
      setCompanionState((prevRaw) => {
        const cur = normalizeCompanionPeriods(prevRaw);
        if (!cur.ownedFrames.includes(frameId)) return cur;
        return { ...cur, equippedFrame: frameId };
      });
    },
    [setCompanionState]
  );

  const getCardCount = useCallback(
    (cardId: string) => companion.ownedCards[cardId] ?? 0,
    [companion.ownedCards]
  );

  const activeMascot = useMemo<ActiveMascotInfo>(() => {
    const eqId = companion.equippedCardId || 'sp:dafeyu';
    const bondKey = resolveBondKey(eqId);
    const bondXp = companion.bonds[bondKey] ?? 0;
    const bondLevel = getBondLevelInfo(bondXp).level;

    if (!catalog) {
      return { ...DEFAULT_DF_INFO, bondXp, bondLevel };
    }

    if (eqId.startsWith('sp:')) {
      const sp: CodexSpCard | undefined = catalog.spCards.find((s) => s.id === eqId);
      if (sp) {
        return {
          cardId: sp.id,
          bondKey,
          isDefaultDafeyu: sp.id === 'sp:dafeyu',
          isSp: true,
          code: sp.code,
          name: sp.name.replace(/（.*?）/, ''),
          subtitle: sp.subtitle,
          rarity: 'SP',
          variantLabel: sp.id === 'sp:dafeyu' ? '四姿态' : '协研特绘',
          color: sp.color,
          sprite: sp.sprite,
          avatar: sp.avatar,
          bondXp,
          bondLevel,
          greetTemplate: sp.greetTemplate,
          judgeOkQuote: sp.judgeOkQuote,
          judgeWarnQuote: sp.judgeWarnQuote,
          studyQuotes: sp.studyQuotes,
        };
      }
      return { ...DEFAULT_DF_INFO, bondXp, bondLevel };
    }

    const [charId, variant] = eqId.split(':') as [string, CardVariant];
    const char = catalog.characters.find((c) => c.id === charId);
    const asset = char?.variants?.[variant];
    if (char && asset) {
      return {
        cardId: asset.cardId,
        bondKey,
        isDefaultDafeyu: false,
        isSp: false,
        code: char.code,
        name: char.name,
        subtitle: char.subtitle,
        rarity: asset.rarity,
        variantLabel: asset.label,
        color: char.color,
        sprite: asset.sprite,
        avatar: asset.avatar,
        bondXp,
        bondLevel,
        greetTemplate: char.greetTemplate,
        judgeOkQuote: char.judgeOkQuote,
        judgeWarnQuote: char.judgeWarnQuote,
        studyQuotes: char.studyQuotes,
      };
    }

    return { ...DEFAULT_DF_INFO, bondXp, bondLevel };
  }, [catalog, companion.bonds, companion.equippedCardId]);

  return (
    <CompanionContext.Provider
      value={{
        catalog,
        companion,
        activeMascot,
        dailyMissions,
        weeklyMissions,
        achievements,
        claimableCount,
        unlockedCodexCount,
        displayCheckInStreak,
        toasts,
        dismissToast,
        pushToast,
        getBondKey: resolveBondKey,
        getCardCount,
        dailyCheckIn,
        claimDailyMission,
        claimWeeklyMission,
        claimAchievement,
        claimAllRewards,
        openPack,
        redeemSelector,
        giftCharacter,
        interactWithMascot,
        equipMascot,
        setApplyGlobally,
        buyFrame,
        equipFrame,
        trackFormulaFlip,
      }}
    >
      {children}
    </CompanionContext.Provider>
  );
};

export function useCompanion(): CompanionContextValue {
  const ctx = useContext(CompanionContext);
  if (!ctx) throw new Error('useCompanion must be used inside CompanionProvider');
  return ctx;
}

export function useCompanionOptional(): CompanionContextValue | null {
  return useContext(CompanionContext);
}
