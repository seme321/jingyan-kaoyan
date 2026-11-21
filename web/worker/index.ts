import type {
  AdminGuestbookCounts,
  AdminGuestbookEntry,
  GuestbookCategory,
  GuestbookChannel,
  GuestbookEntry,
  GuestbookStatus,
} from '../src/types';

interface GuestbookRow {
  id: string;
  author: string;
  role: 'admin' | 'assistant' | 'user';
  category: GuestbookCategory;
  course_id: string;
  content: string;
  status: GuestbookStatus;
  channel: GuestbookChannel;
  contact?: string;
  admin_reply: string;
  admin_replied_at: string;
  likes: number;
  pinned: number;
  created_at: string;
  reviewed_at?: string;
}

const VALID_CATEGORIES = new Set<GuestbookCategory>(['checkin', 'errata', 'wish', 'chat']);
const VALID_STATUSES = new Set<GuestbookStatus>(['pending', 'approved', 'rejected']);
const VALID_CHANNELS = new Set<GuestbookChannel>(['public', 'inbox']);
const VALID_ADMIN_TABS = new Set(['pending', 'inbox', 'approved', 'rejected', 'all']);
const SAFE_ID_RE = /^[a-zA-Z0-9_-]{4,64}$/;
const SAFE_COURSE_RE = /^[a-z0-9_-]{1,32}$/;
const MAX_BODY_BYTES = 8192;

function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store',
    },
  });
}

function normalizeText(value: unknown): string {
  if (typeof value !== 'string') return '';
  return value
    .replace(/\r\n?/g, '\n')
    .replace(/[\x00-\x09\x0B-\x1F\x7F]/g, '')
    .trim();
}

async function sha256Bytes(text: string): Promise<Uint8Array> {
  const encoded = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest('SHA-256', encoded);
  return new Uint8Array(digest);
}

async function sha256Hex(text: string): Promise<string> {
  const bytes = await sha256Bytes(text);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
}

async function verifyAdmin(request: Request, env: Env): Promise<boolean> {
  const expected = typeof env.ADMIN_TOKEN === 'string' ? env.ADMIN_TOKEN.trim() : '';
  if (!expected) return false;

  const authHeader = request.headers.get('Authorization') ?? '';
  if (!authHeader.startsWith('Bearer ')) return false;
  const provided = authHeader.slice(7).trim();
  if (!provided) return false;

  const [providedHash, expectedHash] = await Promise.all([
    sha256Bytes(provided),
    sha256Bytes(expected),
  ]);
  return crypto.subtle.timingSafeEqual(providedHash, expectedHash);
}

async function readBoundedJson(
  request: Request,
  maxBytes = MAX_BODY_BYTES
): Promise<{ ok: true; data: Record<string, unknown> } | { ok: false; status: number; error: string }> {
  const contentLength = request.headers.get('Content-Length');
  if (contentLength !== null) {
    const len = Number(contentLength);
    if (Number.isFinite(len) && len > maxBytes) {
      return { ok: false, status: 413, error: '请求内容过大，请精简后再试' };
    }
  }

  if (!request.body) {
    return { ok: true, data: {} };
  }

  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    if (!value) continue;
    total += value.byteLength;
    if (total > maxBytes) {
      try {
        await reader.cancel();
      } catch {
        // ignore cancel error
      }
      return { ok: false, status: 413, error: '请求内容过大，请精简后再试' };
    }
    chunks.push(value);
  }

  if (total === 0) {
    return { ok: true, data: {} };
  }

  const merged = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    merged.set(chunk, offset);
    offset += chunk.byteLength;
  }

  const text = new TextDecoder().decode(merged).trim();
  if (!text) {
    return { ok: true, data: {} };
  }

  try {
    const parsed: unknown = JSON.parse(text);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      return { ok: false, status: 400, error: '请求体必须为 JSON 对象' };
    }
    return { ok: true, data: parsed as Record<string, unknown> };
  } catch {
    return { ok: false, status: 400, error: 'JSON 格式错误' };
  }
}

