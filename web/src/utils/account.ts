import { BRAND } from '../brand';
import type {
  AccountInboxEntry,
  AuthUser,
  CloudSyncMeta,
  CompanionState,
  CourseStudySlice,
  DailyCompanionProgress,
  MultiCourseStudyState,
  PrivateInboxEntry,
  QuestionRecord,
  StageFrameId,
  WeeklyCompanionProgress,
} from '../types';

export interface StudyStateSummary {
  courseCount: number;
  attemptedCount: number;
  wrongCount: number;
  noteCount: number;
  mockCount: number;
  fish: number;
  ownedCardCount: number;
}

const EMPTY_COURSE_SLICE: CourseStudySlice = {
  records: {},
  favoriteFormulas: [],
  practiceLogs: [],
  mockHistory: [],
  activeMock: null,
};

function mergeStringArray(a: string[] | undefined, b: string[] | undefined): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const item of [...(a ?? []), ...(b ?? [])]) {
    if (typeof item === 'string' && !seen.has(item)) {
      seen.add(item);
      out.push(item);
    }
  }
  return out;
}

export function hasMeaningfulStudyData(state: MultiCourseStudyState | null | undefined): boolean {
  if (!state) return false;
  for (const slice of Object.values(state.courses ?? {})) {
    if (!slice) continue;
    if (Object.keys(slice.records ?? {}).length > 0) return true;
    if ((slice.favoriteFormulas ?? []).length > 0) return true;
    if ((slice.practiceLogs ?? []).length > 0) return true;
    if ((slice.mockHistory ?? []).length > 0) return true;
    if (slice.activeMock) return true;
  }
  const c = state.companion;
  if (!c) return false;
  if (Number(c.totalPacksOpened ?? 0) > 0) return true;
  if (Number(c.checkInStreak ?? 0) > 0 || Boolean(c.lastCheckInDate)) return true;
  if (Number(c.vouchers ?? 0) > 0) return true;
  if (Number(c.fish ?? 80) !== 80) return true;
  if (
    Object.entries(c.ownedCards ?? {}).some(
      ([k, count]) => k !== 'sp:dafeyu' && k !== 'sp:gemini' && Number(count ?? 0) > 0
    )
  ) {
    return true;
  }
  if (Object.values(c.bonds ?? {}).some((v) => Number(v ?? 0) > 0)) return true;
  if ((c.ownedFrames ?? []).some((f) => f !== 'default')) return true;
  if ((c.claimedAchievements ?? []).length > 0) return true;
  if (c.equippedCardId && c.equippedCardId !== 'sp:dafeyu') return true;
  if (c.equippedFrame && c.equippedFrame !== 'default') return true;
  if (c.daily) {
    if (
      c.daily.checkedIn ||
      c.daily.mascotInteracted ||
      (c.daily.practicedQids ?? []).length > 0 ||
      (c.daily.formulaFlippedIds ?? []).length > 0 ||
      (c.daily.claimedMissions ?? []).length > 0
    ) {
      return true;
    }
  }
  if (c.weekly) {
    if (
      (c.weekly.practicedQids ?? []).length > 0 ||
      Number(c.weekly.mockCount ?? 0) > 0 ||
      (c.weekly.claimedMissions ?? []).length > 0
    ) {
      return true;
    }
  }
  return false;
}

