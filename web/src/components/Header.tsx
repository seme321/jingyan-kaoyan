import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom';
import {
  BarChart3,
  BookMarked,
  BookOpen,
  Check,
  ChevronDown,
  Compass,
  FileSpreadsheet,
  Info,
  Layers,
  Megaphone,
  Menu,
  Settings,
  Sparkles,
  Timer,
  X,
} from 'lucide-react';
import { useStudy } from '../context/StudyContext';
import { useData } from '../context/DataContext';
import { BRAND } from '../brand';
import { WhaleLogo } from './WhaleLogo';

interface HeaderProps {
  onOpenSettings: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onOpenSettings }) => {
  const { state } = useStudy();
  const { courses, currentCourse, setCourseId, questionsById, hasUnreadAnnouncement } = useData();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [switcherOpen, setSwitcherOpen] = useState(false);
  const switcherRef = useRef<HTMLDivElement | null>(null);
  const location = useLocation();
  const navigate = useNavigate();

  const wrongCount = useMemo(
    () =>
      Object.entries(state.records).filter(
        ([qid, r]) => r.inWrongBook && Boolean(questionsById[qid])
      ).length,
    [state.records, questionsById]
  );

  const handleSelectCourse = (nextId: string) => {
    if (nextId !== currentCourse.id) {
      setCourseId(nextId);
      if (location.search) {
        navigate(location.pathname, { replace: true });
      }
    }
    setSwitcherOpen(false);
    setMobileOpen(false);
  };

  useEffect(() => {
    setMobileOpen(false);
    setSwitcherOpen(false);
  }, [location.pathname, location.search]);

  useEffect(() => {
    if (!switcherOpen) return;
    const onClickOutside = (e: MouseEvent) => {
      if (switcherRef.current && !switcherRef.current.contains(e.target as Node)) {
        setSwitcherOpen(false);
      }
    };
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, [switcherOpen]);

  return (
    <header className="top-header">
      <div className="header-inner">
        <div className="brand-cluster" ref={switcherRef}>
          <Link to="/" className="brand-link">
            <WhaleLogo size={33} className="brand-logo" />
            <span className="brand-name">{BRAND.name}</span>
          </Link>

          <button
            type="button"
            className={`course-switcher-btn ${switcherOpen ? 'open' : ''}`}
            onClick={() => setSwitcherOpen((v) => !v)}
            title="切换院校与考研专业课板块"
          >
            <span>{currentCourse.shortLabel}</span>
            <ChevronDown size={13} />
          </button>

          {switcherOpen && (
            <div className="course-popover">
              <div className="course-popover-head">切换考研专业课板块（各科学习记录独立保存）</div>
              <div className="course-popover-list">
                {courses.map((c) => {
                  const active = c.id === currentCourse.id;
                  return (
                    <button
                      key={c.id}
                      type="button"
                      className={`course-option ${active ? 'active' : ''}`}
                      onClick={() => handleSelectCourse(c.id)}
                    >
                      <div className="course-opt-top">
                        <span className="course-opt-name">{c.name}</span>
                        <span className={`status-chip ${c.status === 'ready' ? 'ready' : 'planned'}`}>
                          {c.status === 'ready' ? '已上线' : '框架就绪'}
                        </span>
                        {active && <Check size={15} className="text-sky" />}
                      </div>
                      <p className="course-opt-desc">{c.description}</p>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        <nav className="desktop-nav" aria-label="主导航">
          <NavLink to="/practice" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Sparkles size={15} /> 逐题刷题
          </NavLink>
          <NavLink to="/year" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <BookOpen size={15} /> 按年整卷
          </NavLink>
          <NavLink to="/chapters" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Layers size={15} /> 章节练习
          </NavLink>
          <NavLink to="/methods" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Compass size={15} /> 解题方法
          </NavLink>
          <NavLink to="/mock" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Timer size={15} /> 全真模考
            {state.activeMock && <span className="nav-dot" title="有进行中的模考" />}
          </NavLink>
          <NavLink to="/wrong-book" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <BookMarked size={15} /> 错题与收藏
            {wrongCount > 0 && <span className="nav-pill">{wrongCount}</span>}
          </NavLink>
          <NavLink to="/dashboard" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <BarChart3 size={15} /> 命题大盘
          </NavLink>
          <NavLink to="/formulas" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <FileSpreadsheet size={15} /> 公式手册
          </NavLink>
        </nav>

        <div className="header-actions">
          <NavLink
            to="/board"
            className={({ isActive }) => `nav-progress-chip nav-board-chip ${isActive ? 'active' : ''}`}
            title="查看站点公告与考研留言板"
          >
            <Megaphone size={13} /> 公告留言
            {hasUnreadAnnouncement && <span className="nav-dot" title="有最新站点公告" />}
          </NavLink>
          <NavLink to="/progress" className={({ isActive }) => `nav-progress-chip ${isActive ? 'active' : ''}`}>
            我的进度
          </NavLink>
          <button
            type="button"
            className="icon-btn"
            onClick={onOpenSettings}
            title="外观设置与数据备份"
            aria-label="设置"
          >
            <Settings size={17} />
          </button>
          <button
            type="button"
            className="icon-btn mobile-menu-btn"
            onClick={() => setMobileOpen((v) => !v)}
            aria-label="打开菜单"
          >
            {mobileOpen ? <X size={19} /> : <Menu size={19} />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="mobile-drawer">
          <div className="mobile-course-row">
            <span className="mobile-course-lbl">当前专业课板块：</span>
            <div className="seg-group">
              {courses.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  className={`seg-btn ${c.id === currentCourse.id ? 'active' : ''}`}
                  onClick={() => handleSelectCourse(c.id)}
                >
                  {c.shortLabel}
                </button>
              ))}
            </div>
          </div>
          <NavLink to="/practice" className="mobile-nav-link">
            <Sparkles size={16} /> 逐题刷题
          </NavLink>
          <NavLink to="/year" className="mobile-nav-link">
            <BookOpen size={16} /> 按年整卷
          </NavLink>
          <NavLink to="/chapters" className="mobile-nav-link">
            <Layers size={16} /> 考纲章节练习
          </NavLink>
          <NavLink to="/methods" className="mobile-nav-link">
            <Compass size={16} /> 解题方法库
          </NavLink>
          <NavLink to="/mock" className="mobile-nav-link">
            <Timer size={16} /> 全真限时模考
          </NavLink>
          <NavLink to="/wrong-book" className="mobile-nav-link">
            <BookMarked size={16} /> 错题本 / 收藏 / 笔记 {wrongCount > 0 ? `(${wrongCount})` : ''}
          </NavLink>
          <NavLink to="/progress" className="mobile-nav-link">
            <BarChart3 size={16} /> 我的进度与掌握热力图
          </NavLink>
          <NavLink to="/dashboard" className="mobile-nav-link">
            <BarChart3 size={16} /> 命题结构大盘
          </NavLink>
          <NavLink to="/formulas" className="mobile-nav-link">
            <FileSpreadsheet size={16} /> 核心公式速记手册
          </NavLink>
          <NavLink to="/board" className="mobile-nav-link">
            <Megaphone size={16} /> 站点公告与考研留言板
            {hasUnreadAnnouncement && <span className="nav-dot" />}
          </NavLink>
          <NavLink to="/about" className="mobile-nav-link">
            <Info size={16} /> 关于本站 · 鸣谢 Gemini 与角色图鉴
          </NavLink>
        </div>
      )}
    </header>
  );
};
