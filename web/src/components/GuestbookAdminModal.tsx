import React, { useCallback, useEffect, useState } from 'react';
import {
  Check,
  CheckCheck,
  Eye,
  KeyRound,
  LogOut,
  MessageSquarePlus,
  Pin,
  PinOff,
  RefreshCw,
  Reply,
  ShieldCheck,
  Trash2,
  X,
  XCircle,
} from 'lucide-react';
import type {
  AdminGuestbookCounts,
  AdminGuestbookEntry,
  AdminGuestbookTab,
  CourseMeta,
  GuestbookCategory,
  GuestbookChannel,
  GuestbookStatus,
} from '../types';
import {
  GUESTBOOK_CATEGORIES,
  GUESTBOOK_CATEGORY_LABELS,
  deleteAdminGuestbook,
  fetchAdminGuestbook,
  loadSavedAdminToken,
  publishAdminGuestbook,
  saveAdminToken,
  updateAdminGuestbook,
} from '../utils/guestbook';

interface GuestbookAdminModalProps {
  open: boolean;
  courses: CourseMeta[];
  courseLabelMap: Record<string, string>;
  onClose: () => void;
}

const EMPTY_COUNTS: AdminGuestbookCounts = {
  pendingPublic: 0,
  pendingInbox: 0,
  approved: 0,
  inboxAll: 0,
  rejected: 0,
};

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