export function summarizeStudyState(state: MultiCourseStudyState | null | undefined): StudyStateSummary {
  if (!state) {
    return {
      courseCount: 0,
      attemptedCount: 0,
      wrongCount: 0,
      noteCount: 0,
      mockCount: 0,
      fish: 0,
      ownedCardCount: 0,
    };
  }
  let courseCount = 0;
  let attemptedCount = 0;
  let wrongCount = 0;
  let noteCount = 0;
  let mockCount = 0;

  for (const slice of Object.values(state.courses ?? {})) {
    if (!slice) continue;
    const records = Object.values(slice.records ?? {});
    const hasActivity =
      records.length > 0 ||
      (slice.mockHistory ?? []).length > 0 ||
      (slice.favoriteFormulas ?? []).length > 0;
    if (hasActivity) courseCount++;
    for (const r of records) {
      if (r.attempts > 0 || r.status !== 'unseen') attemptedCount++;
      if (r.inWrongBook) wrongCount++;
      if (r.note && r.note.trim()) noteCount++;
    }
    mockCount += (slice.mockHistory ?? []).length;
  }

  const ownedCardCount = Object.values(state.companion?.ownedCards ?? {}).filter(
    (cnt) => Number(cnt ?? 0) > 0
  ).length;

  return {
    courseCount,
    attemptedCount,
    wrongCount,
    noteCount,
    mockCount,
    fish: Number(state.companion?.fish ?? 80),
    ownedCardCount,
  };
}

function mergeRecord(a: QuestionRecord, b: QuestionRecord): QuestionRecord {
  const aUpdated = Number(a.updatedAt ?? 0);
  const bUpdated = Number(b.updatedAt ?? 0);
  const primary = aUpdated >= bUpdated ? a : b;
  const secondary = primary === a ? b : a;
  return {
    ...secondary,
    ...primary,
    attempts: Math.max(Number(a.attempts ?? 0), Number(b.attempts ?? 0)),
    wrongCount: Math.max(Number(a.wrongCount ?? 0), Number(b.wrongCount ?? 0)),
    favorite: Boolean(a.favorite || b.favorite),
    inWrongBook:
      aUpdated === bUpdated
        ? Boolean(a.inWrongBook || b.inWrongBook)
        : Boolean(primary.inWrongBook),
    note: primary.note && primary.note.trim() ? primary.note : secondary.note,
    userDraft: primary.userDraft && primary.userDraft.trim() ? primary.userDraft : secondary.userDraft,
    updatedAt: Math.max(aUpdated, bUpdated),
  };
}

function mergeCourseSlice(a: CourseStudySlice, b: CourseStudySlice): CourseStudySlice {
  const qids = mergeStringArray(Object.keys(a.records ?? {}), Object.keys(b.records ?? {}));
  const records: Record<string, QuestionRecord> = {};
  for (const qid of qids) {
    const recA = a.records?.[qid];
    const recB = b.records?.[qid];
    if (recA && recB) {
      records[qid] = mergeRecord(recA, recB);
    } else if (recA) {
      records[qid] = recA;
    } else if (recB) {
      records[qid] = recB;
    }
  }

  const logSeen = new Set<string>();
  const practiceLogs = [...(a.practiceLogs ?? []), ...(b.practiceLogs ?? [])]
    .filter((item) => {
      if (!item?.id || logSeen.has(item.id)) return false;
      logSeen.add(item.id);
      return true;
    })
    .sort((x, y) => Number(y.timestamp ?? 0) - Number(x.timestamp ?? 0))
    .slice(0, 300);

  const mockSeen = new Set<string>();
  const mockHistory = [...(a.mockHistory ?? []), ...(b.mockHistory ?? [])]
    .filter((item) => {
      if (!item?.id || mockSeen.has(item.id)) return false;
      mockSeen.add(item.id);
      return true;
    })
    .sort((x, y) => Number(y.submittedAt ?? 0) - Number(x.submittedAt ?? 0))
    .slice(0, 50);

  let activeMock = a.activeMock ?? b.activeMock ?? null;
  if (a.activeMock && b.activeMock) {
    const scoreA = Number(a.activeMock.startedAt ?? 0) + Number(a.activeMock.elapsedSeconds ?? 0) * 1000;
    const scoreB = Number(b.activeMock.startedAt ?? 0) + Number(b.activeMock.elapsedSeconds ?? 0) * 1000;
    activeMock = scoreA >= scoreB ? a.activeMock : b.activeMock;
  }

  return {
    records,
    favoriteFormulas: mergeStringArray(a.favoriteFormulas, b.favoriteFormulas),
    practiceLogs,
    mockHistory,
    activeMock,
  };
}

