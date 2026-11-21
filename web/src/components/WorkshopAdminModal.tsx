import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Check,
  ExternalLink,
  Eye,
  EyeOff,
  KeyRound,
  Link2,
  LogOut,
  Pin,
  PinOff,
  RefreshCw,
  ShieldCheck,
  Trash2,
  Upload,
  X,
} from 'lucide-react';
import type { CharacterUnlockMode, WorkshopCatalogItem, WorkshopPackType } from '../types';
import { loadSavedAdminToken, saveAdminToken } from '../utils/guestbook';
import {
  MAX_D1_PACK_BYTES,
  deleteAdminWorkshopPack,
  fetchAdminWorkshopPacks,
  formatPackSize,
  parseAndValidateWorkshopZip,
  patchAdminWorkshopPack,
  registerExternalWorkshopPack,
  uploadAdminWorkshopPack,
  type ParsedWorkshopZip,
} from '../utils/workshopPack';

interface WorkshopAdminModalProps {
  open: boolean;
  onClose: () => void;
  onCatalogChanged: () => void;
}

const PACK_TYPE_LABELS: Record<WorkshopPackType, string> = {
  course: '整科专业课',
  exam: '单年试卷包',
  character: '角色包',
};

export const WorkshopAdminModal: React.FC<WorkshopAdminModalProps> = ({
  open,
  onClose,
  onCatalogChanged,
}) => {
  const [activeToken, setActiveToken] = useState<string>(loadSavedAdminToken);
  const [tokenInput, setTokenInput] = useState('');
  const [authed, setAuthed] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  const [packs, setPacks] = useState<WorkshopCatalogItem[]>([]);
  const [listLoading, setListLoading] = useState(false);
  const [feedback, setFeedback] = useState<{ ok: boolean; text: string } | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const [uploadMode, setUploadMode] = useState<'d1' | 'url'>('d1');
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<{ name: string; bytes: Uint8Array } | null>(null);
  const [parsedPreview, setParsedPreview] = useState<ParsedWorkshopZip | null>(null);
  const [parseErrors, setParseErrors] = useState<string[]>([]);
  const [d1Featured, setD1Featured] = useState(false);
  const [d1UnlockMode, setD1UnlockMode] = useState<CharacterUnlockMode>('direct');
  const [d1Description, setD1Description] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<{ pct: number; label: string } | null>(null);

  // External URL registration fields
  const [extPackId, setExtPackId] = useState('');
  const [extType, setExtType] = useState<WorkshopPackType>('course');
  const [extName, setExtName] = useState('');
  const [extVersion, setExtVersion] = useState('1.0.0');
  const [extAuthor, setExtAuthor] = useState('');
  const [extLicense, setExtLicense] = useState('非商业学习共享');
  const [extSummary, setExtSummary] = useState('');
  const [extUrl, setExtUrl] = useState('');
  const [extTargetCourse, setExtTargetCourse] = useState('');
  const [extUnlockMode, setExtUnlockMode] = useState<CharacterUnlockMode>('direct');
  const [extSizeMb, setExtSizeMb] = useState('');
  const [extFeatured, setExtFeatured] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open, onClose]);

  const handleUnauthorized = useCallback((msg: string) => {
    saveAdminToken('');
    setActiveToken('');
    setAuthed(false);
    setPacks([]);
    setAuthError(msg);
  }, []);

  const loadPacks = useCallback(
    async (token: string) => {
      setListLoading(true);
      const res = await fetchAdminWorkshopPacks(token);
      setListLoading(false);
      if (!res.ok) {
        if (res.status === 401) {
          handleUnauthorized('管理口令已失效，请重新输入。');
        } else {
          setFeedback({ ok: false, text: res.error });
        }
        return false;
      }
      setAuthed(true);
      setAuthError(null);
      setPacks(res.packs);
      return true;
    },
    [handleUnauthorized]
  );

  useEffect(() => {
    if (!open) return;
    const saved = loadSavedAdminToken();
    if (saved && saved !== activeToken) {
      setActiveToken(saved);
    }
    if (saved || activeToken) {
      void loadPacks(saved || activeToken);
    }
  }, [open, activeToken, loadPacks]);

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
    const res = await fetchAdminWorkshopPacks(trimmed);
    setAuthLoading(false);
    if (!res.ok) {
      setAuthError(res.status === 401 ? '管理口令不正确，请核对后重试。' : res.error);
      return;
    }
    saveAdminToken(trimmed);
    setActiveToken(trimmed);
    setTokenInput('');
    setAuthed(true);
    setPacks(res.packs);
  };

  const handleLogout = () => {
    saveAdminToken('');
    setActiveToken('');
    setAuthed(false);
    setPacks([]);
    setFeedback(null);
    setAuthError(null);
  };

  const handlePickZip = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;

    setFeedback(null);
    setParseErrors([]);
    setParsedPreview(null);
    setSelectedFile(null);

    const buf = new Uint8Array(await file.arrayBuffer());
    const res = await parseAndValidateWorkshopZip(buf);
    if (!res.ok) {
      setParseErrors(res.errors);
      return;
    }
    setSelectedFile({ name: file.name, bytes: buf });
    setParsedPreview(res.parsed);
    setD1UnlockMode(res.parsed.unlockMode);
    setD1Description(res.parsed.manifest.description ?? '');
  };

  const handleUploadD1 = async () => {
    if (!activeToken || !selectedFile || !parsedPreview || uploading) return;
    setUploading(true);
    setFeedback(null);
    setUploadProgress({ pct: 0, label: '准备上传…' });

    const res = await uploadAdminWorkshopPack(
      activeToken,
      selectedFile.bytes,
      selectedFile.name,
      parsedPreview,
      {
        featured: d1Featured,
        unlockMode: d1UnlockMode,
        description: d1Description,
      },
      (pct, label) => setUploadProgress({ pct, label })
    );

    setUploading(false);
    if (!res.ok) {
      if (res.status === 401) {
        handleUnauthorized('登录状态已过期，请重新输入口令。');
      } else {
        setFeedback({ ok: false, text: res.error });
      }
      return;
    }

    setSelectedFile(null);
    setParsedPreview(null);
    setD1Description('');
    setD1Featured(false);
    setUploadProgress(null);
    await loadPacks(activeToken);
    onCatalogChanged();
    setFeedback({ ok: true, text: `已成功上架资源包「${res.pack.name}」！` });
  };

  const handleRegisterUrl = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeToken || uploading) return;
    setUploading(true);
    setFeedback(null);

    const parsedSize = Number(extSizeMb);
    const sizeBytes = Number.isFinite(parsedSize) && parsedSize > 0
      ? Math.round(parsedSize * 1024 * 1024)
      : 0;

    const res = await registerExternalWorkshopPack(activeToken, {
      packId: extPackId.trim().toLowerCase(),
      type: extType,
      name: extName.trim(),
      version: extVersion.trim(),
      author: extAuthor.trim() || '站长推荐',
      summary: extSummary.trim(),
      license: extLicense.trim() || '非商业学习共享',
      targetCourseId: extType === 'exam' ? extTargetCourse.trim() : '',
      unlockMode: extType === 'character' ? extUnlockMode : 'direct',
      externalUrl: extUrl.trim(),
      sizeBytes,
      featured: extFeatured,
    });

    setUploading(false);
    if (!res.ok) {
      if (res.status === 401) {
        handleUnauthorized('登录状态已过期，请重新输入口令。');
      } else {
        setFeedback({ ok: false, text: res.error });
      }
      return;
    }

    setExtPackId('');
    setExtName('');
    setExtSummary('');
    setExtUrl('');
    setExtTargetCourse('');
    setExtSizeMb('');
    setExtFeatured(false);
    await loadPacks(activeToken);
    onCatalogChanged();
    setFeedback({ ok: true, text: `外链资源「${res.pack.name}」已上架！` });
  };

  const handlePatch = async (
    packId: string,
    patch: { featured?: boolean; published?: boolean },
    okMsg: string
  ) => {
    if (!activeToken) return;
    setBusyId(packId);
    const res = await patchAdminWorkshopPack(activeToken, packId, patch);
    setBusyId(null);
    if (!res.ok) {
      if (res.status === 401) {
        handleUnauthorized('登录已过期，请重新验证。');
      } else {
        setFeedback({ ok: false, text: res.error });
      }
      return;
    }
    await loadPacks(activeToken);
    onCatalogChanged();
    setFeedback({ ok: true, text: okMsg });
  };

  const handleDelete = async (packId: string) => {
    if (!activeToken) return;
    setBusyId(packId);
    const res = await deleteAdminWorkshopPack(activeToken, packId);
    setBusyId(null);
    setConfirmDeleteId(null);
    if (!res.ok) {
      if (res.status === 401) {
        handleUnauthorized('登录已过期，请重新验证。');
      } else {
        setFeedback({ ok: false, text: res.error });
      }
      return;
    }
    await loadPacks(activeToken);
    onCatalogChanged();
    setFeedback({ ok: true, text: `已删除资源包 ${packId}。` });
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-panel gb-admin-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ws-admin-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <div>
            <div className="page-kicker">WORKSHOP CONSOLE // D1 CHUNKED UPLOAD</div>
            <h3 id="ws-admin-modal-title" className="modal-title">
              站长工坊资源上架与管理
            </h3>
            <p className="modal-sub">
              支持直接分片上传 ≤ 15 MB 的 .jypack.zip 到 D1，或登记外部直链 URL。
            </p>
          </div>
          <button
            type="button"
            className="icon-btn"
            onClick={onClose}
            aria-label="关闭工坊管理后台"
          >
            <X size={18} />
          </button>
        </div>

        {!authed ? (
          <form className="gb-admin-login" onSubmit={handleLogin}>
            <div className="gb-admin-login-hint">
              <KeyRound size={16} className="text-yellow" />
              <span>
                请输入站长管理口令（与留言板共用 Cloudflare Worker Secret <code>ADMIN_TOKEN</code>）：
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
                <ShieldCheck size={14} /> {authLoading ? '验证中…' : '进入上架后台'}
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
                  onClick={() => void loadPacks(activeToken)}
                  disabled={listLoading}
                >
                  <RefreshCw size={13} /> {listLoading ? '刷新中…' : '刷新列表'}
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

            <div className="seg-group" role="tablist">
              <button
                type="button"
                className={`seg-btn ${uploadMode === 'd1' ? 'active' : ''}`}
                onClick={() => setUploadMode('d1')}
              >
                <Upload size={13} /> 上传 .jypack.zip 到 D1（≤15MB）
              </button>
              <button
                type="button"
                className={`seg-btn ${uploadMode === 'url' ? 'active' : ''}`}
                onClick={() => setUploadMode('url')}
              >
                <Link2 size={13} /> 外链 URL 登记（超大包）
              </button>
            </div>

            {uploadMode === 'd1' ? (
              <div className="ws-admin-uploader">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".zip,.jypack.zip"
                  style={{ display: 'none' }}
                  onChange={(e) => void handlePickZip(e)}
                />
                <div className="ws-admin-pick-row">
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    disabled={uploading}
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Upload size={14} /> 选择本地 .jypack.zip
                  </button>
                  {selectedFile && (
                    <span className="ws-admin-file-meta">
                      {selectedFile.name} · {formatPackSize(selectedFile.bytes.byteLength)}
                    </span>
                  )}
                </div>

                {parseErrors.length > 0 && (
                  <div className="feedback-banner err">
                    <strong>资源包校验未通过：</strong>
                    <ul className="ws-error-list">
                      {parseErrors.map((err, i) => (
                        <li key={i}>{err}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {parsedPreview && (
                  <div className="ws-admin-preview-card">
                    <div className="ws-preview-top">
                      {parsedPreview.coverDataUrl && (
                        <img
                          src={parsedPreview.coverDataUrl}
                          alt={parsedPreview.manifest.name}
                          className="ws-preview-cover"
                        />
                      )}
                      <div>
                        <div className="gb-author-row">
                          <strong>{parsedPreview.manifest.name}</strong>
                          <span className="gb-role-badge admin">
                            {PACK_TYPE_LABELS[parsedPreview.manifest.type]}
                          </span>
                          <span className="gb-role-badge local">
                            v{parsedPreview.manifest.version}
                          </span>
                        </div>
                        <div className="gb-sub-meta">
                          <span>ID: {parsedPreview.manifest.packId}</span>
                          <span>·</span>
                          <span>作者：{parsedPreview.manifest.author}</span>
                          <span>·</span>
                          <span>许可：{parsedPreview.manifest.license}</span>
                        </div>
                        <p className="ws-preview-summary">{parsedPreview.manifest.summary}</p>
                      </div>
                    </div>

                    {parsedPreview.sizeBytes > MAX_D1_PACK_BYTES ? (
                      <div className="feedback-banner err">
                        当前包体积 {formatPackSize(parsedPreview.sizeBytes)} 超过 D1 15MB 上限，请改用「外链 URL 登记」。
                      </div>
                    ) : (
                      <>
                        {parsedPreview.manifest.type === 'character' && (
                          <div className="ws-admin-field-row">
                            <label className="gb-mail-label">角色包解锁模式：</label>
                            <select
                              className="ui-select"
                              value={d1UnlockMode}
                              onChange={(e) => setD1UnlockMode(e.target.value as CharacterUnlockMode)}
                            >
                              <option value="direct">即装即用（安装后立即可当看板娘）</option>
                              <option value="gacha">加入小鱼干卡池（需刷题攒鱼干抽取）</option>
                            </select>
                          </div>
                        )}
                        <textarea
                          className="gb-textarea"
                          rows={2}
                          maxLength={2000}
                          value={d1Description}
                          onChange={(e) => setD1Description(e.target.value)}
                          placeholder="补充详细介绍或安装后亮点说明（选填）…"
                        />
                        <div className="gb-admin-compose-foot">
                          <label className="gb-admin-pin-check">
                            <input
                              type="checkbox"
                              checked={d1Featured}
                              onChange={(e) => setD1Featured(e.target.checked)}
                            />
                            <span>置顶推荐</span>
                          </label>
                          <button
                            type="button"
                            className="btn btn-tactical btn-sm"
                            disabled={uploading}
                            onClick={() => void handleUploadD1()}
                          >
                            <Check size={14} /> {uploading ? '正在分片上传…' : '确认上架到工坊'}
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                )}

                {uploadProgress && (
                  <div className="ws-progress-wrap">
                    <div className="ws-progress-head">
                      <span>{uploadProgress.label}</span>
                      <span className="font-mono">{uploadProgress.pct}%</span>
                    </div>
                    <div className="progress-bar-track">
                      <div
                        className="progress-seg mastered"
                        style={{ width: `${uploadProgress.pct}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <form className="gb-admin-compose" onSubmit={handleRegisterUrl}>
                <div className="gb-admin-compose-row">
                  <input
                    type="text"
                    className="gb-input"
                    required
                    value={extPackId}
                    onChange={(e) => setExtPackId(e.target.value)}
                    placeholder="packId（如 seu-925-pack）"
                  />
                  <select
                    className="ui-select"
                    value={extType}
                    onChange={(e) => setExtType(e.target.value as WorkshopPackType)}
                  >
                    <option value="course">整科专业课 (course)</option>
                    <option value="exam">单年试卷包 (exam)</option>
                    <option value="character">角色包 (character)</option>
                  </select>
                  <input
                    type="text"
                    className="gb-input"
                    required
                    value={extVersion}
                    onChange={(e) => setExtVersion(e.target.value)}
                    placeholder="版本号（如 1.0.0）"
                  />
                </div>
                <div className="gb-input-row">
                  <input
                    type="text"
                    className="gb-input"
                    required
                    value={extName}
                    onChange={(e) => setExtName(e.target.value)}
                    placeholder="资源包展示名称"
                  />
                  <input
                    type="text"
                    className="gb-input"
                    value={extAuthor}
                    onChange={(e) => setExtAuthor(e.target.value)}
                    placeholder="作者 / 整理者"
                  />
                </div>
                <input
                  type="url"
                  className="gb-input"
                  required
                  value={extUrl}
                  onChange={(e) => setExtUrl(e.target.value)}
                  placeholder="https://...（必须为 HTTPS 直链）"
                />
                <input
                  type="text"
                  className="gb-input"
                  required
                  value={extSummary}
                  onChange={(e) => setExtSummary(e.target.value)}
                  placeholder="一句话简介"
                />
                <div className="gb-admin-compose-row">
                  <input
                    type="text"
                    className="gb-input"
                    value={extLicense}
                    onChange={(e) => setExtLicense(e.target.value)}
                    placeholder="许可协议（如 CC BY-NC-SA 4.0）"
                  />
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    className="gb-input"
                    value={extSizeMb}
                    onChange={(e) => setExtSizeMb(e.target.value)}
                    placeholder="体积 MB（选填）"
                  />
                  {extType === 'exam' ? (
                    <input
                      type="text"
                      className="gb-input"
                      value={extTargetCourse}
                      onChange={(e) => setExtTargetCourse(e.target.value)}
                      placeholder="目标科目 ID（如 hhu-814）"
                    />
                  ) : extType === 'character' ? (
                    <select
                      className="ui-select"
                      value={extUnlockMode}
                      onChange={(e) => setExtUnlockMode(e.target.value as CharacterUnlockMode)}
                    >
                      <option value="direct">即装即用</option>
                      <option value="gacha">加入卡池</option>
                    </select>
                  ) : (
                    <div />
                  )}
                </div>
                <div className="gb-admin-compose-foot">
                  <label className="gb-admin-pin-check">
                    <input
                      type="checkbox"
                      checked={extFeatured}
                      onChange={(e) => setExtFeatured(e.target.checked)}
                    />
                    <span>置顶推荐</span>
                  </label>
                  <button type="submit" className="btn btn-tactical btn-sm" disabled={uploading}>
                    <ExternalLink size={14} /> {uploading ? '提交中…' : '登记外链上架'}
                  </button>
                </div>
              </form>
            )}

            {feedback && (
              <div className={`feedback-banner ${feedback.ok ? 'ok' : 'err'}`}>
                {feedback.text}
              </div>
            )}

            <div className="gb-admin-list">
              {listLoading && packs.length === 0 ? (
                <div className="empty-mini">正在加载工坊已上架资源…</div>
              ) : packs.length === 0 ? (
                <div className="empty-mini">工坊后台暂无资源，上传第一个资源包试试吧～</div>
              ) : (
                packs.map((pack) => {
                  const isBusy = busyId === pack.packId;
                  return (
                    <article key={pack.packId} className="gb-admin-card">
                      <div className="gb-admin-card-head">
                        <div className="gb-author-row">
                          <strong>{pack.name}</strong>
                          <span className="gb-role-badge admin">
                            {PACK_TYPE_LABELS[pack.type]}
                          </span>
                          <span className="gb-role-badge local">
                            {pack.storageMode === 'd1' ? 'D1 直传' : '外链 URL'}
                          </span>
                          <span className={`gb-role-badge ${pack.published ? 'admin' : 'pending'}`}>
                            {pack.published ? '已上架' : '未上架'}
                          </span>
                          {pack.featured && (
                            <span className="gb-role-badge pin">
                              <Pin size={10} /> 置顶
                            </span>
                          )}
                        </div>
                        <div className="gb-sub-meta">
                          <span className="font-mono">{pack.packId}</span>
                          <span>·</span>
                          <span>v{pack.version}</span>
                          <span>·</span>
                          <span>{formatPackSize(pack.sizeBytes)}</span>
                          <span>·</span>
                          <span>{pack.downloads} 次下载</span>
                        </div>
                      </div>
                      <p className="gb-card-body">{pack.summary}</p>
                      <div className="gb-admin-actions">
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          disabled={isBusy}
                          onClick={() =>
                            void handlePatch(
                              pack.packId,
                              { featured: !pack.featured },
                              pack.featured ? '已取消置顶推荐。' : '已设为置顶推荐！'
                            )
                          }
                        >
                          {pack.featured ? <PinOff size={13} /> : <Pin size={13} />}
                          <span>{pack.featured ? '取消置顶' : '置顶推荐'}</span>
                        </button>
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          disabled={isBusy}
                          onClick={() =>
                            void handlePatch(
                              pack.packId,
                              { published: !pack.published },
                              pack.published ? '已下架该资源包。' : '已重新上架！'
                            )
                          }
                        >
                          {pack.published ? <EyeOff size={13} /> : <Eye size={13} />}
                          <span>{pack.published ? '下架' : '上架'}</span>
                        </button>
                        {confirmDeleteId === pack.packId ? (
                          <button
                            type="button"
                            className="btn btn-danger btn-sm"
                            disabled={isBusy}
                            onClick={() => void handleDelete(pack.packId)}
                          >
                            <Trash2 size={13} /> 确认永久删除
                          </button>
                        ) : (
                          <button
                            type="button"
                            className="btn btn-ghost-danger btn-sm"
                            disabled={isBusy}
                            onClick={() => setConfirmDeleteId(pack.packId)}
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