async function computeIpHash(request: Request, env: Env): Promise<string> {
  const ip =
    request.headers.get('CF-Connecting-IP') ||
    request.headers.get('X-Forwarded-For')?.split(',')[0]?.trim() ||
    'unknown';
  const salt = env.ADMIN_TOKEN ? env.ADMIN_TOKEN.slice(0, 12) : 'jingyan-guestbook-salt';
  return sha256Hex(`${ip}::${salt}`);
}

function mapPublicEntry(row: GuestbookRow): GuestbookEntry {
  const entry: GuestbookEntry = {
    id: row.id,
    author: row.author,
    role: row.role,
    category: row.category,
    courseId: row.course_id,
    content: row.content,
    createdAt: row.created_at,
    likes: Number(row.likes ?? 0),
    pinned: Boolean(row.pinned),
  };
  if (row.admin_reply) {
    entry.adminReply = row.admin_reply;
    if (row.admin_replied_at) {
      entry.adminRepliedAt = row.admin_replied_at;
    }
  }
  return entry;
}

function mapAdminEntry(row: GuestbookRow): AdminGuestbookEntry {
  return {
    ...mapPublicEntry(row),
    status: row.status,
    channel: row.channel,
    contact: row.contact || undefined,
    reviewedAt: row.reviewed_at || undefined,
  };
}

async function handleGetGuestbook(url: URL, env: Env): Promise<Response> {
  const entriesRes = await env.DB.prepare(
    `SELECT id, author, role, category, course_id, content,
            admin_reply, admin_replied_at, likes, pinned, created_at
     FROM guestbook_entries
     WHERE status = 'approved' AND channel = 'public'
     ORDER BY pinned DESC, created_at DESC
     LIMIT 200`
  ).all<GuestbookRow>();

  const entries = (entriesRes.results ?? []).map(mapPublicEntry);

  const pendingParam = url.searchParams.get('pendingIds') ?? '';
  const pendingIds = pendingParam
    .split(',')
    .map((id) => id.trim())
    .filter((id) => SAFE_ID_RE.test(id))
    .slice(0, 20);

  const pendingStatuses: Record<string, { status: GuestbookStatus; channel: GuestbookChannel }> = {};
  if (pendingIds.length > 0) {
    const placeholders = pendingIds.map(() => '?').join(',');
    const statusRes = await env.DB.prepare(
      `SELECT id, status, channel FROM guestbook_entries WHERE id IN (${placeholders})`
    )
      .bind(...pendingIds)
      .all<{ id: string; status: GuestbookStatus; channel: GuestbookChannel }>();
    for (const row of statusRes.results ?? []) {
      pendingStatuses[row.id] = { status: row.status, channel: row.channel };
    }
  }

  const clientId = (url.searchParams.get('clientId') ?? '').trim();
  let likedIds: string[] = [];
  if (SAFE_ID_RE.test(clientId)) {
    const voterHash = await sha256Hex(`voter:${clientId}`);
    const likesRes = await env.DB.prepare(
      `SELECT entry_id FROM guestbook_likes WHERE voter_hash = ?`
    )
      .bind(voterHash)
      .all<{ entry_id: string }>();
    likedIds = (likesRes.results ?? []).map((row) => row.entry_id);
  }

  return jsonResponse({
    entries,
    pendingStatuses,
    likedIds,
    mode: 'moderated',
  });
}