export const GuestbookAdminModal: React.FC<GuestbookAdminModalProps> = ({
  open,
  courses,
  courseLabelMap,
  onClose,
}) => {
  const [activeToken, setActiveToken] = useState<string>(loadSavedAdminToken);
  const [tokenInput, setTokenInput] = useState('');
  const [authed, setAuthed] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  const [tab, setTab] = useState<AdminGuestbookTab>('pending');
  const [entries, setEntries] = useState<AdminGuestbookEntry[]>([]);
  const [counts, setCounts] = useState<AdminGuestbookCounts>(EMPTY_COUNTS);
  const [listLoading, setListLoading] = useState(false);
  const [actionFeedback, setActionFeedback] = useState<{ ok: boolean; text: string } | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const [replyingId, setReplyingId] = useState<string | null>(null);
  const [replyDraft, setReplyDraft] = useState('');

  const [composeOpen, setComposeOpen] = useState(false);
  const [postRole, setPostRole] = useState<'admin' | 'assistant'>('admin');
  const [postCategory, setPostCategory] = useState<GuestbookCategory>('checkin');
  const [postCourseId, setPostCourseId] = useState('all');
  const [postContent, setPostContent] = useState('');
  const [postPinned, setPostPinned] = useState(false);
  const [posting, setPosting] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open, onClose]);

  const handleUnauthorized = useCallback((message: string) => {
    saveAdminToken('');
    setActiveToken('');
    setAuthed(false);
    setEntries([]);
    setAuthError(message);
  }, []);

  const loadTab = useCallback(
    async (token: string, targetTab: AdminGuestbookTab) => {
      setListLoading(true);
      setActionFeedback(null);
      const res = await fetchAdminGuestbook(token, targetTab);
      setListLoading(false);
      if (!res.ok) {
        if (res.status === 401) {
          handleUnauthorized('登录凭据已失效，请重新输入站长管理口令。');
        } else {
          setActionFeedback({ ok: false, text: res.error });
        }
        return false;
      }
      setAuthed(true);
      setAuthError(null);
      setEntries(res.entries);
      setCounts(res.counts);
      return true;
    },
    [handleUnauthorized]
  );

  useEffect(() => {
    if (!open) return;
    if (activeToken) {
      void loadTab(activeToken, tab);
    }
  }, [open, activeToken, tab, loadTab]);

  if (!open) return null;

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = tokenInput.trim();
    if (!trimmed) {
      setAuthError('请输入站长管理口令');
      return;
    }
    setAuthLoading(true);
    setAuthError(null);
    const res = await fetchAdminGuestbook(trimmed, tab);
    setAuthLoading(false);
    if (!res.ok) {
      setAuthError(res.status === 401 ? '管理口令不正确，请核对后重试。' : res.error);
      return;
    }
    saveAdminToken(trimmed);
    setActiveToken(trimmed);
    setTokenInput('');
    setAuthed(true);
    setEntries(res.entries);
    setCounts(res.counts);
  };

  const handleLogout = () => {
    saveAdminToken('');
    setActiveToken('');
    setAuthed(false);
    setEntries([]);
    setCounts(EMPTY_COUNTS);
    setActionFeedback(null);
    setAuthError(null);
  };

  const handlePatch = async (
    id: string,
    patch: {
      status?: GuestbookStatus;
      channel?: GuestbookChannel;
      pinned?: boolean;
      adminReply?: string;
    },
    successText: string
  ) => {
    if (!activeToken) return;
    setBusyId(id);
    setActionFeedback(null);
    const res = await updateAdminGuestbook(activeToken, id, patch);
    setBusyId(null);
    if (!res.ok) {
      if (res.status === 401) {
        handleUnauthorized('登录已过期，请重新输入管理口令。');
      } else {
        setActionFeedback({ ok: false, text: res.error });
      }
      return false;
    }
    await loadTab(activeToken, tab);
    setActionFeedback({ ok: true, text: successText });
    return true;
  };

  const handleDelete = async (id: string) => {
    if (!activeToken) return;
    setBusyId(id);
    setActionFeedback(null);
    const res = await deleteAdminGuestbook(activeToken, id);
    setBusyId(null);
    setConfirmDeleteId(null);
    if (!res.ok) {
      if (res.status === 401) {
        handleUnauthorized('登录已过期，请重新输入管理口令。');
      } else {
        setActionFeedback({ ok: false, text: res.error });
      }
      return;
    }
    await loadTab(activeToken, tab);
    setActionFeedback({ ok: true, text: '已永久删除该条留言。' });
  };

  const handleSaveReply = async (entry: AdminGuestbookEntry) => {
    const trimmed = replyDraft.trim();
    const canViewPrivately = Boolean(entry.accountBound || entry.hasReceipt);
    const successText = !trimmed
      ? '已清空站长回复。'
      : entry.channel === 'inbox' && entry.accountBound
        ? '已保存私密回复（已自动标记已阅，对方可在已绑定账号跨设备查看）。'
        : entry.channel === 'inbox' && canViewPrivately
          ? '已保存私密回复（已自动标记已阅，提交者可在本机查看）。'
          : entry.channel === 'inbox'
            ? '已保存后台回复（已自动标记已阅；旧版无回执投递仅后台可见）。'
            : '已保存站长回复。';
    const ok = await handlePatch(entry.id, { adminReply: replyDraft }, successText);
    if (ok) {
      setReplyingId(null);
      setReplyDraft('');
    }
  };

  const handlePublishOfficial = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeToken) return;
    const trimmed = postContent.trim();
    if (trimmed.length < 2) {
      setActionFeedback({ ok: false, text: '官方留言内容至少需要 2 个字。' });
      return;
    }
    setPosting(true);
    setActionFeedback(null);
    const res = await publishAdminGuestbook(activeToken, {
      role: postRole,
      category: postCategory,
      courseId: postCourseId,
      content: trimmed,
      pinned: postPinned,
    });
    setPosting(false);
    if (!res.ok) {
      if (res.status === 401) {
        handleUnauthorized('登录已过期，请重新输入管理口令。');
      } else {
        setActionFeedback({ ok: false, text: res.error });
      }
      return;
    }
    setPostContent('');
    setPostPinned(false);
    setComposeOpen(false);
    if (tab !== 'approved') {
      setTab('approved');
    } else {
      await loadTab(activeToken, 'approved');
    }
    setActionFeedback({ ok: true, text: '官方留言已直接发布到公开留言板！' });
  };

  const tabItems: Array<{ id: AdminGuestbookTab; label: string; count: string }> = [
    { id: 'pending', label: '待审核公开', count: String(counts.pendingPublic) },
    { id: 'inbox', label: '私密投稿箱', count: `${counts.pendingInbox}/${counts.inboxAll}` },
    { id: 'approved', label: '已公开', count: String(counts.approved) },
    { id: 'rejected', label: '已驳回', count: String(counts.rejected) },
  ];

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-panel gb-admin-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="gb-admin-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <div>
            <div className="page-kicker">MODERATION CONSOLE // D1 ADMIN</div>
            <h3 id="gb-admin-modal-title" className="modal-title">
              站长审核与私密投稿后台
            </h3>
            <p className="modal-sub">
              先审后发管理台：公开留言审核通过后才会向所有访客展示；私密投递不公开上墙，提交者可在本机凭回执私密查看站长回复。
            </p>
          </div>
          <button
            type="button"
            className="icon-btn"
            onClick={onClose}
            aria-label="关闭站长审核后台"
          >
            <X size={18} />
          </button>
        </div>

        {!authed ? (
          <form className="gb-admin-login" onSubmit={handleLogin}>
            <div className="gb-admin-login-hint">
              <KeyRound size={16} className="text-yellow" />
              <span>
                请输入站长管理口令（保存在 Cloudflare Worker Secret <code>ADMIN_TOKEN</code> 中）：
              </span>
            </div>
            <div className="gb-admin-login-row">
              <input
                type="password"
                className="gb-input"
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                placeholder="输入管理口令..."
                autoFocus
                aria-label="站长管理口令"
              />
              <button
                type="submit"
                className="btn btn-tactical btn-sm"
                disabled={authLoading}
              >
                <ShieldCheck size={14} /> {authLoading ? '验证中…' : '进入审核后台'}
              </button>
            </div>
            {authError && <div className="feedback-banner err">{authError}</div>}
          </form>
        ) : (
          <div className="gb-admin-body">
            <div className="gb-admin-toolbar">
              <div className="gb-admin-status-pill">
                <ShieldCheck size={13} /> 已验证站长权限
              </div>
              <div className="gb-admin-toolbar-actions">
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => setComposeOpen((prev) => !prev)}
                >
                  <MessageSquarePlus size={13} /> {composeOpen ? '收起官方发帖' : '发布官方留言'}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => void loadTab(activeToken, tab)}
                  disabled={listLoading}
                >
                  <RefreshCw size={13} /> {listLoading ? '刷新中…' : '刷新'}
                </button>
                <button
                  type="button"
                  className="btn btn-ghost-danger btn-sm"
                  onClick={handleLogout}
                >
                  <LogOut size={13} /> 退出登录
                </button>
              </div>
            </div>

            {composeOpen && (
              <form className="gb-admin-compose" onSubmit={handlePublishOfficial}>
                <div className="gb-admin-compose-row">
                  <select
                    className="ui-select"
                    value={postRole}
                    onChange={(e) => setPostRole(e.target.value as 'admin' | 'assistant')}
                    aria-label="发言身份"
                  >
                    <option value="admin">站长 · 大肥鱼 (ADMIN)</option>
                    <option value="assistant">Gemini · AI 助教</option>
                  </select>
                  <select
                    className="ui-select"
                    value={postCategory}
                    onChange={(e) => setPostCategory(e.target.value as GuestbookCategory)}
                    aria-label="留言分类"
                  >
                    {GUESTBOOK_CATEGORIES.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.label}
                      </option>
                    ))}
                  </select>
                  <select
                    className="ui-select"
                    value={postCourseId}
                    onChange={(e) => setPostCourseId(e.target.value)}
                    aria-label="关联板块"
                  >
                    <option value="all">全站通用</option>
                    {courses.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.shortLabel}
                      </option>
                    ))}
                  </select>
                </div>
                <textarea
                  className="gb-textarea"
                  rows={3}
                  maxLength={500}
                  value={postContent}
                  onChange={(e) => setPostContent(e.target.value)}
                  placeholder="直接发布一条全网可见的官方公告、勘误说明或置顶寄语…"
                />
                <div className="gb-admin-compose-foot">
                  <label className="gb-admin-pin-check">
                    <input
                      type="checkbox"
                      checked={postPinned}
                      onChange={(e) => setPostPinned(e.target.checked)}
                    />
                    <span>置顶显示</span>
                  </label>
                  <button type="submit" className="btn btn-tactical btn-sm" disabled={posting}>
                    {posting ? '发布中…' : '直接公开上线'}
                  </button>
                </div>
              </form>
            )}

            <div className="gb-admin-tabs" role="tablist">
              {tabItems.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  role="tab"
                  aria-selected={tab === item.id}
                  className={`gb-filter-chip ${tab === item.id ? 'active' : ''}`}
                  onClick={() => {
                    setConfirmDeleteId(null);
                    setReplyingId(null);
                    setTab(item.id);
                  }}
                >
                  {item.label} ({item.count})
                </button>
              ))}
            </div>

            {actionFeedback && (
              <div className={`feedback-banner ${actionFeedback.ok ? 'ok' : 'err'}`}>
                {actionFeedback.text}
              </div>
            )}

            <div className="gb-admin-list">
              {listLoading && entries.length === 0 ? (
                <div className="empty-mini">正在加载数据库记录…</div>
              ) : entries.length === 0 ? (
                <div className="empty-mini">当前分类下暂无记录 ✨</div>
              ) : (
                entries.map((entry) => {
                  const isBusy = busyId === entry.id;
                  const isReplying = replyingId === entry.id;
                  return (
                    <article key={entry.id} className="gb-admin-card">
                      <div className="gb-admin-card-head">
                        <div className="gb-author-row">
                          <strong className="gb-author-name">{entry.author}</strong>
                          {entry.role === 'admin' && <span className="gb-role-badge admin">ADMIN</span>}
                          {entry.role === 'assistant' && <span className="gb-role-badge ai">AI 助教</span>}
                          <span className={`gb-role-badge ${entry.channel === 'inbox' ? 'inbox' : 'local'}`}>
                            {entry.channel === 'inbox' ? '私密投递' : '公开区'}
                          </span>
                          {entry.channel === 'inbox' && entry.accountBound && (
                            <span className="gb-role-badge local">账号可跨设备看回复</span>
                          )}
                          {entry.channel === 'inbox' && !entry.accountBound && entry.hasReceipt && (
                            <span className="gb-role-badge local">本机可看回复</span>
                          )}
                          <span
                            className={`gb-role-badge ${
                              entry.status === 'pending'
                                ? 'pending'
                                : entry.status === 'approved'
                                  ? 'admin'
                                  : 'rejected'
                            }`}
                          >
                            {entry.status === 'pending'
                              ? entry.channel === 'inbox'
                                ? '未读'
                                : '待审核'
                              : entry.status === 'approved'
                                ? entry.channel === 'inbox'
                                  ? '已阅'
                                  : '已公开'
                                : '已驳回'}
                          </span>
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

                      {entry.channel === 'inbox' && !entry.accountBound && !entry.hasReceipt && (
                        <div className="gb-admin-legacy-note">
                          旧版私密投递（无本机回执）：仅私密回复对方不可见；如需通知对方，可转为「公开上墙」或另发官方留言。
                        </div>
                      )}

                      {entry.contact && (
                        <div className="gb-admin-contact">
                          联系方式（仅站长可见）：<code>{entry.contact}</code>
                        </div>
                      )}

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

                      {isReplying && (
                        <div className="gb-admin-reply-form">
                          <textarea
                            className="gb-textarea"
                            rows={2}
                            maxLength={500}
                            value={replyDraft}
                            onChange={(e) => setReplyDraft(e.target.value)}
                            placeholder={
                              entry.channel === 'inbox'
                                ? entry.accountBound || entry.hasReceipt
                                  ? '填写私密回复（仅提交者本人可见，不公开上墙；保存后自动标记已阅）…'
                                  : '填写后台回复/备注（旧版无回执投递，仅后台可见；公开上墙后访客方可见）…'
                                : '填写官方回复（留空保存可清空已有回复）…'
                            }
                          />
                          <div className="gb-admin-actions">
                            <button
                              type="button"
                              className="btn btn-tactical btn-sm"
                              disabled={isBusy}
                              onClick={() => void handleSaveReply(entry)}
                            >
                              <Check size={13} /> 保存回复
                            </button>
                            <button
                              type="button"
                              className="btn btn-secondary btn-sm"
                              onClick={() => {
                                setReplyingId(null);
                                setReplyDraft('');
                              }}
                            >
                              取消
                            </button>
                          </div>
                        </div>
                      )}

                      <div className="gb-admin-actions">
                        {entry.channel === 'public' && entry.status === 'pending' && (
                          <>
                            <button
                              type="button"
                              className="btn btn-tactical btn-sm"
                              disabled={isBusy}
                              onClick={() =>
                                void handlePatch(
                                  entry.id,
                                  { status: 'approved' },
                                  '已通过审核，该留言现已全网公开！'
                                )
                              }
                            >
                              <Check size={13} /> 通过公开
                            </button>
                            <button
                              type="button"
                              className="btn btn-secondary btn-sm"
                              disabled={isBusy}
                              onClick={() =>
                                void handlePatch(entry.id, { status: 'rejected' }, '已驳回该条留言。')
                              }
                            >
                              <XCircle size={13} /> 驳回
                            </button>
                          </>
                        )}

                        {entry.channel === 'inbox' && (
                          <>
                            {entry.status === 'pending' && (
                              <button
                                type="button"
                                className="btn btn-tactical btn-sm"
                                disabled={isBusy}
                                onClick={() =>
                                  void handlePatch(
                                    entry.id,
                                    { status: 'approved' },
                                    '已标记为已阅（仍保持私密，不公开上墙）。'
                                  )
                                }
                              >
                                <CheckCheck size={13} /> 标记已阅
                              </button>
                            )}
                            <button
                              type="button"
                              className="btn btn-secondary btn-sm"
                              disabled={isBusy}
                              onClick={() =>
                                void handlePatch(
                                  entry.id,
                                  { status: 'approved', channel: 'public' },
                                  '已将该条投稿转为公开上墙！'
                                )
                              }
                            >
                              <Eye size={13} /> 公开上墙
                            </button>
                          </>
                        )}

                        {entry.channel === 'public' && entry.status === 'approved' && (
                          <>
                            <button
                              type="button"
                              className="btn btn-secondary btn-sm"
                              disabled={isBusy}
                              onClick={() =>
                                void handlePatch(
                                  entry.id,
                                  { pinned: !entry.pinned },
                                  entry.pinned ? '已取消置顶。' : '已置顶该条留言。'
                                )
                              }
                            >
                              {entry.pinned ? <PinOff size={13} /> : <Pin size={13} />}
                              <span>{entry.pinned ? '取消置顶' : '置顶'}</span>
                            </button>
                            <button
                              type="button"
                              className="btn btn-secondary btn-sm"
                              disabled={isBusy}
                              onClick={() =>
                                void handlePatch(
                                  entry.id,
                                  { status: 'rejected', pinned: false },
                                  '已撤下该条留言。'
                                )
                              }
                            >
                              <XCircle size={13} /> 撤下
                            </button>
                          </>
                        )}

                        {entry.status === 'rejected' && (
                          <button
                            type="button"
                            className="btn btn-tactical btn-sm"
                            disabled={isBusy}
                            onClick={() =>
                              void handlePatch(
                                entry.id,
                                { status: 'approved', channel: 'public' },
                                '已恢复并公开该条留言。'
                              )
                            }
                          >
                            <Check size={13} /> 恢复公开
                          </button>
                        )}

                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          disabled={isBusy}
                          onClick={() => {
                            if (isReplying) {
                              setReplyingId(null);
                              setReplyDraft('');
                            } else {
                              setReplyingId(entry.id);
                              setReplyDraft(entry.adminReply ?? '');
                            }
                          }}
                        >
                          <Reply size={13} /> 回复
                        </button>

                        {confirmDeleteId === entry.id ? (
                          <button
                            type="button"
                            className="btn btn-danger btn-sm"
                            disabled={isBusy}
                            onClick={() => void handleDelete(entry.id)}
                          >
                            <Trash2 size={13} /> 确认删除
                          </button>
                        ) : (
                          <button
                            type="button"
                            className="btn btn-ghost-danger btn-sm"
                            disabled={isBusy}
                            onClick={() => setConfirmDeleteId(entry.id)}
                          >
                            <Trash2 size={13} /> 删除
                          </button>
                        )}
                      </div>
                    </article>
                  );
                })
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
