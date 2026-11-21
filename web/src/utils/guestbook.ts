import { BRAND } from '../brand';
import type { GuestbookCategory, GuestbookEntry } from '../types';

export const GUESTBOOK_CATEGORIES: Array<{
  id: GuestbookCategory;
  label: string;
  placeholder: string;
}> = [
  {
    id: 'checkin',
    label: '上岸打卡',
    placeholder: '写下今天的刷题收获、备考进度或给自己立一个上岸 Flag～',
  },
  {
    id: 'errata',
    label: '勘误反馈',
    placeholder: '请备注年份与题号（例如：河海 2018 第 21 题）及发现的公式/配图/解析问题…',
  },
  {
    id: 'wish',
    label: '新科目许愿',
    placeholder: '希望后续新增哪所院校的哪门专业课真题？（例如：某校 8xx 水力学/结构力学等）',
  },
  {
    id: 'chat',
    label: '学习交流',
    placeholder: '分享复习心得、解题技巧，或向同考场研友打个招呼吧！',
  },
];

export const GUESTBOOK_CATEGORY_LABELS: Record<GuestbookCategory, string> = {
  checkin: '上岸打卡',
  errata: '勘误反馈',
  wish: '新科目许愿',
  chat: '学习交流',
};

const LOCAL_ENTRIES_KEY = 'jingyan_guestbook_local_v1';
const LIKED_IDS_KEY = 'jingyan_guestbook_likes_v1';

export function loadLocalGuestbookEntries(): GuestbookEntry[] {
  try {
    const raw = localStorage.getItem(LOCAL_ENTRIES_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.map((item) => ({ ...item, isLocal: true }));
  } catch {
    return [];
  }
}

export function saveLocalGuestbookEntries(entries: GuestbookEntry[]): void {
  try {
    const stripped = entries.map((e) => ({ ...e, isLocal: true }));
    localStorage.setItem(LOCAL_ENTRIES_KEY, JSON.stringify(stripped));
  } catch {
    // ignore storage quota errors
  }
}

export function loadLikedIds(): string[] {
  try {
    const raw = localStorage.getItem(LIKED_IDS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((x): x is string => typeof x === 'string') : [];
  } catch {
    return [];
  }
}

export function toggleLikedId(id: string): string[] {
  const prev = loadLikedIds();
  const next = prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id];
  try {
    localStorage.setItem(LIKED_IDS_KEY, JSON.stringify(next));
  } catch {
    // ignore
  }
  return next;
}

export async function fetchSeedGuestbook(): Promise<GuestbookEntry[]> {
  const url = BRAND.guestbookApiUrl ? BRAND.guestbookApiUrl : './data/guestbook.json';
  try {
    const res = await fetch(url);
    if (!res.ok) return [];
    const data = await res.json();
    const list = Array.isArray(data) ? data : Array.isArray(data?.entries) ? data.entries : [];
    return list as GuestbookEntry[];
  } catch {
    return [];
  }
}

export function buildGuestbookMailto(entry: {
  author: string;
  category: GuestbookCategory;
  courseLabel: string;
  content: string;
}): string {
  const catLabel = GUESTBOOK_CATEGORY_LABELS[entry.category] || entry.category;
  const author = entry.author.trim() || '考研人';
  const subject = `[${BRAND.name}留言板·${catLabel}] 来自「${author}」（${entry.courseLabel}）`;
  const body = [
    `昵称：${author}`,
    `分类：${catLabel}`,
    `关联板块：${entry.courseLabel}`,
    '',
    '留言内容：',
    entry.content.trim(),
    '',
    '---',
    `（由「${BRAND.fullName}」留言板一键生成，QQ 交流群：${BRAND.qqGroup}）`,
  ].join('\n');
  return `mailto:${BRAND.contact}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}