async function handlePostGuestbook(request: Request, env: Env): Promise<Response> {
  const parsed = await readBoundedJson(request);
  if (!parsed.ok) {
    return jsonResponse({ error: parsed.error }, parsed.status);
  }
  const body = parsed.data;

  if (typeof body.website === 'string' && body.website.trim().length > 0) {
    return jsonResponse({ error: '表单校验未通过' }, 400);
  }

  const category = typeof body.category === 'string' ? (body.category as GuestbookCategory) : null;
  if (!category || !VALID_CATEGORIES.has(category)) {
    return jsonResponse({ error: '无效的留言分类' }, 400);
  }

  let channel: GuestbookChannel = 'public';
  if (body.channel !== undefined) {
    if (typeof body.channel !== 'string' || !VALID_CHANNELS.has(body.channel as GuestbookChannel)) {
      return jsonResponse({ error: '无效的提交通道' }, 400);
    }
    channel = body.channel as GuestbookChannel;
  }

  const rawCourseId = typeof body.courseId === 'string' ? body.courseId.trim() : 'all';
  const courseId = SAFE_COURSE_RE.test(rawCourseId) ? rawCourseId : 'all';

  const author = normalizeText(body.author).slice(0, 20) || '考研人';
  const content = normalizeText(body.content);
  if (content.length < 2) {
    return jsonResponse({ error: '留言内容至少需要 2 个字哦～' }, 400);
  }
  if (content.length > 500) {
    return jsonResponse({ error: '留言内容不能超过 500 字' }, 400);
  }

  const urlMatches = content.match(/https?:\/\/\S+/gi);
  if (urlMatches && urlMatches.length >= 2) {
    return jsonResponse({ error: '为防广告刷屏，单条留言最多包含 1 个链接' }, 400);
  }

  const contact = normalizeText(body.contact).slice(0, 60);
  const ipHash = await computeIpHash(request, env);

  const nowMs = Date.now();
  const oneMinuteAgo = new Date(nowMs - 60_000).toISOString();
  const oneHourAgo = new Date(nowMs - 3_600_000).toISOString();

  const rateRow = await env.DB.prepare(
    `SELECT
       COALESCE(SUM(CASE WHEN created_at >= ? THEN 1 ELSE 0 END), 0) AS recent_1m,
       COUNT(*) AS recent_1h
     FROM guestbook_entries
     WHERE ip_hash = ? AND created_at >= ?`
  )
    .bind(oneMinuteAgo, ipHash, oneHourAgo)
    .first<{ recent_1m: number; recent_1h: number }>();

  if ((rateRow?.recent_1m ?? 0) >= 2 || (rateRow?.recent_1h ?? 0) >= 10) {
    return jsonResponse({ error: '提交太频繁了，请稍等片刻再试～' }, 429);
  }

  const id = `gb-${crypto.randomUUID()}`;
  const createdAt = new Date(nowMs).toISOString();

  await env.DB.prepare(
    `INSERT INTO guestbook_entries (
       id, author, role, category, course_id, content,
       status, channel, contact, admin_reply, admin_replied_at,
       likes, pinned, ip_hash, created_at, reviewed_at
     ) VALUES (?, ?, 'user', ?, ?, ?, 'pending', ?, ?, '', '', 0, 0, ?, ?, '')`
  )
    .bind(id, author, category, courseId, content, channel, contact, ipHash, createdAt)
    .run();

  const entry: GuestbookEntry = {
    id,
    author,
    role: 'user',
    category,
    courseId,
    content,
    status: 'pending',
    channel,
    createdAt,
    likes: 0,
    pinned: false,
  };

  return jsonResponse({ ok: true, entry }, 201);
}