function mergeDaily(a: DailyCompanionProgress, b: DailyCompanionProgress): DailyCompanionProgress {
  if ((a.date || '') !== (b.date || '')) {
    return (a.date || '') >= (b.date || '') ? a : b;
  }
  return {
    date: a.date,
    checkedIn: Boolean(a.checkedIn || b.checkedIn),
    practicedQids: mergeStringArray(a.practicedQids, b.practicedQids),
    masteredQids: mergeStringArray(a.masteredQids, b.masteredQids),
    bigQuestionQids: mergeStringArray(a.bigQuestionQids, b.bigQuestionQids),
    wrongClearedQids: mergeStringArray(a.wrongClearedQids, b.wrongClearedQids),
    noteQids: mergeStringArray(a.noteQids, b.noteQids),
    formulaFlippedIds: mergeStringArray(a.formulaFlippedIds, b.formulaFlippedIds),
    microDropQids: mergeStringArray(a.microDropQids, b.microDropQids),
    microDropEarned: Math.max(Number(a.microDropEarned ?? 0), Number(b.microDropEarned ?? 0)),
    bondDropQids: mergeStringArray(a.bondDropQids, b.bondDropQids),
    bondDropEarned: Math.max(Number(a.bondDropEarned ?? 0), Number(b.bondDropEarned ?? 0)),
    mascotInteracted: Boolean(a.mascotInteracted || b.mascotInteracted),
    claimedMissions: mergeStringArray(a.claimedMissions, b.claimedMissions),
  };
}

function mergeWeekly(a: WeeklyCompanionProgress, b: WeeklyCompanionProgress): WeeklyCompanionProgress {
  if ((a.weekKey || '') !== (b.weekKey || '')) {
    return (a.weekKey || '') >= (b.weekKey || '') ? a : b;
  }
  return {
    weekKey: a.weekKey,
    practicedQids: mergeStringArray(a.practicedQids, b.practicedQids),
    mockCount: Math.max(Number(a.mockCount ?? 0), Number(b.mockCount ?? 0)),
    activeDays: mergeStringArray(a.activeDays, b.activeDays),
    claimedMissions: mergeStringArray(a.claimedMissions, b.claimedMissions),
  };
}

function mergeCompanion(
  local?: CompanionState,
  cloud?: CompanionState
): CompanionState | undefined {
  if (!local) return cloud;
  if (!cloud) return local;

  const ownedCards: Record<string, number> = {};
  for (const k of mergeStringArray(Object.keys(local.ownedCards ?? {}), Object.keys(cloud.ownedCards ?? {}))) {
    ownedCards[k] = Math.max(Number(local.ownedCards?.[k] ?? 0), Number(cloud.ownedCards?.[k] ?? 0));
  }

  const bonds: Record<string, number> = {};
  for (const k of mergeStringArray(Object.keys(local.bonds ?? {}), Object.keys(cloud.bonds ?? {}))) {
    bonds[k] = Math.max(Number(local.bonds?.[k] ?? 0), Number(cloud.bonds?.[k] ?? 0));
  }

  const ownedFrames = mergeStringArray(
    local.ownedFrames,
    cloud.ownedFrames
  ) as StageFrameId[];

  const localPacks = Number(local.totalPacksOpened ?? 0);
  const cloudPacks = Number(cloud.totalPacksOpened ?? 0);
  const lastCheckInDate =
    (local.lastCheckInDate || '') >= (cloud.lastCheckInDate || '')
      ? local.lastCheckInDate
      : cloud.lastCheckInDate;

  return {
    ...cloud,
    ...local,
    version: Math.max(Number(local.version ?? 1), Number(cloud.version ?? 1)),
    fish: Math.max(Number(local.fish ?? 0), Number(cloud.fish ?? 0)),
    vouchers: Math.max(Number(local.vouchers ?? 0), Number(cloud.vouchers ?? 0)),
    totalPacksOpened: Math.max(localPacks, cloudPacks),
    pityCounter: localPacks >= cloudPacks ? local.pityCounter : cloud.pityCounter,
    checkInStreak:
      (local.lastCheckInDate || '') === (cloud.lastCheckInDate || '')
        ? Math.max(Number(local.checkInStreak ?? 0), Number(cloud.checkInStreak ?? 0))
        : (local.lastCheckInDate || '') > (cloud.lastCheckInDate || '')
          ? local.checkInStreak
          : cloud.checkInStreak,
    lastCheckInDate,
    ownedCards,
    bonds,
    ownedFrames: ownedFrames.length > 0 ? ownedFrames : ['default'],
    equippedCardId:
      local.equippedCardId && local.equippedCardId !== 'sp:dafeyu'
        ? local.equippedCardId
        : cloud.equippedCardId || 'sp:dafeyu',
    equippedFrame:
      local.equippedFrame && local.equippedFrame !== 'default'
        ? local.equippedFrame
        : cloud.equippedFrame || 'default',
    daily: mergeDaily(local.daily, cloud.daily),
    weekly: mergeWeekly(local.weekly, cloud.weekly),
    claimedAchievements: mergeStringArray(local.claimedAchievements, cloud.claimedAchievements),
  };
}

