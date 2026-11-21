import type { CardRarity, CardVariant, StageFrameId } from '../types';

export const CHECKIN_REWARDS = [20, 20, 50, 20, 20, 30, 100] as const;

export interface MissionDef {
  id: string;
  title: string;
  desc: string;
  target: number;
  rewardFish: number;
  link?: string;
  linkLabel?: string;
}

export const DAILY_MISSIONS: MissionDef[] = [
  {
    id: 'daily_practice_5',
    title: '热身开刷',
    desc: '今日完成 5 道不重复真题作答',
    target: 5,
    rewardFish: 30,
    link: '/practice',
    linkLabel: '去刷题',
  },
  {
    id: 'daily_master_or_big',
    title: '深度攻克',
    desc: '今日掌握 3 道题 或 完成 1 道计算/推导大题',
    target: 1,
    rewardFish: 40,
    link: '/practice?type=calc',
    linkLabel: '练大题',
  },
  {
    id: 'daily_wrong_or_note',
    title: '错题清剿',
    desc: '今日斩除 2 道错题 或 写下 1 条真题笔记（≥8字）',
    target: 1,
    rewardFish: 35,
    link: '/wrong-book',
    linkLabel: '清错题',
  },
  {
    id: 'daily_formula_5',
    title: '公式抽背',
    desc: '在公式手册 3D 闪卡模式下翻面核对 5 组公式',
    target: 5,
    rewardFish: 25,
    link: '/formulas',
    linkLabel: '背公式',
  },
  {
    id: 'daily_all_3',
    title: '每日满勤补给箱',
    desc: '完成上述任意 3 项每日任务即可开启',
    target: 3,
    rewardFish: 50,
  },
];

export const WEEKLY_MISSIONS: MissionDef[] = [
  {
    id: 'weekly_practice_40',
    title: '周度题海巡航',
    desc: '本周累计完成 40 道不重复真题作答',
    target: 40,
    rewardFish: 120,
    link: '/practice',
    linkLabel: '去刷题',
  },
  {
    id: 'weekly_mock_1',
    title: '全真考场演练',
    desc: '本周完成 1 场 180 分钟全真限时模考并交卷',
    target: 1,
    rewardFish: 180,
    link: '/mock',
    linkLabel: '去模考',
  },
  {
    id: 'weekly_days_5',
    title: '五日勤学打卡',
    desc: '本周累计有 5 天产生刷题或签到学习记录',
    target: 5,
    rewardFish: 150,
  },
];

export interface AchievementDef {
  id: string;
  title: string;
  desc: string;
  category: 'study' | 'mock' | 'codex';
  target: number;
  rewardFish: number;
}

export const ACHIEVEMENTS: AchievementDef[] = [
  {
    id: 'ach_first_q',
    title: '初试锋芒',
    desc: '累计完成第 1 道考研真题',
    category: 'study',
    target: 1,
    rewardFish: 40,
  },
  {
    id: 'ach_master_10',
    title: '渐入佳境',
    desc: '全站累计「完全掌握」10 道真题',
    category: 'study',
    target: 10,
    rewardFish: 60,
  },
  {
    id: 'ach_master_50',
    title: '流体力学入门',
    desc: '全站累计「完全掌握」50 道真题',
    category: 'study',
    target: 50,
    rewardFish: 120,
  },
  {
    id: 'ach_master_150',
    title: '半壁江山',
    desc: '全站累计「完全掌握」150 道真题',
    category: 'study',
    target: 150,
    rewardFish: 200,
  },
  {
    id: 'ach_master_300',
    title: '题海宗师',
    desc: '全站累计「完全掌握」300 道真题',
    category: 'study',
    target: 300,
    rewardFish: 300,
  },
  {
    id: 'ach_first_mock',
    title: '全真初体验',
    desc: '完成第 1 场 180 分钟全真模拟考试',
    category: 'mock',
    target: 1,
    rewardFish: 120,
  },
  {
    id: 'ach_mock_3',
    title: '身经百战',
    desc: '累计完成 3 场全真模拟考试',
    category: 'mock',
    target: 3,
    rewardFish: 200,
  },
  {
    id: 'ach_codex_5',
    title: '初遇搭档',
    desc: '累计解锁 5 张图鉴卡片（不含 SP 初始卡）',
    category: 'codex',
    target: 5,
    rewardFish: 80,
  },
  {
    id: 'ach_codex_14',
    title: '星港齐聚',
    desc: '累计解锁 14 张图鉴卡片',
    category: 'codex',
    target: 14,
    rewardFish: 180,
  },
  {
    id: 'ach_codex_30',
    title: '跨形态收藏家',
    desc: '累计解锁 30 张图鉴卡片',
    category: 'codex',
    target: 30,
    rewardFish: 260,
  },
  {
    id: 'ach_codex_42',
    title: '全图鉴制霸',
    desc: '集齐全部 14 位角色 × 3 种形态（42/42）',
    category: 'codex',
    target: 42,
    rewardFish: 500,
  },
];

export type PackId = 'starter' | 'deluxe' | 'variant';

export interface PackDef {
  id: PackId;
  name: string;
  subtitle: string;
  costFish: number;
  cardCount: number;
  badge: string;
  guaranteeLabel: string;
  ratesLabel: string;
}

