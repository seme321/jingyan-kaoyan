import React, { useRef, useState } from 'react';
import { Cloud, Download, RotateCcw, Upload, X } from 'lucide-react';
import { useStudy } from '../context/StudyContext';
import { useData } from '../context/DataContext';
import { useAccount } from '../context/AccountContext';
import { BRAND } from '../brand';
import type { DiagramDarkMode } from '../types';

interface SettingsModalProps {
  open: boolean;
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ open, onClose }) => {
  const { state, updateSettings, exportBackupJson, importBackupJson, resetCurrentCourseProgress } =
    useStudy();
  const { currentCourse } = useData();
  const { user, cloudMeta, openAccountModal } = useAccount();
  const fileRef = useRef<HTMLInputElement | null>(null);
  const [feedback, setFeedback] = useState<{ ok: boolean; text: string } | null>(null);
  const [confirmReset, setConfirmReset] = useState(false);

  if (!open) return null;

  const { settings } = state;
  const activeDiagramMode: DiagramDarkMode =
    settings.diagramDarkMode ?? (settings.softDiagramInDark ? 'blueprint' : 'original');

  const handleDiagramModeChange = (mode: DiagramDarkMode) => {
    updateSettings({
      diagramDarkMode: mode,
      softDiagramInDark: mode !== 'original',
    });
  };

  const handleDownloadBackup = () => {
    const json = exportBackupJson();
    const blob = new Blob([json], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${BRAND.backupPrefix}_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    setFeedback({ ok: true, text: '已导出全部专业课板块的学习记录 JSON 备份' });
  };

  const handleImportFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const res = importBackupJson(String(reader.result ?? ''));
      setFeedback({ ok: res.ok, text: res.message });
    };
    reader.readAsText(file);
    e.target.value = '';
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <div className="page-kicker">SYSTEM CONFIG // PREFERENCES</div>
            <h3 className="modal-title">终端偏好设置与跨板块备份</h3>
            <p className="modal-sub">各专业课板块进度独立存储在本地浏览器，亦支持登录账号跨设备云端同步</p>
          </div>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="关闭设置">
            <X size={18} />
          </button>
        </div>

        <div className="settings-body">
          <div className="setting-row">
            <div>
              <div className="setting-label">终端视觉主题</div>
              <div className="setting-desc">深海战术终端或工业晒图白昼，支持顶栏一键快切</div>
            </div>
            <div className="seg-group">
              {(
                [
                  ['dark', '深海暗夜'],
                  ['light', '晒图白昼'],
                  ['system', '跟随系统'],
                ] as const
              ).map(([val, label]) => (
                <button
                  key={val}
                  type="button"
                  className={`seg-btn ${settings.theme === val ? 'active' : ''}`}
                  onClick={() => updateSettings({ theme: val })}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="setting-row">
            <div>
              <div className="setting-label">正文字号缩放</div>
              <div className="setting-desc">同步缩放题干、KaTeX 推导公式与解析文字</div>
            </div>
            <div className="seg-group">
              {(
                [
                  ['md', '标准'],
                  ['lg', '大'],
                  ['xl', '更大'],
                  ['2xl', '特大'],
                ] as const
              ).map(([val, label]) => (
                <button
                  key={val}
                  type="button"
                  className={`seg-btn ${settings.fontSize === val ? 'active' : ''}`}
                  onClick={() => updateSettings({ fontSize: val })}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="setting-row">
            <div>
              <div className="setting-label">学术阅读字体</div>
              <div className="setting-desc">可切换现代无衬线或传统书卷宋体风格</div>
            </div>
            <div className="seg-group">
              {(
                [
                  ['sans', '无衬线'],
                  ['serif', '书卷宋体'],
                ] as const
              ).map(([val, label]) => (
                <button
                  key={val}
                  type="button"
                  className={`seg-btn ${settings.fontFamily === val ? 'active' : ''}`}
                  onClick={() => updateSettings({ fontFamily: val })}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="setting-row">
            <div>
              <div className="setting-label">深色模式工程配图渲染</div>
              <div className="setting-desc">蓝图夜视可将白底黑线水力学图转为深蓝护眼蓝图</div>
            </div>
            <div className="seg-group">
              {(
                [
                  ['blueprint', '蓝图夜视'],
                  ['soft', '柔光纸面'],
                  ['original', '原始白底'],
                ] as const
              ).map(([val, label]) => (
                <button
                  key={val}
                  type="button"
                  className={`seg-btn ${activeDiagramMode === val ? 'active' : ''}`}
                  onClick={() => handleDiagramModeChange(val)}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="setting-row">
            <div>
              <div className="setting-label">动态水力学背景（公式流与流线）</div>
              <div className="setting-desc">开启背景水力学方程缓动与流线脉冲，关闭则切换为纯静态测绘网格</div>
            </div>
            <button
              type="button"
              className={`switch-btn ${settings.animatedBg !== false ? 'on' : ''}`}
              onClick={() => updateSettings({ animatedBg: settings.animatedBg === false })}
              aria-label="切换动态水力学背景"
            >
              <span className="switch-thumb" />
            </button>
          </div>

          <div className="setting-row">
            <div>
              <div className="setting-label">答题前隐藏考点与方法</div>
              <div className="setting-desc">逐题练习时先独立审题，提交或展开解析后再显示标签</div>
            </div>
            <button
              type="button"
              className={`switch-btn ${settings.hideTagsBeforeAnswer ? 'on' : ''}`}
              onClick={() => updateSettings({ hideTagsBeforeAnswer: !settings.hideTagsBeforeAnswer })}
              aria-label="切换答题前隐藏考点与方法"
            >
              <span className="switch-thumb" />
            </button>
          </div>

          <div className="setting-divider" />

          <div className="setting-row">
            <div>
              <div className="setting-label">云端账号与跨设备同步</div>
              <div className="setting-desc">
                {user
                  ? `已登录 ${user.displayName} (@${user.username})${cloudMeta ? ` · 云端存档 v${cloudMeta.version}` : ''}`
                  : '游客可直接使用；登录账号可将全部做题记录、笔记、图鉴与私密投递跨设备同步'}
              </div>
            </div>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => {
                onClose();
                openAccountModal('sync');
              }}
            >
              <Cloud size={14} /> {user ? '管理账号与云同步' : '登录 / 注册账号'}
            </button>
          </div>

          <div className="setting-divider" />

          <div className="backup-box">
            <div className="setting-label">全量备份与恢复（JSON）</div>
            <div className="setting-desc">
              一次导出即可备份所有院校专业课板块的做题记录、错题本、收藏、私人笔记，以及小鱼干、角色图鉴与养成进度。
            </div>
            <div className="backup-actions">
              <button type="button" className="btn btn-secondary btn-sm" onClick={handleDownloadBackup}>
                <Download size={14} /> 导出全量备份
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => fileRef.current?.click()}
              >
                <Upload size={14} /> 导入备份恢复
              </button>
              <input
                ref={fileRef}
                type="file"
                accept=".json,application/json"
                style={{ display: 'none' }}
                onChange={handleImportFile}
              />
              {!confirmReset ? (
                <button
                  type="button"
                  className="btn btn-ghost-danger btn-sm"
                  onClick={() => setConfirmReset(true)}
                >
                  <RotateCcw size={14} /> 清空「{currentCourse.shortLabel}」记录
                </button>
              ) : (
                <button
                  type="button"
                  className="btn btn-danger btn-sm"
                  onClick={() => {
                    resetCurrentCourseProgress();
                    setConfirmReset(false);
                    setFeedback({ ok: true, text: `已清空「${currentCourse.shortLabel}」的本地做题与模考记录` });
                  }}
                >
                  确认清空当前板块
                </button>
              )}
            </div>
            {feedback && (
              <div className={`feedback-banner ${feedback.ok ? 'ok' : 'err'}`}>{feedback.text}</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
