import React, { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  Check,
  Copy,
  Heart,
  Mail,
  Megaphone,
  MessageSquare,
  Pin,
  Send,
  Sparkles,
  Trash2,
  Users,
} from 'lucide-react';
import { BRAND } from '../brand';
import { Mascot } from '../components/Mascot';
import { useData } from '../context/DataContext';
import type { GuestbookCategory, GuestbookEntry } from '../types';
import { copyText } from '../utils/clipboard';
import {
  GUESTBOOK_CATEGORIES,
  GUESTBOOK_CATEGORY_LABELS,
  buildGuestbookMailto,
  fetchSeedGuestbook,
  loadLikedIds,
  loadLocalGuestbookEntries,
  saveLocalGuestbookEntries,
  toggleLikedId,
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

  const [copiedKey, setCopiedKey] = useState<'qq' | 'email' | null>(null);
  const [seedEntries, setSeedEntries] = useState<GuestbookEntry[]>([]);
  const [localEntries, setLocalEntries] = useState<GuestbookEntry[]>(loadLocalGuestbookEntries);
  const [likedIds, setLikedIds] = useState<string[]>(loadLikedIds);
  const [filterCat, setFilterCat] = useState<'all' | GuestbookCategory>('all');

  const [author, setAuthor] = useState('');
  const [category, setCategory] = useState<GuestbookCategory>('checkin');
  const [courseId, setEntryCourseId] = useState<string>('all');
  const [content, setContent] = useState('');
  const [submitNotice, setSubmitNotice] = useState<string | null>(null);

  useEffect(() => {
    markAnnouncementsRead();
  }, [markAnnouncementsRead]);

  useEffect(() => {
    let cancelled = false;
    fetchSeedGuestbook().then((entries) => {
      if (!cancelled) setSeedEntries(entries);
    });
    return () => {
      cancelled = true;
    };
  }, []);

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
    const merged = [...localEntries, ...seedEntries];
    return merged.sort((a, b) => {
      if (Boolean(a.pinned) !== Boolean(b.pinned)) return a.pinned ? -1 : 1;
      return b.createdAt.localeCompare(a.createdAt);
    });
  }, [localEntries, seedEntries]);

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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = content.trim();
    if (!trimmed) {
      setSubmitNotice('请先填写留言内容再发布哦～');
      return;
    }
    const newEntry: GuestbookEntry = {
      id: `local-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      author: author.trim() || '考研人',
      role: 'user',
      category,
      courseId,
      content: trimmed,
      createdAt: new Date().toISOString(),
      likes: 0,
      isLocal: true,
    };
    const next = [newEntry, ...localEntries];
    setLocalEntries(next);
    saveLocalGuestbookEntries(next);
    setContent('');
    setFilterCat('all');
    setSubmitNotice('留言已发布并保存到本机！如需提交公开勘误，也可点击「邮件投稿给站长」。');
    window.setTimeout(() => setSubmitNotice(null), 4000);
  };

  const handleDeleteLocal = (id: string) => {
    const next = localEntries.filter((item) => item.id !== id);
    setLocalEntries(next);
    saveLocalGuestbookEntries(next);
  };

  const handleToggleLike = (id: string) => {
    setLikedIds(toggleLikedId(id));
  };

  const handleJumpCourse = (targetCourseId: string) => {
    if (targetCourseId && targetCourseId !== currentCourse.id) {
      setCourseId(targetCourseId);
    }
    navigate('/year');
  };

  const mailtoDraftHref = buildGuestbookMailto({
    author,
    category,
    courseLabel: courseLabelMap[courseId] ?? courseId,
    content: content.trim() || '（请在此补充具体题号或留言内容）',
  });

  return (
    <div className="page-container">
      {/* Page Hero */}
      <section className="page-header-card board-hero">
        <Mascot pose="cheer" size={120} />
        <div className="board-hero-main">
          <h1 className="page-title">
            <Megaphone size={22} className="text-sky" /> 站点公告与考研留言板
          </h1>
          <p className="page-desc">
            发布最新真题上线动态、勘误更新日志与备考交流打卡；欢迎加入考研 QQ 群或直接发邮件联系站长。
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
              <span className="copy-pill-hint">{copiedKey === 'qq' ? '已复制' : '复制群号'}</span>
            </button>

            <a href={`mailto:${BRAND.contact}`} className="copy-pill">
              <Mail size={14} />
              <span>邮箱：{BRAND.contact}</span>
            </a>

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
        {/* Left: Announcements */}
        <section className="board-announcements-col" aria-label="站点公告">
          <div className="section-head">
            <h2 className="section-title">
              <Megaphone size={18} className="text-sky" /> 站点公告 ({announcements.length})
            </h2>
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
                        <Pin size={11} /> 置顶
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
                            className="btn btn-ghost btn-sm"
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

        {/* Right: Guestbook */}
        <section className="board-guestbook-col" aria-label="考研留言板">
          <div className="section-head">
            <h2 className="section-title">
              <MessageSquare size={18} className="text-aqua" /> 考研留言板 ({allEntries.length})
            </h2>
          </div>

          <form className="card-panel guestbook-composer" onSubmit={handleSubmit}>
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
              <button type="submit" className="btn btn-primary btn-sm">
                <Send size={14} /> 发布留言
              </button>
              <a
                href={mailtoDraftHref}
                className="btn btn-ghost btn-sm"
                title={`一键生成邮件发送至 ${BRAND.contact}`}
              >
                <Mail size={14} /> 邮件投稿给站长
              </a>
            </div>

            {submitNotice && <div className="feedback-banner ok">{submitNotice}</div>}

            <p className="gb-static-note">
              说明：本站当前为纯静态站点，你在本页发布的留言将保存在当前浏览器本地（localStorage）；若希望公开上墙、提交真题勘误或实时讨论，欢迎点击「邮件投稿给站长」（
              <code>{BRAND.contact}</code>）或加入 QQ 群 <code>{BRAND.qqGroup}</code>。
            </p>
          </form>

          {/* Filter pills */}
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

          {/* Guestbook Feed */}
          <div className="gb-feed">
            {visibleEntries.length === 0 ? (
              <div className="card-panel empty-mini">该分类下暂时还没有留言，欢迎抢占沙发～</div>
            ) : (
              visibleEntries.map((entry) => {
                const isLiked = likedIds.includes(entry.id);
                const displayLikes = entry.likes + (isLiked ? 1 : 0);
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
                            {entry.role === 'admin' && <span className="gb-role-badge admin">站长</span>}
                            {entry.role === 'assistant' && <span className="gb-role-badge ai">AI 助教</span>}
                            {entry.isLocal && <span className="gb-role-badge local">我的留言</span>}
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
                            <time>{formatTime(entry.createdAt)}</time>
                          </div>
                        </div>
                      </div>
                    </div>

                    <p className="gb-card-body">{entry.content}</p>

                    <div className="gb-card-foot">
                      <button
                        type="button"
                        className={`gb-like-btn ${isLiked ? 'liked' : ''}`}
                        onClick={() => handleToggleLike(entry.id)}
                      >
                        <Heart size={13} fill={isLiked ? 'currentColor' : 'none'} />
                        <span>{displayLikes > 0 ? displayLikes : '点赞'}</span>
                      </button>

                      {entry.isLocal && (
                        <div className="gb-local-actions">
                          <a
                            href={buildGuestbookMailto({
                              author: entry.author,
                              category: entry.category,
                              courseLabel: courseLabelMap[entry.courseId] ?? entry.courseId,
                              content: entry.content,
                            })}
                            className="gb-action-link"
                          >
                            <Mail size={12} /> 发邮件给站长
                          </a>
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
    </div>
  );
};