async function handleLikeGuestbook(id: string, request: Request, env: Env): Promise<Response> {
  if (!SAFE_ID_RE.test(id)) {
    return jsonResponse({ error: '无效的留言 ID' }, 400);
  }

  const target = await env.DB.prepare(
    `SELECT id, likes FROM guestbook_entries
     WHERE id = ? AND status = 'approved' AND channel = 'public'`
  )
    .bind(id)
    .first<{ id: string; likes: number }>();

  if (!target) {
    return jsonResponse({ error: '留言不存在或尚未公开' }, 404);
  }

  const parsed = await readBoundedJson(request);
  if (!parsed.ok) {
    return jsonResponse({ error: parsed.error }, parsed.status);
  }
  const clientId = typeof parsed.data.clientId === 'string' ? parsed.data.clientId.trim() : '';
  const voterHash = SAFE_ID_RE.test(clientId)
    ? await sha256Hex(`voter:${clientId}`)
    : await sha256Hex(`voter-ip:${await computeIpHash(request, env)}`);

  const existing = await env.DB.prepare(
    `SELECT 1 AS hit FROM guestbook_likes WHERE entry_id = ? AND voter_hash = ?`
  )
    .bind(id, voterHash)
    .first<{ hit: number }>();

  let liked = false;
  if (existing) {
    const del = await env.DB.prepare(
      `DELETE FROM guestbook_likes WHERE entry_id = ? AND voter_hash = ?`
    )
      .bind(id, voterHash)
      .run();
    if ((del.meta.changes ?? 0) > 0) {
      await env.DB.prepare(
        `UPDATE guestbook_entries SET likes = MAX(0, likes - 1) WHERE id = ?`
      )
        .bind(id)
        .run();
    }
    liked = false;
  } else {
    const nowIso = new Date().toISOString();
    const ins = await env.DB.prepare(
      `INSERT OR IGNORE INTO guestbook_likes (entry_id, voter_hash, created_at) VALUES (?, ?, ?)`
    )
      .bind(id, voterHash, nowIso)
      .run();
    if ((ins.meta.changes ?? 0) > 0) {
      await env.DB.prepare(
        `UPDATE guestbook_entries SET likes = likes + 1 WHERE id = ?`
      )
        .bind(id)
        .run();
    }
    liked = true;
  }

  const updated = await env.DB.prepare(
    `SELECT likes FROM guestbook_entries WHERE id = ?`
  )
    .bind(id)
    .first<{ likes: number }>();

  return jsonResponse({
    ok: true,
    liked,
    likes: Number(updated?.likes ?? target.likes ?? 0),
  });
}

async function handleAdminGet(url: URL, env: Env): Promise<Response> {
  const rawTab = url.searchParams.get('tab') ?? 'pending';
  const tab = VALID_ADMIN_TABS.has(rawTab) ? rawTab : 'pending';

  let whereClause = '';
  let orderClause = 'ORDER BY created_at DESC';
  if (tab === 'pending') {
    whereClause = `WHERE status = 'pending' AND channel = 'public'`;
    orderClause = 'ORDER BY created_at DESC';
  } else if (tab === 'inbox') {
    whereClause = `WHERE channel = 'inbox'`;
    orderClause = `ORDER BY CASE status WHEN 'pending' THEN 0 ELSE 1 END, created_at DESC`;
  } else if (tab === 'approved') {
    whereClause = `WHERE status = 'approved' AND channel = 'public'`;
    orderClause = 'ORDER BY pinned DESC, created_at DESC';
  } else if (tab === 'rejected') {
    whereClause = `WHERE status = 'rejected'`;
    orderClause = 'ORDER BY created_at DESC';
  } else {
    orderClause = 'ORDER BY pinned DESC, created_at DESC';
  }

  const [entriesRes, countsRow] = await Promise.all([
    env.DB.prepare(
      `SELECT id, author, role, category, course_id, content,
              status, channel, contact, admin_reply, admin_replied_at,
              likes, pinned, created_at, reviewed_at
       FROM guestbook_entries
       ${whereClause}
       ${orderClause}
       LIMIT 200`
    ).all<GuestbookRow>(),
    env.DB.prepare(
      `SELECT
         COALESCE(SUM(CASE WHEN status = 'pending' AND channel = 'public' THEN 1 ELSE 0 END), 0) AS pendingPublic,
         COALESCE(SUM(CASE WHEN status = 'pending' AND channel = 'inbox' THEN 1 ELSE 0 END), 0) AS pendingInbox,
         COALESCE(SUM(CASE WHEN status = 'approved' AND channel = 'public' THEN 1 ELSE 0 END), 0) AS approved,
         COALESCE(SUM(CASE WHEN channel = 'inbox' THEN 1 ELSE 0 END), 0) AS inboxAll,
         COALESCE(SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END), 0) AS rejected
       FROM guestbook_entries`
    ).first<AdminGuestbookCounts>(),
  ]);

  const counts: AdminGuestbookCounts = {
    pendingPublic: Number(countsRow?.pendingPublic ?? 0),
    pendingInbox: Number(countsRow?.pendingInbox ?? 0),
    approved: Number(countsRow?.approved ?? 0),
    inboxAll: Number(countsRow?.inboxAll ?? 0),
    rejected: Number(countsRow?.rejected ?? 0),
  };

  return jsonResponse({
    entries: (entriesRes.results ?? []).map(mapAdminEntry),
    counts,
  });
}

