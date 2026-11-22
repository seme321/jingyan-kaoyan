import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowRight,
  Check,
  Cloud,
  CloudDownload,
  CloudUpload,
  GitMerge,
  KeyRound,
  Lock,
  LogIn,
  LogOut,
  RefreshCw,
  ShieldCheck,
  UserCheck,
  UserPlus,
  X,
} from 'lucide-react';
import { useAccount } from '../context/AccountContext';
import { useData } from '../context/DataContext';
import { useStudy } from '../context/StudyContext';
import { GUESTBOOK_CATEGORY_LABELS } from '../utils/guestbook';
import { summarizeStudyState } from '../utils/account';

function formatTime(iso?: string): string {
  if (!iso) return '暂无';
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso.slice(0, 16);
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  } catch {
    return iso.slice(0, 16);
  }
}

export const AccountModal: React.FC = () => {
  const {
    user,
    backendOnline,
    cloudMeta,
    syncStatus,
    syncError,
    syncConflict,
    accountInbox,
    inboxLoading,
    repliedAccountInboxCount,
    modalOpen,
    modalTab,
    closeAccountModal,
    setModalTab,
    login,
    register,
    logout,
    logoutOthers,
    updateProfile,
    changePassword,
    pushToCloud,
    pullFromCloud,
    mergeAndSync,
    refreshAccountInbox,
  } = useAccount();
  const { multiState } = useStudy();
  const { courses } = useData();

  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [authBusy, setAuthBusy] = useState(false);
  const [authFeedback, setAuthFeedback] = useState<{ ok: boolean; text: string } | null>(null);

  const [syncBusy, setSyncBusy] = useState(false);
  const [syncFeedback, setSyncFeedback] = useState<{ ok: boolean; text: string } | null>(null);

  const [editDisplayName, setEditDisplayName] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [secBusy, setSecBusy] = useState(false);
  const [secFeedback, setSecFeedback] = useState<{ ok: boolean; text: string } | null>(null);

  useEffect(() => {
    if (user) {
      setEditDisplayName(user.displayName);
    }
  }, [user]);

  useEffect(() => {
    if (!modalOpen) return;
    setAuthFeedback(null);
    setSyncFeedback(null);
    setSecFeedback(null);
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        closeAccountModal();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [modalOpen, closeAccountModal]);

  const courseLabelMap = useMemo(() => {
    const map: Record<string, string> = { all: '全站通用' };
    for (const c of courses) {
      map[c.id] = c.shortLabel;
    }
    return map;
  }, [courses]);

  const localSummary = useMemo(() => summarizeStudyState(multiState), [multiState]);
  const cloudSummary = useMemo(
    () => (syncConflict ? summarizeStudyState(syncConflict.cloudData) : null),
    [syncConflict]
  );

  if (!modalOpen) return null;

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const u = username.trim();
    if (!/^[a-zA-Z0-9_-]{3,20}$/.test(u)) {
      setAuthFeedback({ ok: false, text: '用户名需为 3~20 位字母、数字、下划线或短横线' });
      return;
    }
    if (password.length < 6) {
      setAuthFeedback({ ok: false, text: '密码至少需要 6 位' });
      return;
    }
    if (authMode === 'register' && password !== confirmPassword) {
      setAuthFeedback({ ok: false, text: '两次输入的密码不一致' });
      return;
    }

    setAuthBusy(true);
    setAuthFeedback(null);
    const res =
      authMode === 'login'
        ? await login(u, password)
        : await register(u, password, displayName.trim() || undefined);
    setAuthBusy(false);

    if (!res.ok) {
      setAuthFeedback({ ok: false, text: res.error || '操作失败，请稍后重试' });
      return;
    }

    setPassword('');
    setConfirmPassword('');
    setAuthFeedback({
      ok: true,
      text: authMode === 'login' ? '登录成功！正在为你同步云端数据与私密投递…' : '注册并登录成功！',
    });
  };

  const handleMergeSync = async () => {
    setSyncBusy(true);
    setSyncFeedback(null);
    const res = await mergeAndSync();
    setSyncBusy(false);
    setSyncFeedback(
      res.ok
        ? { ok: true, text: '已将本机与云端数据智能合并并同步至最新！' }
        : { ok: false, text: res.error || '同步失败' }
    );
  };

  const handlePushForce = async () => {
    setSyncBusy(true);
    setSyncFeedback(null);
    const res = await pushToCloud(true);
    setSyncBusy(false);
    setSyncFeedback(
      res.ok
        ? { ok: true, text: '已将本机当前全量学习记录与图鉴覆盖同步到云端！' }
        : { ok: false, text: res.error || '上传失败' }
    );
  };

  const handlePullCloud = async () => {
    setSyncBusy(true);
    setSyncFeedback(null);
    const res = await pullFromCloud();
    setSyncBusy(false);
    setSyncFeedback(
      res.ok
        ? { ok: true, text: '已从云端拉取存档并恢复到本机！' }
        : { ok: false, text: res.error || '拉取失败' }
    );
  };

  const handleSaveDisplayName = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = editDisplayName.trim();
    if (!trimmed) {
      setSecFeedback({ ok: false, text: '显示昵称不能为空' });
      return;
    }
    setSecBusy(true);
    setSecFeedback(null);
    const res = await updateProfile(trimmed);
    setSecBusy(false);
    setSecFeedback(
      res.ok
        ? { ok: true, text: '显示昵称已更新！' }
        : { ok: false, text: res.error || '更新失败' }
    );
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentPassword || newPassword.length < 6) {
      setSecFeedback({ ok: false, text: '请输入当前密码，且新密码不少于 6 位' });
      return;
    }
    setSecBusy(true);
    setSecFeedback(null);
    const res = await changePassword(currentPassword, newPassword);
    setSecBusy(false);
    if (res.ok) {
      setCurrentPassword('');
      setNewPassword('');
      setSecFeedback({ ok: true, text: '密码修改成功，其他设备的登录会话已自动失效。' });
    } else {
      setSecFeedback({ ok: false, text: res.error || '修改密码失败' });
    }
  };

  const handleLogoutOthers = async () => {
    setSecBusy(true);
    setSecFeedback(null);
    const res = await logoutOthers();
    setSecBusy(false);
    setSecFeedback(
      res.ok
        ? { ok: true, text: `已注销其他设备会话（共 ${res.revokedCount ?? 0} 个）。` }
        : { ok: false, text: res.error || '操作失败' }
    );
  };

  let syncBadgeLabel = '待同步';
  let syncBadgeClass = 'pending';
  if (syncStatus === 'syncing') {
    syncBadgeLabel = '同步中…';
    syncBadgeClass = 'pending';
  } else if (syncStatus === 'synced') {
    syncBadgeLabel = cloudMeta ? `已同步 v${cloudMeta.version}` : '已连接';
    syncBadgeClass = 'local';
  } else if (syncStatus === 'conflict') {
    syncBadgeLabel = '存在双端差异';
    syncBadgeClass = 'pending';
  } else if (syncStatus === 'offline') {
    syncBadgeLabel = '离线模式';
    syncBadgeClass = 'rejected';
  } else if (syncStatus === 'error') {
    syncBadgeLabel = '同步异常';
    syncBadgeClass = 'rejected';
  }

  return (
    <div className="modal-backdrop" onClick={closeAccountModal}>
      <div
        className="modal-panel account-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="account-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <div>
            <div className="page-kicker">CLOUD ACCOUNT // CROSS-DEVICE SYNC</div>
            <h3 id="account-modal-title" className="modal-title">
              云端账号与跨设备数据中心
            </h3>
            <p className="modal-sub">
              注册登录后可跨设备自动同步刷题进度、错题笔记、小鱼干图鉴与私密投递回复。
            </p>
          </div>
          <button
            type="button"
            className="icon-btn"
            onClick={closeAccountModal}
            aria-label="关闭账号窗口"
          >
            <X size={18} />
          </button>
        </div>

        {!user ? (
          <div className="acct-auth-wrap">
            {!backendOnline && (
              <div className="feedback-banner err">
                当前处于纯静态离线环境，暂无法连接云端账号接口；你仍可免登录使用全站刷题并通过「设置 → 导出全量备份」迁移数据。
              </div>
            )}

            <div className="gb-admin-tabs" role="tablist">
              <button
                type="button"
                role="tab"
                aria-selected={authMode === 'login'}
                className={`gb-filter-chip ${authMode === 'login' ? 'active' : ''}`}
                onClick={() => {
                  setAuthMode('login');
                  setAuthFeedback(null);
                }}
              >
                <LogIn size={13} /> 登录已有账号
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={authMode === 'register'}
                className={`gb-filter-chip ${authMode === 'register' ? 'active' : ''}`}
                onClick={() => {
                  setAuthMode('register');
                  setAuthFeedback(null);
                }}
              >
                <UserPlus size={13} /> 注册新账号
              </button>
            </div>

            <form className="acct-auth-form" onSubmit={handleAuthSubmit}>
              <div className="acct-field">
                <label className="acct-label" htmlFor="acct-username">
                  用户名（仅支持 3~20 位英文、数字、_ 或 -）
                </label>
                <input
                  id="acct-username"
                  type="text"
                  className="gb-input"
                  autoComplete="username"
                  maxLength={20}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="例如：hhu_water_2027"
                />
              </div>

              {authMode === 'register' && (
                <div className="acct-field">
                  <label className="acct-label" htmlFor="acct-display-name">
                    显示昵称（选填，用于顶栏与留言署名）
                  </label>
                  <input
                    id="acct-display-name"
                    type="text"
                    className="gb-input"
                    maxLength={20}
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder="留空则默认使用用户名"
                  />
                </div>
              )}

              <div className="acct-field">
                <label className="acct-label" htmlFor="acct-password">
                  密码（至少 6 位）
                </label>
                <input
                  id="acct-password"
                  type="password"
                  className="gb-input"
                  autoComplete={authMode === 'login' ? 'current-password' : 'new-password'}
                  maxLength={128}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="请输入密码"
                />
              </div>

              {authMode === 'register' && (
                <div className="acct-field">
                  <label className="acct-label" htmlFor="acct-password-confirm">
                    确认密码
                  </label>
                  <input
                    id="acct-password-confirm"
                    type="password"
                    className="gb-input"
                    autoComplete="new-password"
                    maxLength={128}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="请再次输入密码"
                  />
                </div>
              )}

              <button
                type="submit"
                className="btn btn-tactical btn-sm"
                disabled={authBusy || !backendOnline}
              >
                {authMode === 'login' ? <LogIn size={14} /> : <UserPlus size={14} />}
                <span>
                  {authBusy
                    ? '处理中…'
                    : authMode === 'login'
                      ? '登录并同步数据'
                      : '创建账号并绑定本机进度'}
                </span>
              </button>

              {authFeedback && (
                <div className={`feedback-banner ${authFeedback.ok ? 'ok' : 'err'}`}>
                  {authFeedback.text}
                </div>
              )}
            </form>

            <div className="acct-local-summary">
              <div className="acct-label">当前浏览器本地进度预览</div>
              <div className="acct-mini-stats">
                <span>已刷 {localSummary.attemptedCount} 题</span>
                <span>错题 {localSummary.wrongCount}</span>
                <span>笔记 {localSummary.noteCount}</span>
                <span>模考 {localSummary.mockCount} 次</span>
                <span>小鱼干 {localSummary.fish}</span>
              </div>
              <p className="gb-static-note">
                说明：登录后会自动认领当前浏览器的历史私密投递回执；若云端和本机都有做题记录，支持无损智能合并，不会误删任何笔记与图鉴。
              </p>
            </div>
          </div>
        ) : (
          <div className="acct-authed-body">
            <div className="acct-user-bar">
              <div className="acct-user-meta">
                <div className="acct-user-name-row">
                  <UserCheck size={16} className="text-sky" />
                  <strong>{user.displayName}</strong>
                  <span className="hud-code">@{user.username}</span>
                  <span className={`gb-role-badge ${syncBadgeClass}`}>{syncBadgeLabel}</span>
                </div>
                <span className="acct-user-sub">
                  最近同步：{cloudMeta?.updatedAt ? formatTime(cloudMeta.updatedAt) : '尚未上传云端存档'}
                </span>
              </div>
              <button type="button" className="btn btn-ghost-danger btn-sm" onClick={() => void logout()}>
                <LogOut size={13} /> 退出登录
              </button>
            </div>

            <div className="gb-admin-tabs" role="tablist">
              <button
                type="button"
                role="tab"
                aria-selected={modalTab === 'sync'}
                className={`gb-filter-chip ${modalTab === 'sync' ? 'active' : ''}`}
                onClick={() => setModalTab('sync')}
              >
                <Cloud size={13} /> 云端同步
                {syncConflict && <span className="nav-dot" />}
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={modalTab === 'inbox'}
                className={`gb-filter-chip ${modalTab === 'inbox' ? 'active' : ''}`}
                onClick={() => {
                  setModalTab('inbox');
                  void refreshAccountInbox();
                }}
              >
                <Lock size={13} /> 私密投递 ({accountInbox.length})
                {repliedAccountInboxCount > 0 && (
                  <span className="nav-fish-badge">{repliedAccountInboxCount}</span>
                )}
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={modalTab === 'security'}
                className={`gb-filter-chip ${modalTab === 'security' ? 'active' : ''}`}
                onClick={() => setModalTab('security')}
              >
                <KeyRound size={13} /> 账号与安全
              </button>
            </div>

            {modalTab === 'sync' && (
              <div className="acct-tab-panel">
                {syncConflict && (
                  <div className="acct-conflict-banner">
                    <div className="acct-conflict-head">
                      <AlertTriangle size={16} />
                      <strong>
                        {syncConflict.reason === 'initial'
                          ? '检测到本机与云端均有学习记录，请选择同步策略'
                          : '检测到另一台设备刚刚更新了云端存档，自动同步已暂停防覆盖'}
                      </strong>
                    </div>
                    <p className="acct-conflict-desc">
                      推荐使用「智能合并并同步」：按每道题最新作答合并、保留所有笔记/收藏/模考/已解锁角色与更高小鱼干，双端进度都不丢。
                    </p>
                    <div className="acct-sync-actions">
                      <button
                        type="button"
                        className="btn btn-tactical btn-sm"
                        disabled={syncBusy}
                        onClick={() => void handleMergeSync()}
                      >
                        <GitMerge size={14} /> 智能合并并同步（推荐）
                      </button>
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        disabled={syncBusy}
                        onClick={() => void handlePullCloud()}
                      >
                        <CloudDownload size={14} /> 用云端覆盖本机
                      </button>
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        disabled={syncBusy}
                        onClick={() => void handlePushForce()}
                      >
                        <CloudUpload size={14} /> 用本机覆盖云端
                      </button>
                    </div>
                  </div>
                )}

                <div className="acct-sync-grid">
                  <div className="acct-stat-card">
                    <div className="acct-stat-head">
                      <span>本机当前进度</span>
                      <span className="hud-code">LOCAL</span>
                    </div>
                    <ul className="acct-stat-list">
                      <li>已练习板块：{localSummary.courseCount} 个</li>
                      <li>已刷题目：{localSummary.attemptedCount} 题</li>
                      <li>错题 / 笔记：{localSummary.wrongCount} / {localSummary.noteCount}</li>
                      <li>模考记录：{localSummary.mockCount} 次</li>
                      <li>小鱼干 / 图鉴卡：{localSummary.fish} / {localSummary.ownedCardCount}</li>
                    </ul>
                  </div>

                  <div className="acct-stat-card">
                    <div className="acct-stat-head">
                      <span>云端档案状态</span>
                      <span className="hud-code">
                        {cloudMeta ? `V${cloudMeta.version}` : 'EMPTY'}
                      </span>
                    </div>
                    {cloudSummary ? (
                      <ul className="acct-stat-list">
                        <li>云端时间：{formatTime(syncConflict?.cloudUpdatedAt)}</li>
                        <li>已刷题目：{cloudSummary.attemptedCount} 题</li>
                        <li>错题 / 笔记：{cloudSummary.wrongCount} / {cloudSummary.noteCount}</li>
                        <li>模考记录：{cloudSummary.mockCount} 次</li>
                        <li>小鱼干 / 图鉴卡：{cloudSummary.fish} / {cloudSummary.ownedCardCount}</li>
                      </ul>
                    ) : (
                      <ul className="acct-stat-list">
                        <li>版本号：{cloudMeta ? `第 ${cloudMeta.version} 版` : '暂无云端存档'}</li>
                        <li>存档大小：{cloudMeta ? `${(cloudMeta.dataSize / 1024).toFixed(1)} KB` : '—'}</li>
                        <li>同步方式：变更后 2.5 秒自动上传</li>
                        <li>切回页面自动检查云端更新</li>
                      </ul>
                    )}
                  </div>
                </div>

                {!syncConflict && (
                  <div className="acct-sync-actions">
                    <button
                      type="button"
                      className="btn btn-tactical btn-sm"
                      disabled={syncBusy}
                      onClick={() => void handlePushForce()}
                    >
                      <CloudUpload size={14} /> {syncBusy ? '同步中…' : '立即上传本机到云端'}
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      disabled={syncBusy || !cloudMeta}
                      onClick={() => void handlePullCloud()}
                    >
                      <CloudDownload size={14} /> 从云端拉取覆盖本机
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      disabled={syncBusy || !cloudMeta}
                      onClick={() => void handleMergeSync()}
                    >
                      <GitMerge size={14} /> 智能合并双端进度
                    </button>
                  </div>
                )}

                {syncError && !syncFeedback && <div className="feedback-banner err">{syncError}</div>}
                {syncFeedback && (
                  <div className={`feedback-banner ${syncFeedback.ok ? 'ok' : 'err'}`}>
                    {syncFeedback.text}
                  </div>
                )}
              </div>
            )}

            {modalTab === 'inbox' && (
              <div className="acct-tab-panel">
                <div className="acct-inbox-toolbar">
                  <span className="gb-private-tip">
                    绑定到此账号的所有私密投递与站长回复，支持在任何已登录设备实时查看。
                  </span>
                  <div className="acct-inbox-btns">
                    <button
                      type="button"
                      className="gb-admin-trigger"
                      disabled={inboxLoading}
                      onClick={() => void refreshAccountInbox()}
                    >
                      <RefreshCw size={12} /> {inboxLoading ? '同步中…' : '刷新'}
                    </button>
                    <Link
                      to="/board"
                      className="gb-action-link"
                      onClick={closeAccountModal}
                    >
                      前往留言板提交 <ArrowRight size={12} />
                    </Link>
                  </div>
                </div>

                <div className="gb-private-list acct-inbox-list">
                  {inboxLoading && accountInbox.length === 0 ? (
                    <div className="empty-mini">正在同步账号私密投递…</div>
                  ) : accountInbox.length === 0 ? (
                    <div className="empty-mini">
                      暂无绑定到此账号的私密投递。在留言板选择「私密投递给站长」后会自动出现在这里。
                    </div>
                  ) : (
                    accountInbox.map((item) => {
                      let statusClass = 'pending';
                      let statusLabel = '待站长查收';
                      if (item.adminReply) {
                        statusClass = 'replied';
                        statusLabel = '站长已回复';
                      } else if (item.channel === 'public' && item.status === 'approved') {
                        statusClass = 'local';
                        statusLabel = '已转为公开上墙';
                      } else if (item.status === 'approved') {
                        statusClass = 'admin';
                        statusLabel = '站长已阅';
                      }

                      return (
                        <article
                          key={item.id}
                          className={`gb-inbox-card ${item.adminReply ? 'replied' : ''}`}
                        >
                          <div className="gb-inbox-head">
                            <div className="gb-author-row">
                              <strong className="gb-author-name">{item.author}</strong>
                              <span className="gb-role-badge inbox">私密投递</span>
                              <span className={`gb-role-badge ${statusClass}`}>{statusLabel}</span>
                            </div>
                            <div className="gb-sub-meta">
                              <span>{GUESTBOOK_CATEGORY_LABELS[item.category] ?? item.category}</span>
                              <span>·</span>
                              <span>{courseLabelMap[item.courseId] ?? item.courseId}</span>
                              <span>·</span>
                              <time className="font-mono">{formatTime(item.createdAt)}</time>
                            </div>
                          </div>
                          <p className="gb-card-body">{item.content}</p>
                          {item.adminReply && (
                            <div className="gb-admin-reply-box">
                              <div className="gb-admin-reply-head">
                                <span>站长私密回复</span>
                                {item.adminRepliedAt && (
                                  <time className="font-mono">{formatTime(item.adminRepliedAt)}</time>
                                )}
                              </div>
                              <p className="gb-admin-reply-text">{item.adminReply}</p>
                            </div>
                          )}
                        </article>
                      );
                    })
                  )}
                </div>
              </div>
            )}

            {modalTab === 'security' && (
              <div className="acct-tab-panel">
                <form className="acct-settings-card" onSubmit={handleSaveDisplayName}>
                  <div className="setting-label">修改显示昵称</div>
                  <div className="acct-inline-row">
                    <input
                      type="text"
                      className="gb-input"
                      maxLength={20}
                      value={editDisplayName}
                      onChange={(e) => setEditDisplayName(e.target.value)}
                      placeholder="输入新的显示昵称"
                    />
                    <button type="submit" className="btn btn-tactical btn-sm" disabled={secBusy}>
                      <Check size={13} /> 保存昵称
                    </button>
                  </div>
                </form>

                <form className="acct-settings-card" onSubmit={handleChangePassword}>
                  <div className="setting-label">修改登录密码</div>
                  <input
                    type="password"
                    className="gb-input"
                    autoComplete="current-password"
                    maxLength={128}
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    placeholder="当前密码"
                  />
                  <input
                    type="password"
                    className="gb-input"
                    autoComplete="new-password"
                    maxLength={128}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="新密码（至少 6 位）"
                  />
                  <div>
                    <button type="submit" className="btn btn-secondary btn-sm" disabled={secBusy}>
                      <KeyRound size={13} /> 更新密码并下线其他设备
                    </button>
                  </div>
                </form>

                <div className="acct-settings-card">
                  <div className="setting-label">会话安全管理</div>
                  <div className="setting-desc">
                    如果你在公共电脑或借用设备上登录过，可一键注销除当前设备外的所有其他会话。
                  </div>
                  <div>
                    <button
                      type="button"
                      className="btn btn-ghost-danger btn-sm"
                      disabled={secBusy}
                      onClick={() => void handleLogoutOthers()}
                    >
                      <ShieldCheck size={13} /> 注销其他设备登录
                    </button>
                  </div>
                </div>

                {secFeedback && (
                  <div className={`feedback-banner ${secFeedback.ok ? 'ok' : 'err'}`}>
                    {secFeedback.text}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