export function mergeMultiCourseState(
  local: MultiCourseStudyState,
  cloud: MultiCourseStudyState
): MultiCourseStudyState {
  const courseIds = mergeStringArray(
    Object.keys(local.courses ?? {}),
    Object.keys(cloud.courses ?? {})
  );
  const courses: Record<string, CourseStudySlice> = {};
  for (const cid of courseIds) {
    const l = local.courses?.[cid] ?? EMPTY_COURSE_SLICE;
    const c = cloud.courses?.[cid] ?? EMPTY_COURSE_SLICE;
    courses[cid] = mergeCourseSlice(l, c);
  }
  const companion = mergeCompanion(local.companion, cloud.companion);
  return {
    courses,
    settings: { ...(cloud.settings ?? {}), ...(local.settings ?? {}) },
    ...(companion ? { companion } : {}),
  };
}

type ApiResult<T> = ({ ok: true } & T) | { ok: false; error: string; status?: number; offline?: boolean };

async function apiJson<T>(url: string, init: RequestInit = {}): Promise<ApiResult<T>> {
  try {
    const headers = new Headers(init.headers);
    if (init.body && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }
    const res = await fetch(url, {
      ...init,
      headers,
      credentials: 'same-origin',
      cache: 'no-store',
    });
    const contentType = res.headers.get('content-type') ?? '';
    if (!contentType.includes('application/json')) {
      return { ok: false, error: '当前处于纯静态离线环境', status: res.status, offline: true };
    }
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      return {
        ok: false,
        error: data?.error || `请求失败（HTTP ${res.status}）`,
        status: res.status,
      };
    }
    return { ok: true, ...(data as T) };
  } catch {
    return { ok: false, error: '无法连接服务器，请检查网络连接', offline: true };
  }
}

export async function fetchAuthMe(): Promise<
  ApiResult<{
    user: AuthUser | null;
    cloudMeta: CloudSyncMeta | null;
    inboxReplyCount: number;
  }>
> {
  if (!BRAND.authApiUrl) {
    return { ok: false, error: '未配置账号接口', offline: true };
  }
  return apiJson(`${BRAND.authApiUrl}/me`, { method: 'GET' });
}

