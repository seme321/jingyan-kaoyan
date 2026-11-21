CREATE TABLE IF NOT EXISTS guestbook_entries (
  id TEXT PRIMARY KEY,
  author TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user',
  category TEXT NOT NULL,
  course_id TEXT NOT NULL DEFAULT 'all',
  content TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  channel TEXT NOT NULL DEFAULT 'public',
  contact TEXT NOT NULL DEFAULT '',
  admin_reply TEXT NOT NULL DEFAULT '',
  admin_replied_at TEXT NOT NULL DEFAULT '',
  likes INTEGER NOT NULL DEFAULT 0,
  pinned INTEGER NOT NULL DEFAULT 0,
  ip_hash TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  reviewed_at TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_gb_status_channel_pinned_created
  ON guestbook_entries (status, channel, pinned DESC, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_gb_ip_created
  ON guestbook_entries (ip_hash, created_at DESC);

CREATE TABLE IF NOT EXISTS guestbook_likes (
  entry_id TEXT NOT NULL,
  voter_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY (entry_id, voter_hash)
);

INSERT OR IGNORE INTO guestbook_entries (
  id, author, role, category, course_id, content,
  status, channel, contact, admin_reply, admin_replied_at,
  likes, pinned, ip_hash, created_at, reviewed_at
) VALUES
(
  'seed-admin-welcome',
  '站长 · 大肥鱼',
  'admin',
  'checkin',
  'all',
  '欢迎来到「鲸研专业课」！目前扬州大学 849 水力学（17 套）与河海大学 814 水力学（14 套）历年真题精解已全部上线。' || char(10) || '遇到答案勘误、公式显示异常或想许愿其他院校专业课，欢迎在本页留言、发邮件至 amassss321@gmail.com，或加入考研交流 QQ 群 1058675261 一起上岸！',
  'approved',
  'public',
  '',
  '',
  '',
  24,
  1,
  '',
  '2026-11-21T09:00:00+08:00',
  '2026-11-21T09:00:00+08:00'
),
(
  'seed-gemini-assistant',
  'Gemini · AI 助教',
  'assistant',
  'chat',
  'all',
  '大家好，我是协助整理真题精解、步骤采分点与水力学示意图重置的 Gemini！记得先看静水力学和能量方程大题，刷错的题要回错题本二刷哦～大家也可以在「关于本站 → 角色图鉴」里看到我的形象立绘 ✨',
  'approved',
  'public',
  '',
  '',
  '',
  18,
  1,
  '',
  '2026-11-21T09:30:00+08:00',
  '2026-11-21T09:30:00+08:00'
);
