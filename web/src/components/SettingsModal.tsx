import React, { useRef, useState } from 'react';
import { Download, RotateCcw, Upload, X } from 'lucide-react';
import { useStudy } from '../context/StudyContext';
import { useData } from '../context/DataContext';
import { BRAND } from '../brand';

interface SettingsModalProps {
  open: boolean;
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ open, onClose }) => {
  const { state, updateSettings, exportBackupJson, importBackupJson, resetCurrentCourseProgress } =
    useStudy();
  const { currentCourse } = useData();
  const fileRef = useRef<HTMLInputElement | null>(null);
  const [feedback, setFeedback] = useState<{ ok: boolean; text: string } | null>(null);
  const [confirmReset, setConfirmReset] = useState(false);

  if (!open) return null;

  const { settings } = state;

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
            <h3 className="modal-title">偏好设置与跨板块备份</h3>
            <p className="modal-sub">各专业课板块进度独立存储在本地浏览器中，无需注册登录</p>
          </div>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="关闭设置">
            <X size={18} />
          </button>
        </div>

        <div className="settings-body">
          <div className="setting-row">
            <div>
              <div className="setting-label">界面外观</div>
              <div className="setting-desc">深海夜读或浅海白昼，随心切换</div>
            </div>
            <div className="seg-group">
              {(
                [
                  ['dark', '深色'],
                  ['light', '浅色'],
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
              <div className="setting-label">正文字号</div>
              <div className="setting-desc">同步缩放题目、推导公式与解析文字</div>
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
              <div className="setting-label">阅读字体</div>
              <div className="setting-desc">可切换现代无衬线或传统书卷宋体风格</div>
            </div>
            <div className="seg-group">
              {(
                [
                  ['sans', '默认无衬线'],
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
              <div className="setting-label">答题前隐藏考点与方法</div>
              <div className="setting-desc">逐题练习时先独立审题，提交或展开解析后再显示标签</div>
            </div>
            <button
              type="button"
              className={`switch-btn ${settings.hideTagsBeforeAnswer ? 'on' : ''}`}
              onClick={() => updateSettings({ hideTagsBeforeAnswer: !settings.hideTagsBeforeAnswer })}
            >
              <span className="switch-thumb" />
            </button>
          </div>

          <div className="setting-row">
            <div>
              <div className="setting-label">深色下附图柔和护眼</div>
              <div className="setting-desc">降低白底工程示意图在暗色背景下的刺眼对比度</div>
            </div>
            <button
              type="button"
              className={`switch-btn ${settings.softDiagramInDark ? 'on' : ''}`}
              onClick={() => updateSettings({ softDiagramInDark: !settings.softDiagramInDark })}
            >
              <span className="switch-thumb" />
            </button>
          </div>

          <div className="setting-divider" />

          <div className="backup-box">
            <div className="setting-label">全量备份与恢复（JSON）</div>
            <div className="setting-desc">
              一次导出即可备份所有院校专业课板块的做题记录、错题本、收藏与私人笔记。
            </div>
            <div className="backup-actions">
              <button type="button" className="btn btn-secondary" onClick={handleDownloadBackup}>
                <Download size={15} /> 导出全量备份
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => fileRef.current?.click()}
              >
                <Upload size={15} /> 导入备份恢复
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
                  className="btn btn-ghost-danger"
                  onClick={() => setConfirmReset(true)}
                >
                  <RotateCcw size={15} /> 清空「{currentCourse.shortLabel}」记录
                </button>
              ) : (
                <button
                  type="button"
                  className="btn btn-danger"
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