export async function registerAccount(payload: {
  username: string;
  password: string;
  displayName?: string;
}): Promise<ApiResult<{ user: AuthUser }>> {
  return apiJson(`${BRAND.authApiUrl}/register`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function loginAccount(payload: {
  username: string;
  password: string;
}): Promise<ApiResult<{ user: AuthUser; cloudMeta: CloudSyncMeta | null }>> {
  return apiJson(`${BRAND.authApiUrl}/login`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function logoutAccount(): Promise<ApiResult<Record<string, never>>> {
  return apiJson(`${BRAND.authApiUrl}/logout`, { method: 'POST' });
}

export async function logoutOtherSessions(): Promise<ApiResult<{ revokedCount: number }>> {
  return apiJson(`${BRAND.authApiUrl}/logout-all`, { method: 'POST' });
}

export async function updateAccountProfile(displayName: string): Promise<ApiResult<{ user: AuthUser }>> {
  return apiJson(`${BRAND.authApiUrl}/profile`, {
    method: 'PATCH',
    body: JSON.stringify({ displayName }),
  });
}

export async function changeAccountPassword(payload: {
  currentPassword: string;
  newPassword: string;
}): Promise<ApiResult<Record<string, never>>> {
  return apiJson(`${BRAND.authApiUrl}/password`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function fetchCloudStudyData(): Promise<
  ApiResult<{
    hasData: boolean;
    version: number;
    updatedAt: string;
    dataSize: number;
    data: MultiCourseStudyState | null;
  }>
> {
  return apiJson(`${BRAND.accountApiUrl}/sync`, { method: 'GET' });
}

export async function pushCloudStudyData(
  data: MultiCourseStudyState,
  baseVersion: number,
  force = false
): Promise<
  | { ok: true; version: number; updatedAt: string; dataSize: number }
  | {
      ok: false;
      conflict: true;
      error: string;
      version: number;
      updatedAt: string;
      data: MultiCourseStudyState;
    }
  | { ok: false; conflict?: false; error: string; status?: number; offline?: boolean }
> {
  try {
    const res = await fetch(`${BRAND.accountApiUrl}/sync`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data, baseVersion, force }),
      credentials: 'same-origin',
      cache: 'no-store',
    });
    const contentType = res.headers.get('content-type') ?? '';
    if (!contentType.includes('application/json')) {
      return { ok: false, error: '当前处于纯静态离线环境', status: res.status, offline: true };
    }
    const payload = await res.json().catch(() => null);
    if (res.status === 409 && payload?.conflict && payload?.data) {
      return {
        ok: false,
        conflict: true,
        error: payload.error || '云端存在其他设备的更新版本',
        version: Number(payload.version ?? 0),
        updatedAt: String(payload.updatedAt ?? ''),
        data: payload.data as MultiCourseStudyState,
      };
    }
    if (!res.ok || !payload?.ok) {
      return {
        ok: false,
        error: payload?.error || `同步失败（HTTP ${res.status}）`,
        status: res.status,
      };
    }
    return {
      ok: true,
      version: Number(payload.version ?? 1),
      updatedAt: String(payload.updatedAt ?? ''),
      dataSize: Number(payload.dataSize ?? 0),
    };
  } catch {
    return { ok: false, error: '网络请求失败，暂未同步到云端', offline: true };
  }
}

export async function fetchAccountInbox(): Promise<ApiResult<{ items: AccountInboxEntry[] }>> {
  return apiJson(`${BRAND.accountApiUrl}/inbox`, { method: 'GET' });
}

export async function claimAccountInboxReceipts(
  entries: PrivateInboxEntry[]
): Promise<ApiResult<{ claimedCount: number }>> {
  const receipts = entries
    .filter((e) => e.id.trim() && e.receiptToken.trim())
    .slice(0, 20)
    .map((e) => ({ id: e.id, token: e.receiptToken }));
  if (receipts.length === 0) {
    return { ok: true, claimedCount: 0 };
  }
  return apiJson(`${BRAND.accountApiUrl}/inbox/claim`, {
    method: 'POST',
    body: JSON.stringify({ receipts }),
  });
}
