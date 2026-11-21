import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  Check,
  Copy,
  ExternalLink,
  Heart,
  Lock,
  Mail,
  Megaphone,
  MessageSquare,
  Pin,
  Send,
  ShieldCheck,
  Sparkles,
  Trash2,
  Users,
  X,
} from 'lucide-react';
import { BRAND } from '../brand';
import { GuestbookAdminModal } from '../components/GuestbookAdminModal';
import { Mascot } from '../components/Mascot';
import { useData } from '../context/DataContext';
import type { GuestbookCategory, GuestbookChannel, GuestbookEntry } from '../types';
import { copyText } from '../utils/clipboard';
import {
  GUESTBOOK_CATEGORIES,
  GUESTBOOK_CATEGORY_LABELS,
  buildGuestbookMailDraft,
  fetchPublicGuestbook,
  getOrCreateGuestbookClientId,
  loadLikedIds,
  loadLocalGuestbookEntries,
  loadPendingGuestbookEntries,
  saveLocalGuestbookEntries,
  savePendingGuestbookEntries,
  submitPublicGuestbook,
  toggleLikedId,
  togglePublicGuestbookLike,
  type GuestbookMailDraft,
} from '../utils/guestbook';

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso.slice(0, 16);
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  } catch {
    return iso.slice(0, 16);
  }
}