async function handleAdminPost(request: Request, env: Env): Promise<Response> {
  const parsed = await readBoundedJson(request);
  if (!parsed.ok) {
    return jsonResponse({ error: parsed.error }, parsed.status);
  }
  const body = parsed.data;

  const role: 'admin' | 'assistant' = body.role === 'assistant' ? 'assistant' : 'admin';
  const defaultAuthor = role === 'assistant' ? 'Gemini · AI 助教' : '站长 · 大肥鱼';
  const author = normalizeText(body.author).slice(0, 20) || defaultAuthor;

  const category = typeof body.category === 'string' ? (body.category as GuestbookCategory) : 'checkin';
  if (!VALID_CATEGORIES.has(category)) {
    return jsonResponse({ error: '无效的留言分类' }, 400);
  }

  const rawCourseId = typeof body.courseId === 'string' ? body.courseId.trim() : 'all';
  const courseId = SAFE_COURSE_RE.test(rawCourseId) ? rawCourseId : 'all';

  const content = normalizeText(body.content);
  if (content.length < 2 || content.length > 500) {
    return jsonResponse({ error: '留言内容需在 2 至 500 字之间' }, 400);
  }

  const pinned = Boolean(body.pinned);
  const id = `gb-${crypto.randomUUID()}`;
  const nowIso = new Date().toISOString();

  await env.DB.prepare(
    `INSERT INTO guestbook_entries (
       id, author, role, category, course_id, content,
       status, channel, contact, admin_reply, admin_replied_at,
       likes, pinned, ip_hash, created_at, reviewed_at
     ) VALUES (?, ?, ?, ?, ?, ?, 'approved', 'public', '', '', '', 0, ?, '', ?, ?)`
  )
    .bind(id, author, role, category, courseId, content, pinned ? 1 : 0, nowIso, nowIso)
    .run();

  const entry: AdminGuestbookEntry = {
    id,
    author,
    role,
    category,
    courseId,
    content,
    status: 'approved',
    channel: 'public',
    createdAt: nowIso,
    reviewedAt: nowIso,
    likes: 0,
    pinned,
  };

  return jsonResponse({ ok: true, entry }, 201);
}

async function handleAdminPatch(id: string, request: Request, env: Env): Promise<Response> {
  if (!SAFE_ID_RE.test(id)) {
    return jsonResponse({ error: '无效的留言 ID' }, 400);
  }

  const existing = await env.DB.prepare(
    `SELECT id FROM guestbook_entries WHERE id = ?`
  )
    .bind(id)
    .first<{ id: string }>();

  if (!existing) {
    return jsonResponse({ error: '留言不存在' }, 404);
  }

  const parsed = await readBoundedJson(request);
  if (!parsed.ok) {
    return jsonResponse({ error: parsed.error }, parsed.status);
  }
  const body = parsed.data;

  const sets: string[] = [];
  const params: unknown[] = [];
  const nowIso = new Date().toISOString();

  if (body.status !== undefined) {
    if (typeof body.status !== 'string' || !VALID_STATUSES.has(body.status as GuestbookStatus)) {
      return jsonResponse({ error: '无效的审核状态' }, 400);
    }
    sets.push('status = ?', 'reviewed_at = ?');
    params.push(body.status, nowIso);
  }

  if (body.channel !== undefined) {
    if (typeof body.channel !== 'string' || !VALID_CHANNELS.has(body.channel as GuestbookChannel)) {
      return jsonResponse({ error: '无效的投递通道' }, 400);
    }
    sets.push('channel = ?');
    params.push(body.channel);
  }

  if (body.pinned !== undefined) {
    sets.push('pinned = ?');
    params.push(body.pinned ? 1 : 0);
  }

  if (body.adminReply !== undefined) {
    if (typeof body.adminReply !== 'string') {
      return jsonResponse({ error: '回复内容格式错误' }, 400);
    }
    const replyText = normalizeText(body.adminReply).slice(0, 500);
    sets.push('admin_reply = ?', 'admin_replied_at = ?');
    params.push(replyText, replyText ? nowIso : '');
  }

  if (sets.length === 0) {
    return jsonResponse({ error: '未提供可更新字段' }, 400);
  }

  params.push(id);
  await env.DB.prepare(`UPDATE guestbook_entries SET ${sets.join(', ')} WHERE id = ?`)
    .bind(...params)
    .run();

  const updated = await env.DB.prepare(
    `SELECT id, author, role, category, course_id, content,
            status, channel, contact, admin_reply, admin_replied_at,
            likes, pinned, created_at, reviewed_at
     FROM guestbook_entries WHERE id = ?`
  )
    .bind(id)
    .first<GuestbookRow>();

  if (!updated) {
    return jsonResponse({ error: '留言不存在' }, 404);
  }

  return jsonResponse({ ok: true, entry: mapAdminEntry(updated) });
}