export const PACK_DEFS: PackDef[] = [
  {
    id: 'starter',
    name: '深海入门卡包',
    subtitle: '3 连寻访 · 每日日常即可轻松开包',
    costFish: 80,
    cardCount: 3,
    badge: 'STANDARD SUPPLY',
    guaranteeLabel: '保底 ≥ 1 张 SR 或 SSR',
    ratesLabel: 'R 60% / SR 32% / SSR 8%（10抽必出SSR）',
  },
  {
    id: 'deluxe',
    name: '星港典藏卡包',
    subtitle: '5 连寻访 · 直出标准版完整立绘',
    costFish: 200,
    cardCount: 5,
    badge: 'PREMIUM CRATE',
    guaranteeLabel: '保底 ≥ 1 张 SSR 标准版',
    ratesLabel: 'R 35% / SR 45% / SSR 20%（未收录高权重）',
  },
  {
    id: 'variant',
    name: '形态定向卡包',
    subtitle: '3 连定向 UP · 精准补全指定体型图鉴',
    costFish: 150,
    cardCount: 3,
    badge: 'TARGETED UP',
    guaranteeLabel: '可自选 Q版 / 中间体型 / 标准版 专场',
    ratesLabel: '所选形态概率大幅提升，含未收录权重倾斜',
  },
];

export const VARIANT_LABELS: Record<CardVariant, string> = {
  chibi: 'Q版 · R',
  medium: '中间体型版 · SR',
  standard: '标准版 · SSR',
};

export const VARIANT_RARITY: Record<CardVariant, 'R' | 'SR' | 'SSR'> = {
  chibi: 'R',
  medium: 'SR',
  standard: 'SSR',
};

export const SELECTOR_COST_FISH = 450;
export const SELECTOR_COST_VOUCHERS = 15;

export const DUPLICATE_REFUND: Record<
  'R' | 'SR' | 'SSR',
  { fish: number; bond: number; vouchers: number }
> = {
  R: { fish: 20, bond: 20, vouchers: 1 },
  SR: { fish: 45, bond: 40, vouchers: 2 },
  SSR: { fish: 100, bond: 80, vouchers: 3 },
};

export interface GiftItemDef {
  id: string;
  name: string;
  costFish: number;
  bondGain: number;
  desc: string;
}

export const GIFT_ITEMS: GiftItemDef[] = [
  {
    id: 'dried_fish',
    name: '烤小鱼干',
    costFish: 30,
    bondGain: 35,
    desc: '酥脆解馋的陪读零嘴，适合日常培养默契',
  },
  {
    id: 'study_tea',
    name: '书房热茶',
    costFish: 50,
    bondGain: 65,
    desc: '温热提神的熬夜刷题伴侣，大幅增加信赖度',
  },
  {
    id: 'blueprint_note',
    name: '蓝图手账本',
    costFish: 80,
    bondGain: 115,
    desc: 'PRTS 制式笔记本，记录并肩攻克真题的时光',
  },
];

export const BOND_LEVEL_THRESHOLDS = [0, 40, 100, 180, 280, 400, 550, 730, 950, 1200] as const;

export const BOND_PERKS: Array<{ level: number; label: string }> = [
  { level: 2, label: '解锁全套专属考研陪读语录' },
  { level: 4, label: '刷题判题气泡激活「默契连携」专属微光' },
  { level: 6, label: '主页展台解锁信赖流光徽章' },
  { level: 10, label: '满绊「上岸誓约」金色纪念印记' },
];

export function getBondLevelInfo(xp: number): {
  level: number;
  xp: number;
  currentFloor: number;
  nextFloor: number | null;
  progressPct: number;
} {
  let level = 1;
  for (let i = 0; i < BOND_LEVEL_THRESHOLDS.length; i++) {
    if (xp >= BOND_LEVEL_THRESHOLDS[i]) {
      level = i + 1;
    }
  }
  const currentFloor = BOND_LEVEL_THRESHOLDS[level - 1] ?? 0;
  const nextFloor =
    level < BOND_LEVEL_THRESHOLDS.length ? BOND_LEVEL_THRESHOLDS[level] : null;
  const progressPct =
    nextFloor === null
      ? 100
      : Math.min(100, Math.max(0, Math.round(((xp - currentFloor) / (nextFloor - currentFloor)) * 100)));
  return { level, xp, currentFloor, nextFloor, progressPct };
}

export interface StageFrameDef {
  id: StageFrameId;
  name: string;
  costFish: number;
  desc: string;
}

export const STAGE_FRAMES: StageFrameDef[] = [
  {
    id: 'default',
    name: 'PRTS 标准战术框',
    costFish: 0,
    desc: '默认深海工程终端双色角标边框',
  },
  {
    id: 'abyssal',
    name: '深海流线波纹',
    costFish: 120,
    desc: '青蓝水力学流线扫描与深海柔光边栏',
  },
  {
    id: 'starlight',
    name: '星港观测矩阵',
    costFish: 160,
    desc: '星芒紫青双色角标与点阵观测光晕',
  },
  {
    id: 'hazard',
    name: '罗德岛警戒条纹',
    costFish: 180,
    desc: '工业黄黑警戒带与高能作战台边框',
  },
];

export const RARITY_ORDER: Record<CardRarity, number> = {
  SP: 4,
  SSR: 3,
  SR: 2,
  R: 1,
};