export const BoardPage: React.FC = () => {
  const { courses, currentCourse, setCourseId, announcements, markAnnouncementsRead } = useData();
  const navigate = useNavigate();

  const clientIdRef = useRef<string>(getOrCreateGuestbookClientId());
  const noticeTimerRef = useRef<number | null>(null);
  const mailCopyTimerRef = useRef<number | null>(null);

  const [copiedKey, setCopiedKey] = useState<'qq' | 'email' | null>(null);
  const [publicEntries, setPublicEntries] = useState<GuestbookEntry[]>([]);
  const [pendingEntries, setPendingEntries] = useState<GuestbookEntry[]>(loadPendingGuestbookEntries);
  const [localEntries, setLocalEntries] = useState<GuestbookEntry[]>(loadLocalGuestbookEntries);
  const [likedIds, setLikedIds] = useState<string[]>(loadLikedIds);
  const [isOnline, setIsOnline] = useState(true);
  const [boardLoading, setBoardLoading] = useState(true);
  const [likingId, setLikingId] = useState<string | null>(null);
  const [filterCat, setFilterCat] = useState<'all' | GuestbookCategory>('all');

  const [author, setAuthor] = useState('');
  const [category, setCategory] = useState<GuestbookCategory>('checkin');
  const [courseId, setEntryCourseId] = useState<string>('all');
  const [contact, setContact] = useState('');
  const [website, setWebsite] = useState('');
  const [content, setContent] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitNotice, setSubmitNotice] = useState<{ ok: boolean; text: string } | null>(null);

  const [adminOpen, setAdminOpen] = useState(false);
  const [mailModal, setMailModal] = useState<{
    draft: GuestbookMailDraft;
    isEmptyContent: boolean;
  } | null>(null);
  const [mailCopiedKey, setMailCopiedKey] = useState<'to' | 'subject' | 'body' | 'all' | null>(null);
  const [mailCopyFeedback, setMailCopyFeedback] = useState<{ ok: boolean; text: string } | null>(null);

  useEffect(() => {
    markAnnouncementsRead();
  }, [markAnnouncementsRead]);

  useEffect(() => {
    return () => {
      if (noticeTimerRef.current !== null) {
        window.clearTimeout(noticeTimerRef.current);
      }
      if (mailCopyTimerRef.current !== null) {
        window.clearTimeout(mailCopyTimerRef.current);
      }
    };
  }, []);

  const isMailModalOpen = mailModal !== null;
  useEffect(() => {
    if (!isMailModalOpen) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setMailModal(null);
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [isMailModalOpen]);

  const refreshGuestbook = useCallback(async () => {
    const currentPending = loadPendingGuestbookEntries();
    const pendingIds = currentPending.map((e) => e.id);
    const res = await fetchPublicGuestbook(pendingIds, clientIdRef.current);

    setPublicEntries(res.entries);
    setIsOnline(res.online);
    setLikedIds(res.likedIds);

    if (res.online) {
      const approvedIds = new Set(res.entries.map((e) => e.id));
      const reconciled = currentPending.filter((item) => {
        if (approvedIds.has(item.id)) return false;
        const statusInfo = res.pendingStatuses[item.id];
        if (!statusInfo) return false;
        return statusInfo.status === 'pending';
      });
      setPendingEntries(reconciled);
      savePendingGuestbookEntries(reconciled);
    } else {
      setPendingEntries(currentPending);
    }
    setBoardLoading(false);
  }, []);

  useEffect(() => {
    let active = true;
    const load = async () => {
      await refreshGuestbook();
    };
    if (active) {
      void load();
    }
    return () => {
      active = false;
    };
  }, [refreshGuestbook]);

  const handleCopy = async (key: 'qq' | 'email', value: string) => {
    const ok = await copyText(value);
    if (ok) {
      setCopiedKey(key);
      window.setTimeout(() => setCopiedKey((prev) => (prev === key ? null : prev)), 2200);
    }
  };

  const courseLabelMap = useMemo(() => {
    const map: Record<string, string> = { all: '全站通用' };
    for (const c of courses) {
      map[c.id] = c.shortLabel;
    }
    return map;
  }, [courses]);

  const allEntries = useMemo(() => {
    const seen = new Set<string>();
    const merged: GuestbookEntry[] = [];
    for (const item of [...pendingEntries, ...localEntries, ...publicEntries]) {
      if (seen.has(item.id)) continue;
      seen.add(item.id);
      merged.push(item);
    }
    return merged.sort((a, b) => {
      if (Boolean(a.pinned) !== Boolean(b.pinned)) return a.pinned ? -1 : 1;
      if (Boolean(a.isPendingLocal) !== Boolean(b.isPendingLocal)) {
        return a.isPendingLocal ? -1 : 1;
      }
      return b.createdAt.localeCompare(a.createdAt);
    });
  }, [pendingEntries, localEntries, publicEntries]);

  const categoryCounts = useMemo(() => {
    const counts: Record<'all' | GuestbookCategory, number> = {
      all: allEntries.length,
      checkin: 0,
      errata: 0,
      wish: 0,
      chat: 0,
    };
    for (const e of allEntries) {
      counts[e.category] = (counts[e.category] ?? 0) + 1;
    }
    return counts;
  }, [allEntries]);

  const visibleEntries = useMemo(
    () => (filterCat === 'all' ? allEntries : allEntries.filter((e) => e.category === filterCat)),
    [allEntries, filterCat]
  );

  const activeCategoryMeta =
    GUESTBOOK_CATEGORIES.find((c) => c.id === category) ?? GUESTBOOK_CATEGORIES[0];

  const showSubmitNotice = (ok: boolean, text: string) => {
    setSubmitNotice({ ok, text });
    if (noticeTimerRef.current !== null) {
      window.clearTimeout(noticeTimerRef.current);
    }
    noticeTimerRef.current = window.setTimeout(() => {
      setSubmitNotice(null);
      noticeTimerRef.current = null;
    }, 5200);
  };

  const handleSubmitEntry = async (targetChannel: GuestbookChannel) => {
    const trimmed = content.trim();
    if (trimmed.length < 2) {
      showSubmitNotice(false, '请至少输入 2 个字的留言内容再提交哦～');
      return;
    }
    if (submitting) return;

    setSubmitting(true);
    const res = await submitPublicGuestbook({
      author: author.trim(),
      category,
      courseId,
      content: trimmed,
      channel: targetChannel,
      contact: contact.trim(),
      website,
    });
    setSubmitting(false);

    if (!res.ok) {
      showSubmitNotice(false, res.error);
      return;
    }

    setContent('');
    setContact('');
    setWebsite('');
    setFilterCat('all');

    if (targetChannel === 'public') {
      const pendingEntry: GuestbookEntry = {
        ...res.entry,
        isPendingLocal: true,
      };
      const nextPending = [pendingEntry, ...pendingEntries];
      setPendingEntries(nextPending);
      savePendingGuestbookEntries(nextPending);
      showSubmitNotice(
        true,
        '留言已提交！当前处于「待审核 · 仅自己可见」，站长审核通过后将全网公开显示。'
      );
    } else {
      showSubmitNotice(true, '已私密投递给站长后台（绝不会公开上墙），感谢你的反馈！');
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    void handleSubmitEntry('public');
  };

  const handleDeleteLocal = (id: string) => {
    const next = localEntries.filter((item) => item.id !== id);
    setLocalEntries(next);
    saveLocalGuestbookEntries(next);
  };

  const handleDismissPending = (id: string) => {
    const next = pendingEntries.filter((item) => item.id !== id);
    setPendingEntries(next);
    savePendingGuestbookEntries(next);
  };

  const handleToggleLike = async (entry: GuestbookEntry) => {
    if (entry.isPendingLocal) return;

    if (!isOnline || entry.isLocal) {
      setLikedIds(toggleLikedId(entry.id));
      return;
    }

    if (likingId === entry.id) return;
    setLikingId(entry.id);
    const res = await togglePublicGuestbookLike(entry.id, clientIdRef.current);
    setLikingId(null);

    if (!res.ok) {
      showSubmitNotice(false, res.error);
      return;
    }

    setPublicEntries((prev) =>
      prev.map((item) => (item.id === entry.id ? { ...item, likes: res.likes } : item))
    );
    setLikedIds((prev) => {
      if (res.liked) {
        return prev.includes(entry.id) ? prev : [...prev, entry.id];
      }
      return prev.filter((id) => id !== entry.id);
    });
  };

  const handleJumpCourse = (targetCourseId: string) => {
    if (targetCourseId && targetCourseId !== currentCourse.id) {
      setCourseId(targetCourseId);
    }
    navigate('/year');
  };

  const openMailModal = (params: {
    author: string;
    category: GuestbookCategory;
    courseLabel: string;
    content: string;
  }) => {
    const draft = buildGuestbookMailDraft(params);
    setMailCopiedKey(null);
    setMailCopyFeedback(null);
    setMailModal({
      draft,
      isEmptyContent: !params.content.trim(),
    });
  };

  const handleOpenComposerMail = () => {
    openMailModal({
      author,
      category,
      courseLabel: courseLabelMap[courseId] ?? courseId,
      content,
    });
  };

  const handleCopyMailField = async (
    key: 'to' | 'subject' | 'body' | 'all',
    value: string,
    label: string
  ) => {
    const ok = await copyText(value);
    if (mailCopyTimerRef.current !== null) {
      window.clearTimeout(mailCopyTimerRef.current);
    }
    if (ok) {
      setMailCopiedKey(key);
      setMailCopyFeedback({ ok: true, text: `已复制「${label}」，可直接粘贴到你的网页邮箱或邮件客户端。` });
      mailCopyTimerRef.current = window.setTimeout(() => {
        setMailCopiedKey((prev) => (prev === key ? null : prev));
        mailCopyTimerRef.current = null;
      }, 2200);
    } else {
      setMailCopyFeedback({ ok: false, text: `未能自动写入剪贴板，请手动选中上方「${label}」内容复制。` });
    }
  };

  return (
    <div className="page-container">
      <section className="page-header-card board-hero">
        <Mascot pose="cheer" size={120} />
        <div className="board-hero-main">
          <div className="page-kicker">BROADCAST // COMMUNITY TERMINAL</div>
          <h1 className="page-title">
            <Megaphone size={22} className="text-yellow" /> 站点公告与考研留言板
          </h1>
          <p className="page-desc">
            发布最新真题上线动态、勘误更新日志与公开备考打卡交流；支持「先审后发」公开上墙、私密投递站长及邮件助手。
          </p>
          <div className="contact-pills-row">
            <button
              type="button"
              className={`copy-pill ${copiedKey === 'qq' ? 'copied' : ''}`}
              onClick={() => handleCopy('qq', BRAND.qqGroup)}
              title="点击复制 QQ 群号"
            >
              <Users size={14} />
              <span>QQ 交流群：{BRAND.qqGroup}</span>
              {copiedKey === 'qq' ? <Check size={13} /> : <Copy size={13} />}
              <span className="copy-pill-hint">{copiedKey === 'qq' ? 'COPIED' : 'COPY'}</span>
            </button>

            <button
              type="button"
              className="copy-pill"
              onClick={handleOpenComposerMail}
              title="点击打开邮件投稿与联系助手"
            >
              <Mail size={14} />
              <span>邮箱：{BRAND.contact}</span>
            </button>

            <button
              type="button"
              className={`copy-pill ${copiedKey === 'email' ? 'copied' : ''}`}
              onClick={() => handleCopy('email', BRAND.contact)}
              title="点击复制联系邮箱"
            >
              {copiedKey === 'email' ? <Check size={13} /> : <Copy size={13} />}
              <span>{copiedKey === 'email' ? '邮箱已复制' : '复制邮箱'}</span>
            </button>

            <Link to="/about?section=codex" className="copy-pill accent">
              <Sparkles size={14} />
              <span>鸣谢 Gemini · 角色图鉴 →</span>
            </Link>
          </div>
        </div>
      </section>

      <div className="board-layout">
        {/* Left: System Broadcasts */}
        <section className="board-announcements-col" aria-label="站点公告">
          <div className="section-head">
            <h2 className="section-title">
              <Megaphone size={17} className="text-sky" /> 站点公告 ({announcements.length})
            </h2>
            <span className="hud-code">FEED // SYSTEM</span>
          </div>

          <div className="ann-list">
            {announcements.length === 0 ? (
              <div className="card-panel empty-mini">暂无公告</div>
            ) : (
              announcements.map((ann) => (
                <article key={ann.id} className={`card-panel ann-card ${ann.pinned ? 'pinned' : ''}`}>
                  <div className="ann-meta-row">
                    {ann.pinned && (
                      <span className="status-chip ready">
                        <Pin size={11} /> PINNED
                      </span>
                    )}
                    <span className="ann-tag-chip">{ann.tag}</span>
                    <span className="ann-date">{ann.date}</span>
                  </div>
                  <h3 className="ann-title">{ann.title}</h3>
                  <p className="ann-summary">{ann.summary}</p>
                  {ann.highlights.length > 0 && (
                    <ul className="ann-highlights">
                      {ann.highlights.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  )}
                  {ann.relatedCourses && ann.relatedCourses.length > 0 && (
                    <div className="ann-course-links">
                      {ann.relatedCourses.map((cid) => {
                        const c = courses.find((item) => item.id === cid);
                        if (!c) return null;
                        return (
                          <button
                            key={cid}
                            type="button"
                            className="btn btn-secondary btn-sm"
                            onClick={() => handleJumpCourse(c.id)}
                          >
                            前往 {c.name} 真题 <ArrowRight size={13} />
                          </button>
                        );
                      })}
                    </div>
                  )}
                </article>
              ))
            )}
          </div>
        </section>

        {/* Right: Guestbook Terminal */}
        <section className="board-guestbook-col" aria-label="考研留言板">
          <div className="section-head">
            <h2 className="section-title">
              <MessageSquare size={17} className="text-aqua" /> 考研留言板 ({allEntries.length})
            </h2>
            <div className="gb-head-actions">
              <span className="hud-code">{isOnline ? 'PUBLIC // MODERATED' : 'OFFLINE // CACHE'}</span>
              <button
                type="button"
                className="gb-admin-trigger"
                onClick={() => setAdminOpen(true)}
                title="站长审核管理入口"
              >
                <ShieldCheck size={12} /> 站长审核
              </button>
            </div>
          </div>

          <form className="card-panel guestbook-composer" onSubmit={handleFormSubmit}>
            <div className="gb-cat-row" role="radiogroup" aria-label="留言分类">
              {GUESTBOOK_CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  type="button"
                  className={`gb-cat-pill ${category === cat.id ? 'active' : ''}`}
                  onClick={() => setCategory(cat.id)}
                >
                  {cat.label}
                </button>
              ))}
            </div>

            <div className="gb-input-row">
              <input
                type="text"
                className="gb-input"
                maxLength={20}
                value={author}
                onChange={(e) => setAuthor(e.target.value)}
                placeholder="你的昵称（留空默认「考研人」）"
                aria-label="昵称"
              />
              <select
                className="ui-select"
                value={courseId}
                onChange={(e) => setEntryCourseId(e.target.value)}
                aria-label="关联专业课板块"
              >
                <option value="all">全站通用</option>
                {courses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.shortLabel}
                  </option>
                ))}
              </select>
            </div>

            <input
              type="text"
              className="gb-input gb-contact-input"
              maxLength={60}
              value={contact}
              onChange={(e) => setContact(e.target.value)}
              placeholder="联系方式（选填：QQ/邮箱，仅站长后台可见，绝不公开）"
              aria-label="联系方式（选填）"
            />

            <div className="gb-honeypot" aria-hidden="true">
              <input
                type="text"
                tabIndex={-1}
                autoComplete="off"
                value={website}
                onChange={(e) => setWebsite(e.target.value)}
                placeholder="Leave blank"
              />
            </div>

            <div className="gb-textarea-wrap">
              <textarea
                className="gb-textarea"
                rows={4}
                maxLength={500}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder={activeCategoryMeta.placeholder}
                aria-label="留言内容"
              />
              <span className="gb-char-count">{content.length} / 500</span>
            </div>

            <div className="gb-submit-row">
              <button type="submit" className="btn btn-tactical btn-sm" disabled={submitting}>
                <Send size={14} /> {submitting ? '提交中…' : '提交公开留言'}
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                disabled={submitting}
                onClick={() => void handleSubmitEntry('inbox')}
                title="不公开上墙，直接发送到站长 D1 后台收件箱"
              >
                <Lock size={14} /> 私密投递给站长
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={handleOpenComposerMail}
                title={`生成邮件投稿模板并发送至 ${BRAND.contact}`}
              >
                <Mail size={14} /> 邮件助手
              </button>
            </div>

            {submitNotice && (
              <div className={`feedback-banner ${submitNotice.ok ? 'ok' : 'err'}`}>
                {submitNotice.text}
              </div>
            )}

            <p className="gb-static-note">
              说明：公开留言采用「先审后发」机制——提交后你本机可立即看到「待审核」状态，站长审核通过后全网可见；勘误或敏感反馈可选「私密投递给站长」，也可通过「邮件助手」（
              <code>{BRAND.contact}</code>）或 QQ 群 <code>{BRAND.qqGroup}</code> 联系。
            </p>
          </form>

          <div className="gb-filter-row">
            <button
              type="button"
              className={`gb-filter-chip ${filterCat === 'all' ? 'active' : ''}`}
              onClick={() => setFilterCat('all')}
            >
              全部 ({categoryCounts.all})
            </button>
            {GUESTBOOK_CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                type="button"
                className={`gb-filter-chip ${filterCat === cat.id ? 'active' : ''}`}
                onClick={() => setFilterCat(cat.id)}
              >
                {cat.label} ({categoryCounts[cat.id] ?? 0})
              </button>
            ))}
          </div>

          <div className="gb-feed">
            {boardLoading && visibleEntries.length === 0 ? (
              <div className="card-panel empty-mini">正在同步公开留言板…</div>
            ) : visibleEntries.length === 0 ? (
              <div className="card-panel empty-mini">该分类下暂时还没有留言，欢迎抢占沙发～</div>
            ) : (
              visibleEntries.map((entry) => {
                const isLiked = likedIds.includes(entry.id);
                const useLocalCount = !isOnline || Boolean(entry.isLocal);
                const displayLikes = useLocalCount
                  ? entry.likes + (isLiked ? 1 : 0)
                  : entry.likes;
                const avatarSrc =
                  entry.role === 'assistant'
                    ? './mascot/gemini.webp'
                    : entry.role === 'admin'
                      ? './mascot/hero.webp'
                      : null;
                return (
                  <article key={entry.id} className={`card-panel gb-card ${entry.pinned ? 'pinned' : ''}`}>
                    <div className="gb-card-head">
                      <div className="gb-author-cluster">
                        <div className={`gb-avatar ${entry.role ?? 'user'}`}>
                          {avatarSrc ? (
                            <img src={avatarSrc} alt={entry.author} />
                          ) : (
                            <span>{entry.author.trim().slice(0, 1) || '研'}</span>
                          )}
                        </div>
                        <div>
                          <div className="gb-author-row">
                            <strong className="gb-author-name">{entry.author}</strong>
                            {entry.role === 'admin' && <span className="gb-role-badge admin">ADMIN</span>}
                            {entry.role === 'assistant' && <span className="gb-role-badge ai">AI 助教</span>}
                            {entry.isPendingLocal && (
                              <span className="gb-role-badge pending">待审核 · 仅自己可见</span>
                            )}
                            {entry.isLocal && <span className="gb-role-badge local">LOCAL</span>}
                            {entry.pinned && (
                              <span className="gb-role-badge pin">
                                <Pin size={10} /> 置顶
                              </span>
                            )}
                          </div>
                          <div className="gb-sub-meta">
                            <span>{GUESTBOOK_CATEGORY_LABELS[entry.category] ?? entry.category}</span>
                            <span>·</span>
                            <span>{courseLabelMap[entry.courseId] ?? entry.courseId}</span>
                            <span>·</span>
                            <time className="font-mono">{formatTime(entry.createdAt)}</time>
                          </div>
                        </div>
                      </div>
                    </div>

                    <p className="gb-card-body">{entry.content}</p>

                    {entry.adminReply && (
                      <div className="gb-admin-reply-box">
                        <div className="gb-admin-reply-head">
                          <span>站长回复</span>
                          {entry.adminRepliedAt && (
                            <time className="font-mono">{formatTime(entry.adminRepliedAt)}</time>
                          )}
                        </div>
                        <p className="gb-admin-reply-text">{entry.adminReply}</p>
                      </div>
                    )}

                    <div className="gb-card-foot">
                      <button
                        type="button"
                        className={`gb-like-btn ${isLiked ? 'liked' : ''}`}
                        disabled={Boolean(entry.isPendingLocal) || likingId === entry.id}
                        title={entry.isPendingLocal ? '审核通过公开后即可获赞' : undefined}
                        onClick={() => void handleToggleLike(entry)}
                      >
                        <Heart size={13} fill={isLiked ? 'currentColor' : 'none'} />
                        <span>
                          {entry.isPendingLocal
                            ? '审核中'
                            : displayLikes > 0
                              ? displayLikes
                              : '点赞'}
                        </span>
                      </button>

                      {entry.isPendingLocal && (
                        <div className="gb-local-actions">
                          <button
                            type="button"
                            className="gb-delete-btn"
                            onClick={() => handleDismissPending(entry.id)}
                            title="仅移除本机预览卡片，不影响后台审核队列"
                          >
                            <Trash2 size={12} /> 隐藏本地预览
                          </button>
                        </div>
                      )}

                      {entry.isLocal && (
                        <div className="gb-local-actions">
                          <button
                            type="button"
                            className="gb-action-link"
                            onClick={() =>
                              openMailModal({
                                author: entry.author,
                                category: entry.category,
                                courseLabel: courseLabelMap[entry.courseId] ?? entry.courseId,
                                content: entry.content,
                              })
                            }
                          >
                            <Mail size={12} /> 发邮件给站长
                          </button>
                          <button
                            type="button"
                            className="gb-delete-btn"
                            onClick={() => handleDeleteLocal(entry.id)}
                            title="删除这条本地留言"
                          >
                            <Trash2 size={12} /> 删除
                          </button>
                        </div>
                      )}
                    </div>
                  </article>
                );
              })
            )}
          </div>
        </section>
      </div>

      <GuestbookAdminModal
        open={adminOpen}
        courses={courses}
        courseLabelMap={courseLabelMap}
        onClose={() => {
          setAdminOpen(false);
          void refreshGuestbook();
        }}
      />

      {mailModal && (
        <div className="modal-backdrop" onClick={() => setMailModal(null)}>
          <div
            className="modal-panel"
            role="dialog"
            aria-modal="true"
            aria-labelledby="mail-modal-title"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <div>
                <div className="page-kicker">MAIL DISPATCH // WEBMAIL HELPER</div>
                <h3 id="mail-modal-title" className="modal-title">
                  邮件投稿给站长
                </h3>
                <p className="modal-sub">
                  若电脑未配置默认邮箱软件（QQ/163/Gmail 网页版用户常见），可直接复制下方内容发送，或一键跳转网页版邮箱。
                </p>
              </div>
              <button
                type="button"
                className="icon-btn"
                onClick={() => setMailModal(null)}
                aria-label="关闭邮件投稿助手"
              >
                <X size={18} />
              </button>
            </div>

            <div className="gb-mail-body">
              {mailModal.isEmptyContent && (
                <div className="gb-mail-warn">
                  提示：你在输入框暂未填写正文。可以先关闭弹窗补充具体年份/题号或留言，也可以直接复制站长邮箱联系。
                </div>
              )}

              <div className="gb-mail-field">
                <div className="gb-mail-field-head">
                  <span className="gb-mail-label">收件人邮箱</span>
                  <button
                    type="button"
                    className={`gb-mail-copy-btn ${mailCopiedKey === 'to' ? 'copied' : ''}`}
                    onClick={() => handleCopyMailField('to', mailModal.draft.to, '收件人邮箱')}
                  >
                    {mailCopiedKey === 'to' ? <Check size={12} /> : <Copy size={12} />}
                    <span>{mailCopiedKey === 'to' ? '已复制' : '复制邮箱'}</span>
                  </button>
                </div>
                <div className="gb-mail-value font-mono">{mailModal.draft.to}</div>
              </div>

              <div className="gb-mail-field">
                <div className="gb-mail-field-head">
                  <span className="gb-mail-label">邮件主题</span>
                  <button
                    type="button"
                    className={`gb-mail-copy-btn ${mailCopiedKey === 'subject' ? 'copied' : ''}`}
                    onClick={() => handleCopyMailField('subject', mailModal.draft.subject, '邮件主题')}
                  >
                    {mailCopiedKey === 'subject' ? <Check size={12} /> : <Copy size={12} />}
                    <span>{mailCopiedKey === 'subject' ? '已复制' : '复制主题'}</span>
                  </button>
                </div>
                <div className="gb-mail-value">{mailModal.draft.subject}</div>
              </div>

              <div className="gb-mail-field">
                <div className="gb-mail-field-head">
                  <span className="gb-mail-label">邮件正文</span>
                  <button
                    type="button"
                    className={`gb-mail-copy-btn ${mailCopiedKey === 'body' ? 'copied' : ''}`}
                    onClick={() => handleCopyMailField('body', mailModal.draft.body, '邮件正文')}
                  >
                    {mailCopiedKey === 'body' ? <Check size={12} /> : <Copy size={12} />}
                    <span>{mailCopiedKey === 'body' ? '已复制' : '复制正文'}</span>
                  </button>
                </div>
                <pre className="gb-mail-preview">{mailModal.draft.body}</pre>
              </div>

              <div className="gb-mail-actions">
                <button
                  type="button"
                  className="btn btn-tactical btn-sm"
                  onClick={() =>
                    handleCopyMailField(
                      'all',
                      mailModal.draft.fullText,
                      '完整邮件内容（收件人+主题+正文）'
                    )
                  }
                >
                  {mailCopiedKey === 'all' ? <Check size={14} /> : <Copy size={14} />}
                  <span>{mailCopiedKey === 'all' ? '已复制全部内容' : '一键复制全部内容'}</span>
                </button>
                <a
                  href={mailModal.draft.gmailHref}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-secondary btn-sm"
                >
                  <ExternalLink size={14} /> Gmail 网页版写信
                </a>
                <a
                  href={mailModal.draft.outlookHref}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-secondary btn-sm"
                >
                  <ExternalLink size={14} /> Outlook 网页版写信
                </a>
                <a href={mailModal.draft.mailtoHref} className="btn btn-secondary btn-sm">
                  <Mail size={14} /> 唤起本机邮箱软件
                </a>
              </div>

              {mailCopyFeedback && (
                <div className={`feedback-banner ${mailCopyFeedback.ok ? 'ok' : 'err'}`}>
                  {mailCopyFeedback.text}
                </div>
              )}

              <p className="gb-mail-tip">
                QQ 邮箱 / 163 网易邮箱用户：点击上方复制按钮后，在网页邮箱粘贴收件人、主题与正文即可；也可直接加入考研交流 QQ 群{' '}
                <code>{BRAND.qqGroup}</code> 反馈。
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
