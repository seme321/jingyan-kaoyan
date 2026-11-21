import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Download,
  FileCode2,
  FilePlus2,
  FolderUp,
  HelpCircle,
  Package,
  Pin,
  Power,
  PowerOff,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Trash2,
} from 'lucide-react';
import { BRAND } from '../brand';
import { WorkshopAdminModal } from '../components/WorkshopAdminModal';
import { useData } from '../context/DataContext';
import { useWorkshop } from '../context/WorkshopContext';
import type { InstalledWorkshopPack, WorkshopCatalogItem, WorkshopPackType } from '../types';
import {
  downloadWorkshopPackBytes,
  fetchWorkshopCatalog,
  formatPackSize,
} from '../utils/workshopPack';

type WorkshopTab = 'all' | 'course_all' | 'character' | 'installed';

interface WorkshopBanner {
  kind: 'ok' | 'err';
  text: string;
  actionLabel?: string;
  onAction?: () => void;
}

const PACK_TYPE_META: Record<
  WorkshopPackType,
  { label: string; badgeClass: string; Icon: React.FC<{ size?: number }> }
> = {
  course: { label: '整科专业课', badgeClass: 'course', Icon: BookOpen },
  exam: { label: '真题补充包', badgeClass: 'exam', Icon: FilePlus2 },
  character: { label: '角色干员包', badgeClass: 'character', Icon: Sparkles },
};

function getDownloadHref(pack: WorkshopCatalogItem, online: boolean): string {
  if (!online && pack.storageMode === 'url' && pack.externalUrl) {
    return pack.externalUrl;
  }
  return `${BRAND.workshopApiUrl}/packs/${encodeURIComponent(pack.packId)}/download`;
}