async function handleAdminDelete(id: string, env: Env): Promise<Response> {
  if (!SAFE_ID_RE.test(id)) {
    return jsonResponse({ error: '无效的留言 ID' }, 400);
  }

  const existing = await env.DB.prepare(
    `SELECT id FROM guestbook_entries WHERE id = ?`
  )
    .bind(id)
    .first<{ id: string }>();

  if (!existing) {
    return jsonResponse({ error: '留言不存在' }, 404);
  }

  await env.DB.batch([
    env.DB.prepare(`DELETE FROM guestbook_likes WHERE entry_id = ?`).bind(id),
    env.DB.prepare(`DELETE FROM guestbook_entries WHERE id = ?`).bind(id),
  ]);

  return jsonResponse({ ok: true, deletedId: id });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const { pathname } = url;

    if (!pathname.startsWith('/api/')) {
      return jsonResponse({ error: 'Not Found' }, 404);
    }

    try {
      if (pathname === '/api/guestbook') {
        if (request.method === 'GET') {
          return await handleGetGuestbook(url, env);
        }
        if (request.method === 'POST') {
          return await handlePostGuestbook(request, env);
        }
        return jsonResponse({ error: 'Method Not Allowed' }, 405);
      }

      const likeMatch = pathname.match(/^\/api\/guestbook\/([^/]+)\/like$/);
      if (likeMatch) {
        if (request.method === 'POST') {
          return await handleLikeGuestbook(decodeURIComponent(likeMatch[1]), request, env);
        }
        return jsonResponse({ error: 'Method Not Allowed' }, 405);
      }

      if (pathname === '/api/admin/guestbook') {
        if (!(await verifyAdmin(request, env))) {
          return jsonResponse({ error: '管理口令无效或未授权' }, 401);
        }
        if (request.method === 'GET') {
          return await handleAdminGet(url, env);
        }
        if (request.method === 'POST') {
          return await handleAdminPost(request, env);
        }
        return jsonResponse({ error: 'Method Not Allowed' }, 405);
      }

      const adminItemMatch = pathname.match(/^\/api\/admin\/guestbook\/([^/]+)$/);
      if (adminItemMatch) {
        if (!(await verifyAdmin(request, env))) {
          return jsonResponse({ error: '管理口令无效或未授权' }, 401);
        }
        const entryId = decodeURIComponent(adminItemMatch[1]);
        if (request.method === 'PATCH') {
          return await handleAdminPatch(entryId, request, env);
        }
        if (request.method === 'DELETE') {
          return await handleAdminDelete(entryId, env);
        }
        return jsonResponse({ error: 'Method Not Allowed' }, 405);
      }

      return jsonResponse({ error: 'Not Found' }, 404);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      console.error(
        JSON.stringify({
          message: 'guestbook api error',
          method: request.method,
          pathname,
          error: message,
        })
      );
      return jsonResponse({ error: '服务器内部错误，请稍后再试' }, 500);
    }
  },
} satisfies ExportedHandler<Env>;
