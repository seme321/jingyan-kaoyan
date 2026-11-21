import { BRAND } from '../brand';
import type {
  AdminGuestbookCounts,
  AdminGuestbookEntry,
  AdminGuestbookTab,
  GuestbookCategory,
  GuestbookChannel,
  GuestbookEntry,
  GuestbookStatus,
} from '../types';

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
const PENDING_ENTRIES_KEY = 'jingyan_guestbook_pending_v2';
const CLIENT_ID_KEY = 'jingyan_guestbook_client_id_v1';
const ADMIN_TOKEN_KEY = 'jingyan_admin_token_v1';

const SAFE_CLIENT_ID_RE = /^[a-zA-Z0-9_-]{8,64}$/;

export function getOrCreateGuestbookClientId(): string {
  try {
    const existing = localStorage.getItem(CLIENT_ID_KEY);
    if (existing && SAFE_CLIENT_ID_RE.test(existing)) {
      return existing;
    }
    const generated =
      typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
        ? `jy-${crypto.randomUUID()}`
        : `jy-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
    localStorage.setItem(CLIENT_ID_KEY, generated);
    return generated;
  } catch {
    return '';
  }
}

export function loadSavedAdminToken(): string {
  try {
    return sessionStorage.getItem(ADMIN_TOKEN_KEY) ?? '';
  } catch {
    return '';
  }
}

export function saveAdminToken(token: string): void {
  try {
    if (token) {
      sessionStorage.setItem(ADMIN_TOKEN_KEY, token);
    } else {
      sessionStorage.removeItem(ADMIN_TOKEN_KEY);
    }
  } catch {
    // ignore storage errors
  }
}

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

export function loadPendingGuestbookEntries(): GuestbookEntry[] {
  try {
    const raw = localStorage.getItem(PENDING_ENTRIES_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.map((item) => ({ ...item, isPendingLocal: true }));
  } catch {
    return [];
  }
}

export function savePendingGuestbookEntries(entries: GuestbookEntry[]): void {
  try {
    const stripped = entries.map((e) => ({ ...e, isPendingLocal: true }));
    localStorage.setItem(PENDING_ENTRIES_KEY, JSON.stringify(stripped));
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
  try {
    const res = await fetch('./data/guestbook.json');
    if (!res.ok) return [];
    const data = await res.json();
    const list = Array.isArray(data) ? data : Array.isArray(data?.entries) ? data.entries : [];
    return list as GuestbookEntry[];
  } catch {
    return [];
  }
}

export interface PublicGuestbookResult {
  entries: GuestbookEntry[];
  pendingStatuses: Record<string, { status: GuestbookStatus; channel: GuestbookChannel }>;
  likedIds: string[];
  online: boolean;
}

export async function fetchPublicGuestbook(
  pendingIds: string[],
  clientId: string
): Promise<PublicGuestbookResult> {
  if (BRAND.guestbookApiUrl) {
    try {
      const params = new URLSearchParams();
      if (clientId) params.set('clientId', clientId);
      if (pendingIds.length > 0) params.set('pendingIds', pendingIds.slice(0, 20).join(','));
      const query = params.toString();
      const url = query ? `${BRAND.guestbookApiUrl}?${query}` : BRAND.guestbookApiUrl;
      const res = await fetch(url, { cache: 'no-store' });
      const contentType = res.headers.get('content-type') ?? '';
      if (res.ok && contentType.includes('application/json')) {
        const data = await res.json();
        if (Array.isArray(data?.entries)) {
          return {
            entries: data.entries as GuestbookEntry[],
            pendingStatuses:
              (data.pendingStatuses as Record<
                string,
                { status: GuestbookStatus; channel: GuestbookChannel }
              >) ?? {},
            likedIds: Array.isArray(data.likedIds)
              ? data.likedIds.filter((x: unknown): x is string => typeof x === 'string')
              : [],
            online: true,
          };
        }
      }
    } catch {
      // fall through to offline seed JSON
    }
  }

  const seedEntries = await fetchSeedGuestbook();
  return {
    entries: seedEntries,
    pendingStatuses: {},
    likedIds: loadLikedIds(),
    online: false,
  };
}

export async function submitPublicGuestbook(payload: {
  author: string;
  category: GuestbookCategory;
  courseId: string;
  content: string;
  channel: GuestbookChannel;
  contact?: string;
  website?: string;
}): Promise<{ ok: true; entry: GuestbookEntry } | { ok: false; error: string }> {
  if (!BRAND.guestbookApiUrl) {
    return { ok: false, error: '当前未配置公开留言后端接口。' };
  }
  try {
    const res = await fetch(BRAND.guestbookApiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => null);
    if (!res.ok || !data?.ok || !data?.entry) {
      return { ok: false, error: data?.error || `提交失败（HTTP ${res.status}）` };
    }
    return { ok: true, entry: data.entry as GuestbookEntry };
  } catch {
    return { ok: false, error: '网络请求失败，请检查网络连接或使用「邮件助手」联系站长。' };
  }
}

export async function togglePublicGuestbookLike(
  id: string,
  clientId: string
): Promise<{ ok: true; liked: boolean; likes: number } | { ok: false; error: string }> {
  if (!BRAND.guestbookApiUrl) {
    return { ok: false, error: '当前处于离线模式' };
  }
  try {
    const res = await fetch(`${BRAND.guestbookApiUrl}/${encodeURIComponent(id)}/like`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clientId }),
    });
    const data = await res.json().catch(() => null);
    if (!res.ok || !data?.ok) {
      return { ok: false, error: data?.error || '点赞失败' };
    }
    return {
      ok: true,
      liked: Boolean(data.liked),
      likes: Number(data.likes ?? 0),
    };
  } catch {
    return { ok: false, error: '网络请求失败' };
  }
}

function getAdminApiBase(): string {
  return BRAND.guestbookApiUrl.replace(/\/guestbook\/?$/, '/admin/guestbook');
}

async function adminRequest<T>(
  path: string,
  token: string,
  init: RequestInit = {}
): Promise<({ ok: true } & T) | { ok: false; status: number; error: string }> {
  try {
    const headers = new Headers(init.headers);
    headers.set('Authorization', `Bearer ${token}`);
    if (init.body && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }
    const res = await fetch(path, {
      ...init,
      headers,
      cache: 'no-store',
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      return {
        ok: false,
        status: res.status,
        error: data?.error || `请求失败（HTTP ${res.status}）`,
      };
    }
    return { ok: true, ...(data as T) };
  } catch {
    return { ok: false, status: 0, error: '无法连接审核后台接口，请检查网络或确认 Worker 已启动。' };
  }
}

export async function fetchAdminGuestbook(
  token: string,
  tab: AdminGuestbookTab
): Promise<
  | { ok: true; entries: AdminGuestbookEntry[]; counts: AdminGuestbookCounts }
  | { ok: false; status: number; error: string }
> {
  const base = getAdminApiBase();
  return adminRequest<{ entries: AdminGuestbookEntry[]; counts: AdminGuestbookCounts }>(
    `${base}?tab=${encodeURIComponent(tab)}`,
    token,
    { method: 'GET' }
  );
}

export async function publishAdminGuestbook(
  token: string,
  payload: {
    author?: string;
    role?: 'admin' | 'assistant';
    category: GuestbookCategory;
    courseId: string;
    content: string;
    pinned?: boolean;
  }
): Promise<{ ok: true; entry: AdminGuestbookEntry } | { ok: false; status: number; error: string }> {
  return adminRequest<{ entry: AdminGuestbookEntry }>(getAdminApiBase(), token, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateAdminGuestbook(
  token: string,
  id: string,
  patch: {
    status?: GuestbookStatus;
    channel?: GuestbookChannel;
    pinned?: boolean;
    adminReply?: string;
  }
): Promise<{ ok: true; entry: AdminGuestbookEntry } | { ok: false; status: number; error: string }> {
  return adminRequest<{ entry: AdminGuestbookEntry }>(
    `${getAdminApiBase()}/${encodeURIComponent(id)}`,
    token,
    {
      method: 'PATCH',
      body: JSON.stringify(patch),
    }
  );
}

export async function deleteAdminGuestbook(
  token: string,
  id: string
): Promise<{ ok: true; deletedId: string } | { ok: false; status: number; error: string }> {
  return adminRequest<{ deletedId: string }>(
    `${getAdminApiBase()}/${encodeURIComponent(id)}`,
    token,
    { method: 'DELETE' }
  );
}

export interface GuestbookMailDraft {
  to: string;
  subject: string;
  body: string;
  fullText: string;
  mailtoHref: string;
  gmailHref: string;
  outlookHref: string;
}

export function buildGuestbookMailDraft(entry: {
  author: string;
  category: GuestbookCategory;
  courseLabel: string;
  content: string;
}): GuestbookMailDraft {
  const catLabel = GUESTBOOK_CATEGORY_LABELS[entry.category] || entry.category;
  const author = entry.author.trim() || '考研人';
  const contentText = entry.content.trim() || '（请在此补充具体题号或留言内容）';
  const to = BRAND.contact;
  const subject = `[${BRAND.name}留言板·${catLabel}] 来自「${author}」（${entry.courseLabel}）`;
  const body = [
    `昵称：${author}`,
    `分类：${catLabel}`,
    `关联板块：${entry.courseLabel}`,
    '',
    '留言内容：',
    contentText,
    '',
    '---',
    `（由「${BRAND.fullName}」留言板一键生成，QQ 交流群：${BRAND.qqGroup}）`,
  ].join('\n');
  const fullText = `收件人：${to}\n主题：${subject}\n\n${body}`;
  const mailtoHref = `mailto:${to}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  const gmailHref = `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(to)}&su=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  const outlookHref = `https://outlook.live.com/mail/0/deeplink/compose?to=${encodeURIComponent(to)}&subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  return {
    to,
    subject,
    body,
    fullText,
    mailtoHref,
    gmailHref,
    outlookHref,
  };
}

export function buildGuestbookMailto(entry: {
  author: string;
  category: GuestbookCategory;
  courseLabel: string;
  content: string;
}): string {
  return buildGuestbookMailDraft(entry).mailtoHref;
}