export const WorkshopPage: React.FC = () => {
  const navigate = useNavigate();
  const { setCourseId } = useData();
  const {
    ready: workshopReady,
    installedPacks,
    installedMap,
    installPackFromBytes,
    togglePackEnabled,
    uninstallPack,
    resolvePackBlobUrl,
  } = useWorkshop();

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [activeTab, setActiveTab] = useState<WorkshopTab>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [catalogPacks, setCatalogPacks] = useState<WorkshopCatalogItem[]>([]);
  const [catalogOnline, setCatalogOnline] = useState(true);
  const [catalogLoading, setCatalogLoading] = useState(true);

  const [showGuide, setShowGuide] = useState(false);
  const [adminOpen, setAdminOpen] = useState(false);

  const [importingLocal, setImportingLocal] = useState(false);
  const [importErrors, setImportErrors] = useState<string[]>([]);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [downloadProgress, setDownloadProgress] = useState<{
    received: number;
    total: number;
  } | null>(null);
  const [confirmUninstallId, setConfirmUninstallId] = useState<string | null>(null);
  const [banner, setBanner] = useState<WorkshopBanner | null>(null);

  const loadCatalog = useCallback(async () => {
    setCatalogLoading(true);
    try {
      const res = await fetchWorkshopCatalog();
      setCatalogPacks(res.packs);
      setCatalogOnline(res.online);
    } finally {
      setCatalogLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadCatalog();
  }, [loadCatalog]);

  const navigateToInstalledPack = useCallback(
    (pack: InstalledWorkshopPack) => {
      if (pack.manifest.type === 'course') {
        const cid = pack.coursePayload?.course?.id;
        if (cid) setCourseId(cid);
        navigate('/year');
        return;
      }
      if (pack.manifest.type === 'exam') {
        const cid = pack.coursePayload?.targetCourseId || pack.manifest.targetCourseId;
        if (cid) setCourseId(cid);
        navigate('/year');
        return;
      }
      const mode =
        pack.characterPayload?.unlockMode ?? pack.manifest.unlockMode ?? 'direct';
      navigate(mode === 'gacha' ? '/companion?tab=gacha' : '/companion?tab=stage');
    },
    [navigate, setCourseId]
  );

  const getPackActionLabel = (pack: InstalledWorkshopPack): string => {
    if (pack.manifest.type === 'course') return '前往该科目刷题 →';
    if (pack.manifest.type === 'exam') return '前往查看新增真题 →';
    return (pack.characterPayload?.unlockMode ?? pack.manifest.unlockMode) === 'gacha'
      ? '前往卡池抽取 →'
      : '前往补给站查看 →';
  };

  const handleLocalImportFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;

    setImportingLocal(true);
    setImportErrors([]);
    setBanner(null);

    try {
      const bytes = new Uint8Array(await file.arrayBuffer());
      const res = await installPackFromBytes(bytes, 'local');
      if (!res.ok) {
        setImportErrors(res.errors);
        setBanner({
          kind: 'err',
          text: `本地包「${file.name}」校验未通过，请查看下方错误列表。`,
        });
        return;
      }

      const installed = res.pack;
      setBanner({
        kind: 'ok',
        text: `已成功导入「${installed.manifest.name}」（v${installed.manifest.version}），已写入本地离线仓库并启用。`,
        actionLabel: getPackActionLabel(installed),
        onAction: () => navigateToInstalledPack(installed),
      });
    } catch (err) {
      setBanner({
        kind: 'err',
        text: `读取本地文件失败：${err instanceof Error ? err.message : '未知错误'}`,
      });
    } finally {
      setImportingLocal(false);
    }
  };

  const handleInstallCatalogPack = async (pack: WorkshopCatalogItem) => {
    setDownloadingId(pack.packId);
    setDownloadProgress({ received: 0, total: pack.sizeBytes });
    setImportErrors([]);
    setBanner(null);

    try {
      const dl = await downloadWorkshopPackBytes(pack, (received, total) => {
        setDownloadProgress({ received, total });
      });
      if (!dl.ok) {
        setBanner({ kind: 'err', text: dl.error });
        return;
      }

      const res = await installPackFromBytes(dl.bytes, 'workshop');
      if (!res.ok) {
        setImportErrors(res.errors);
        setBanner({
          kind: 'err',
          text: `资源包「${pack.name}」安装校验失败：${res.errors[0] || '格式异常'}`,
        });
        return;
      }

      const installed = res.pack;
      setBanner({
        kind: 'ok',
        text: `已安装并启用「${installed.manifest.name}」（v${installed.manifest.version}）。`,
        actionLabel: getPackActionLabel(installed),
        onAction: () => navigateToInstalledPack(installed),
      });
      void loadCatalog();
    } finally {
      setDownloadingId(null);
      setDownloadProgress(null);
    }
  };

  const handleToggleEnabled = async (pack: InstalledWorkshopPack) => {
    const nextEnabled = !pack.enabled;
    await togglePackEnabled(pack.packId, nextEnabled);
    setBanner({
      kind: 'ok',
      text: nextEnabled
        ? `已重新启用「${pack.manifest.name}」。`
        : `已暂停「${pack.manifest.name}」（保留包数据，随时可重新启用）。`,
    });
  };

  const handleUninstall = async (pack: InstalledWorkshopPack) => {
    await uninstallPack(pack.packId);
    setConfirmUninstallId(null);
    setBanner({
      kind: 'ok',
      text: `已卸载「${pack.manifest.name}」并清理本地缓存。`,
    });
  };

  const normalizedQuery = searchQuery.trim().toLowerCase();

  const filteredCatalog = useMemo(() => {
    return catalogPacks.filter((pack) => {
      if (activeTab === 'course_all' && pack.type !== 'course' && pack.type !== 'exam') {
        return false;
      }
      if (activeTab === 'character' && pack.type !== 'character') {
        return false;
      }
      if (!normalizedQuery) return true;
      const haystack = [
        pack.packId,
        pack.name,
        pack.author,
        pack.summary,
        pack.targetCourseId,
        ...pack.tags,
      ]
        .join(' ')
        .toLowerCase();
      return haystack.includes(normalizedQuery);
    });
  }, [catalogPacks, activeTab, normalizedQuery]);

  const filteredInstalled = useMemo(() => {
    return installedPacks.filter((pack) => {
      if (!normalizedQuery) return true;
      const haystack = [
        pack.packId,
        pack.manifest.name,
        pack.manifest.author,
        pack.manifest.summary,
        pack.manifest.targetCourseId ?? '',
        ...(pack.manifest.tags ?? []),
      ]
        .join(' ')
        .toLowerCase();
      return haystack.includes(normalizedQuery);
    });
  }, [installedPacks, normalizedQuery]);

  const statsChips = (
    packType: WorkshopPackType,
    stats: WorkshopCatalogItem['stats'],
    sizeBytes: number,
    downloads?: number
  ) => {
    const items: string[] = [];
    if (packType === 'character') {
      if (stats.spCardCount) items.push(`${stats.spCardCount} 张 SP 看板娘`);
      if (stats.characterCount) items.push(`${stats.characterCount} 位三阶干员`);
    } else {
      if (stats.paperCount) items.push(`${stats.paperCount} 套真题`);
      if (stats.questionCount) items.push(`${stats.questionCount} 道题目`);
      if (stats.figureCount) items.push(`${stats.figureCount} 张配图`);
    }
    if (sizeBytes > 0) items.push(formatPackSize(sizeBytes));
    if (typeof downloads === 'number' && downloads > 0) {
      items.push(`${downloads} 次下载`);
    }
    return items;
  };

  return (
    <div className="page-container">
      <section className="page-hero ws-hero">
        <div className="hero-accent-line" />
        <div className="ws-hero-main">
          <div>
            <span className="hero-tag">WORKSHOP // COMMUNITY MODULES</span>
            <h1 className="page-title">
              <Package size={24} className="inline-icon" /> 创意工坊 · 专业课与角色扩展中心
            </h1>
            <p className="hero-desc">
              在这里浏览、下载并一键安装<strong>新增高校专业课试卷包</strong>、
              <strong>历年真题补充包</strong>与<strong>自定义看板娘角色包</strong>；也可直接导入本地制作好的{' '}
              <code>.jypack.zip</code>，所有已安装模块均持久保存在你的浏览器本地，离线可用、随时启停。
            </p>
          </div>
          <div className="ws-hero-actions">
            <input
              ref={fileInputRef}
              type="file"
              accept=".zip,.jypack.zip"
              style={{ display: 'none' }}
              onChange={(e) => void handleLocalImportFile(e)}
            />
            <button
              type="button"
              className="btn btn-tactical btn-sm"
              disabled={importingLocal}
              onClick={() => fileInputRef.current?.click()}
            >
              <FolderUp size={15} />
              <span>{importingLocal ? '正在解析导入…' : '从本地导入 .jypack.zip'}</span>
            </button>
            <button
              type="button"
              className={`btn btn-secondary btn-sm ${showGuide ? 'active' : ''}`}
              onClick={() => setShowGuide((v) => !v)}
            >
              <HelpCircle size={15} />
              <span>打包与制作规范</span>
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => setAdminOpen(true)}
            >
              <ShieldCheck size={15} />
              <span>站长上架管理</span>
            </button>
          </div>
        </div>
      </section>

      {showGuide && (
        <section className="studio-card ws-guide-card">
          <div className="ws-guide-head">
            <h2 className="section-heading">
              <FileCode2 size={17} /> .jypack.zip 资源包制作速览
            </h2>
            <span className="gb-role-badge local">通用格式 v1</span>
          </div>
          <div className="ws-guide-grid">
            <div className="ws-guide-col">
              <h3>1. 根目录必备 manifest.json</h3>
              <p>
                每个资源包均为标准 ZIP 压缩包，内含 <code>manifest.json</code>（声明{' '}
                <code>schemaVersion: 1</code>、<code>packId</code>、<code>type</code>：
                <code>course</code> / <code>exam</code> / <code>character</code>、
                <code>name</code>、<code>version</code>、<code>author</code>、<code>license</code>、
                <code>summary</code>）。
              </p>
            </div>
            <div className="ws-guide-col">
              <h3>2. 专业课包 vs 角色包结构</h3>
              <p>
                <strong>专业课包</strong>包含 <code>course.json</code>（整门新科目必填）、
                <code>chapters.json</code>、<code>papers/*.json</code> 与 <code>figures/*</code>；
                <strong>角色包</strong>包含 <code>characters.json</code>（<code>spCards</code> /{' '}
                <code>characters</code>）与 <code>assets/*</code>，支持 <code>direct</code>{' '}
                即装即用或 <code>gacha</code> 小鱼干抽取。
              </p>
            </div>
            <div className="ws-guide-col">
              <h3>3. 一键检验与打包命令</h3>
              <p>
                使用仓库内脚手架一键检验并打包（含 KaTeX 公式语法与采分点总分检查），详情查阅{' '}
                <code>docs/创意工坊资源包制作与导入规范.md</code>：
              </p>
              <pre className="ws-code-snippet">
                python scripts/pack_workshop.py --src ./my_pack --out my_pack.jypack.zip
              </pre>
            </div>
          </div>
        </section>
      )}

      {banner && (
        <div className={`feedback-banner ${banner.kind} ws-banner`}>
          <span>{banner.text}</span>
          {banner.actionLabel && banner.onAction && (
            <button
              type="button"
              className="btn btn-tactical btn-sm"
              onClick={banner.onAction}
            >
              <span>{banner.actionLabel}</span>
              <ArrowRight size={14} />
            </button>
          )}
        </div>
      )}

      {importErrors.length > 0 && (
        <div className="feedback-banner err">
          <div>
            <strong>资源包校验错误（共 {importErrors.length} 项）：</strong>
            <ul className="ws-error-list">
              {importErrors.map((err, i) => (
                <li key={i}>{err}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      <section className="studio-card ws-toolbar">
        <div className="seg-group" role="tablist" aria-label="工坊分类">
          <button
            type="button"
            className={`seg-btn ${activeTab === 'all' ? 'active' : ''}`}
            onClick={() => setActiveTab('all')}
          >
            全部工坊资源 ({catalogPacks.length})
          </button>
          <button
            type="button"
            className={`seg-btn ${activeTab === 'course_all' ? 'active' : ''}`}
            onClick={() => setActiveTab('course_all')}
          >
            专业课试卷包 ({catalogPacks.filter((p) => p.type !== 'character').length})
          </button>
          <button
            type="button"
            className={`seg-btn ${activeTab === 'character' ? 'active' : ''}`}
            onClick={() => setActiveTab('character')}
          >
            角色包 ({catalogPacks.filter((p) => p.type === 'character').length})
          </button>
          <button
            type="button"
            className={`seg-btn ${activeTab === 'installed' ? 'active' : ''}`}
            onClick={() => setActiveTab('installed')}
          >
            已安装管理 ({installedPacks.length})
          </button>
        </div>

        <div className="ws-toolbar-right">
          <label className="ws-search-box">
            <Search size={14} />
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索科目、packId、作者或标签…"
              aria-label="搜索工坊资源"
            />
          </label>
          <span className={`ws-mode-pill ${catalogOnline ? 'online' : 'offline'}`}>
            {catalogOnline ? '云端工坊同步' : '本地离线目录'}
          </span>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            disabled={catalogLoading}
            onClick={() => void loadCatalog()}
            title="刷新工坊目录"
          >
            <RefreshCw size={14} />
          </button>
        </div>
      </section>

      {activeTab === 'installed' ? (
        !workshopReady ? (
          <div className="studio-card empty-mini">正在读取浏览器本地工坊仓库…</div>
        ) : filteredInstalled.length === 0 ? (
          <div className="studio-card empty-mini">
            {installedPacks.length === 0
              ? '暂未安装任何创意工坊资源包。你可以从上方「全部工坊资源」安装，或点击「从本地导入 .jypack.zip」。'
              : '没有匹配当前搜索词的已安装资源包。'}
          </div>
        ) : (
          <div className="ws-grid">
            {filteredInstalled.map((pack) => {
              const meta = PACK_TYPE_META[pack.manifest.type];
              const TypeIcon = meta.Icon;
              const coverSrc = pack.coverRelPath
                ? resolvePackBlobUrl(pack.packId, pack.coverRelPath)
                : undefined;
              const chips = statsChips(pack.manifest.type, pack.stats, pack.sizeBytes);
              return (
                <article
                  key={pack.packId}
                  className={`studio-card ws-card ${pack.enabled ? '' : 'is-disabled'}`}
                >
                  <div className="ws-card-top">
                    {coverSrc ? (
                      <img
                        src={coverSrc}
                        alt={pack.manifest.name}
                        className="ws-card-cover"
                      />
                    ) : (
                      <div className={`ws-card-cover-placeholder ${meta.badgeClass}`}>
                        <TypeIcon size={24} />
                      </div>
                    )}
                    <div className="ws-card-head-text">
                      <div className="ws-card-badges">
                        <span className={`ws-badge ${meta.badgeClass}`}>{meta.label}</span>
                        <span className={`ws-badge ${pack.enabled ? 'enabled' : 'disabled'}`}>
                          {pack.enabled ? '已启用' : '已暂停'}
                        </span>
                        <span className="ws-badge neutral">
                          {pack.source === 'local' ? '本地导入' : '工坊下载'}
                        </span>
                        {pack.manifest.type === 'character' && (
                          <span className="ws-badge unlock">
                            {(pack.characterPayload?.unlockMode ?? pack.manifest.unlockMode) ===
                            'gacha'
                              ? '卡池抽取'
                              : '即装即用'}
                          </span>
                        )}
                      </div>
                      <h3 className="ws-card-title">{pack.manifest.name}</h3>
                      <div className="ws-card-meta">
                        <span className="font-mono">{pack.packId}</span>
                        <span>·</span>
                        <span>v{pack.manifest.version}</span>
                        <span>·</span>
                        <span>{pack.manifest.author}</span>
                      </div>
                    </div>
                  </div>

                  <p className="ws-card-summary">{pack.manifest.summary}</p>
                  <div className="ws-card-meta">
                    <span>许可：{pack.manifest.license}</span>
                    <span>·</span>
                    <span>安装于 {pack.installedAt.slice(0, 10)}</span>
                  </div>

                  {chips.length > 0 && (
                    <div className="ws-card-stats">
                      {chips.map((c) => (
                        <span key={c} className="ws-stat-chip">
                          {c}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="ws-card-actions">
                    {pack.enabled && (
                      <button
                        type="button"
                        className="btn btn-tactical btn-sm"
                        onClick={() => navigateToInstalledPack(pack)}
                      >
                        <span>前往使用</span>
                        <ArrowRight size={13} />
                      </button>
                    )}
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => void handleToggleEnabled(pack)}
                    >
                      {pack.enabled ? <PowerOff size={13} /> : <Power size={13} />}
                      <span>{pack.enabled ? '暂停使用' : '重新启用'}</span>
                    </button>
                    {confirmUninstallId === pack.packId ? (
                      <button
                        type="button"
                        className="btn btn-danger btn-sm"
                        onClick={() => void handleUninstall(pack)}
                      >
                        <Trash2 size={13} /> 确认卸载
                      </button>
                    ) : (
                      <button
                        type="button"
                        className="btn btn-ghost-danger btn-sm"
                        onClick={() => setConfirmUninstallId(pack.packId)}
                      >
                        <Trash2 size={13} /> 卸载
                      </button>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        )
      ) : catalogLoading && catalogPacks.length === 0 ? (
        <div className="studio-card empty-mini">正在拉取创意工坊资源目录…</div>
      ) : filteredCatalog.length === 0 ? (
        <div className="studio-card empty-mini">
          <p>
            {catalogPacks.length === 0
              ? '当前创意工坊云端目录暂未上架公开资源包。如果你已有本地制作或好友分享的 .jypack.zip，可直接点击右上角「从本地导入 .jypack.zip」体验！'
              : '没有找到匹配当前筛选条件的资源包，试试清空搜索关键词或切换分类标签。'}
          </p>
        </div>
      ) : (
        <div className="ws-grid">
          {filteredCatalog.map((pack) => {
            const meta = PACK_TYPE_META[pack.type];
            const TypeIcon = meta.Icon;
            const installed = installedMap[pack.packId];
            const hasUpdate = Boolean(installed && installed.manifest.version !== pack.version);
            const isDownloading = downloadingId === pack.packId;
            const pct =
              isDownloading && downloadProgress && downloadProgress.total > 0
                ? Math.min(100, Math.round((downloadProgress.received / downloadProgress.total) * 100))
                : 0;
            const chips = statsChips(pack.type, pack.stats, pack.sizeBytes, pack.downloads);

            return (
              <article
                key={pack.packId}
                className={`studio-card ws-card ${pack.featured ? 'is-featured' : ''}`}
              >
                <div className="ws-card-top">
                  {pack.coverDataUrl ? (
                    <img src={pack.coverDataUrl} alt={pack.name} className="ws-card-cover" />
                  ) : (
                    <div className={`ws-card-cover-placeholder ${meta.badgeClass}`}>
                      <TypeIcon size={24} />
                    </div>
                  )}
                  <div className="ws-card-head-text">
                    <div className="ws-card-badges">
                      {pack.featured && (
                        <span className="ws-badge pin">
                          <Pin size={10} /> 站长推荐
                        </span>
                      )}
                      <span className={`ws-badge ${meta.badgeClass}`}>{meta.label}</span>
                      {pack.type === 'character' && (
                        <span className="ws-badge unlock">
                          {pack.unlockMode === 'gacha' ? '卡池抽取' : '即装即用'}
                        </span>
                      )}
                      <span className="ws-badge neutral">
                        {pack.storageMode === 'd1' ? '站内直传' : '外链托管'}
                      </span>
                      {installed && (
                        <span className="ws-badge enabled">
                          <CheckCircle2 size={10} /> {installed.enabled ? '已安装' : '已暂停'}
                        </span>
                      )}
                      {hasUpdate && <span className="ws-badge update">可更新 v{pack.version}</span>}
                    </div>
                    <h3 className="ws-card-title">{pack.name}</h3>
                    <div className="ws-card-meta">
                      <span className="font-mono">{pack.packId}</span>
                      <span>·</span>
                      <span>v{pack.version}</span>
                      <span>·</span>
                      <span>作者：{pack.author}</span>
                    </div>
                  </div>
                </div>

                <p className="ws-card-summary">{pack.summary}</p>
                {pack.description && <p className="ws-card-desc">{pack.description}</p>}

                {pack.license && (
                  <div className="ws-card-meta">
                    <span>许可与署名：{pack.license}</span>
                    {pack.targetCourseId && (
                      <>
                        <span>·</span>
                        <span>目标科目：{pack.targetCourseId}</span>
                      </>
                    )}
                  </div>
                )}

                {chips.length > 0 && (
                  <div className="ws-card-stats">
                    {chips.map((c) => (
                      <span key={c} className="ws-stat-chip">
                        {c}
                      </span>
                    ))}
                  </div>
                )}

                {pack.tags.length > 0 && (
                  <div className="ws-card-tags">
                    {pack.tags.map((tag) => (
                      <span key={tag} className="tag-chip">
                        #{tag}
                      </span>
                    ))}
                  </div>
                )}

                {isDownloading && downloadProgress && (
                  <div className="ws-progress-wrap">
                    <div className="ws-progress-head">
                      <span>正在下载并校验资源包…</span>
                      <span className="font-mono">
                        {formatPackSize(downloadProgress.received)}
                        {downloadProgress.total > 0
                          ? ` / ${formatPackSize(downloadProgress.total)} (${pct}%)`
                          : ''}
                      </span>
                    </div>
                    <div className="progress-bar-track">
                      <div className="progress-seg mastered" style={{ width: `${pct || 30}%` }} />
                    </div>
                  </div>
                )}

                <div className="ws-card-actions">
                  {installed ? (
                    <>
                      {installed.enabled && (
                        <button
                          type="button"
                          className="btn btn-tactical btn-sm"
                          onClick={() => navigateToInstalledPack(installed)}
                        >
                          <span>前往使用</span>
                          <ArrowRight size={13} />
                        </button>
                      )}
                      {hasUpdate && (
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          disabled={Boolean(downloadingId)}
                          onClick={() => void handleInstallCatalogPack(pack)}
                        >
                          <Download size={13} /> 更新至 v{pack.version}
                        </button>
                      )}
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={() => void handleToggleEnabled(installed)}
                      >
                        {installed.enabled ? <PowerOff size={13} /> : <Power size={13} />}
                        <span>{installed.enabled ? '暂停' : '启用'}</span>
                      </button>
                      {confirmUninstallId === pack.packId ? (
                        <button
                          type="button"
                          className="btn btn-danger btn-sm"
                          onClick={() => void handleUninstall(installed)}
                        >
                          <Trash2 size={13} /> 确认卸载
                        </button>
                      ) : (
                        <button
                          type="button"
                          className="btn btn-ghost-danger btn-sm"
                          onClick={() => setConfirmUninstallId(pack.packId)}
                        >
                          <Trash2 size={13} /> 卸载
                        </button>
                      )}
                    </>
                  ) : (
                    <>
                      <button
                        type="button"
                        className="btn btn-tactical btn-sm"
                        disabled={Boolean(downloadingId)}
                        onClick={() => void handleInstallCatalogPack(pack)}
                      >
                        <Download size={14} />
                        <span>{isDownloading ? '安装中…' : '一键安装'}</span>
                      </button>
                      <a
                        className="btn btn-secondary btn-sm"
                        href={getDownloadHref(pack, catalogOnline)}
                        download={pack.fileName}
                        target={pack.storageMode === 'url' ? '_blank' : undefined}
                        rel={pack.storageMode === 'url' ? 'noopener noreferrer' : undefined}
                      >
                        <Download size={13} />
                        <span>下载 .zip</span>
                      </a>
                    </>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      )}

      <WorkshopAdminModal
        open={adminOpen}
        onClose={() => setAdminOpen(false)}
        onCatalogChanged={() => void loadCatalog()}
      />
    </div>
  );
};
