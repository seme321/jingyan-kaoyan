import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom';
import {
  Activity,
  BarChart3,
  BookMarked,
  BookOpen,
  Check,
  ChevronDown,
  Compass,
  FileSpreadsheet,
  Fish,
  Info,
  Layers,
  Megaphone,
  Menu,
  Moon,
  Package,
  Settings,
  Sparkles,
  Sun,
  Timer,
  User,
  UserCheck,
  X,
} from 'lucide-react';
import { useStudy } from '../context/StudyContext';
import { useData } from '../context/DataContext';
import { useCompanionOptional } from '../context/CompanionContext';
import { useAccount } from '../context/AccountContext';
import { BRAND } from '../brand';
import { WhaleLogo } from './WhaleLogo';

interface HeaderProps {
  onOpenSettings: () => void;
}

const MATRIX_PATHS = ['/chapters', '/methods', '/dashboard'];

export const Header: React.FC<HeaderProps> = ({ onOpenSettings }) => {
  const { state, resolvedTheme, updateSettings } = useStudy();
  const { courses, currentCourse, setCourseId, questionsById, hasUnreadAnnouncement } = useData();
  const companionCtx = useCompanionOptional();
  const { user, syncStatus, syncConflict, repliedAccountInboxCount, openAccountModal } =
    useAccount();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [switcherOpen, setSwitcherOpen] = useState(false);
  const [matrixOpen, setMatrixOpen] = useState(false);
  const switcherRef = useRef<HTMLDivElement | null>(null);
  const matrixRef = useRef<HTMLDivElement | null>(null);
  const location = useLocation();
  const navigate = useNavigate();

  const wrongCount = useMemo(
    () =>
      Object.entries(state.records).filter(
        ([qid, r]) => r.inWrongBook && Boolean(questionsById[qid])
      ).length,
    [state.records, questionsById]
  );

  const isMatrixActive = MATRIX_PATHS.includes(location.pathname);

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

  const handleQuickThemeToggle = () => {
    updateSettings({ theme: resolvedTheme === 'dark' ? 'light' : 'dark' });
  };

  useEffect(() => {
    setMobileOpen(false);
    setSwitcherOpen(false);
    setMatrixOpen(false);
  }, [location.pathname, location.search]);

  useEffect(() => {
    if (!switcherOpen && !matrixOpen) return;
    const onClickOutside = (e: MouseEvent) => {
      const target = e.target as Node;
      if (switcherRef.current && !switcherRef.current.contains(target)) {
        setSwitcherOpen(false);
      }
      if (matrixRef.current && !matrixRef.current.contains(target)) {
        setMatrixOpen(false);
      }
    };
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, [switcherOpen, matrixOpen]);

  return (
    <header className="top-header">
      <div className="header-inner">
        <div className="brand-cluster" ref={switcherRef}>
          <Link to="/" className="brand-link">
            <WhaleLogo size={32} className="brand-logo" />
            <span className="brand-wordmark">
              <span className="brand-name">{BRAND.name}</span>
              <span className="brand-sub-code">HYDRO // TERMINAL</span>
            </span>
          </Link>

          <button
            type="button"
            className={`course-switcher-btn ${switcherOpen ? 'open' : ''}`}
            onClick={() => {
              setSwitcherOpen((v) => !v);
              setMatrixOpen(false);
            }}
            title="切换院校与考研专业课板块"
          >
            <span>{currentCourse.shortLabel}</span>
            <ChevronDown size={13} />
          </button>

          {switcherOpen && (
            <div className="course-popover">
              <div className="course-popover-head">
                <span>SELECT MODULE // 切换专业课</span>
                <span>ISOLATED</span>
              </div>
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
                          {c.status === 'ready' ? 'ONLINE' : 'STANDBY'}
                        </span>
                        {active && <Check size={15} className="text-sky" />}
                      </div>
                      <p className="course-opt-desc">{c.description}</p>
                    </button>
                  );
                })}
              </div>
              <Link
                to="/workshop"
                className="course-popover-foot"
                onClick={() => setSwitcherOpen(false)}
              >
                <Package size={13} /> 前往创意工坊安装更多专业课 →
              </Link>
            </div>
          )}
        </div>

        {/* Streamlined 6-Item Primary Desktop Navigation */}
        <nav className="desktop-nav" aria-label="主导航">
          <NavLink to="/practice" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span className="nav-idx">01</span>
            <Sparkles size={14} /> 逐题刷题
          </NavLink>

          <NavLink to="/year" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span className="nav-idx">02</span>
            <BookOpen size={14} /> 按年整卷
          </NavLink>

          <div className="nav-dropdown-wrap" ref={matrixRef}>
            <button
              type="button"
              className={`nav-item ${isMatrixActive || matrixOpen ? 'active' : ''}`}
              aria-expanded={matrixOpen}
              onClick={() => {
                setMatrixOpen((v) => !v);
                setSwitcherOpen(false);
              }}
            >
              <span className="nav-idx">03</span>
              <Layers size={14} /> 专题矩阵
              <ChevronDown size={13} />
            </button>

            {matrixOpen && (
              <div className="nav-dropdown-menu" role="menu">
                <div className="nav-drop-head">ORTHOGONAL MATRIX // 双轴专题与命题分析</div>
                <NavLink
                  to="/chapters"
                  className={({ isActive }) => `nav-drop-item ${isActive ? 'active' : ''}`}
                >
                  <span className="nav-drop-icon text-sky">
                    <Layers size={15} />
                  </span>
                  <span className="nav-drop-text">
                    <span className="nav-drop-title">
                      考纲章节练习 <span className="nav-drop-code">AXIS-A</span>
                    </span>
                    <span className="nav-drop-desc">按章节重心与常规分值定向攻克薄弱章</span>
                  </span>
                </NavLink>

                <NavLink
                  to="/methods"
                  className={({ isActive }) => `nav-drop-item ${isActive ? 'active' : ''}`}
                >
                  <span className="nav-drop-icon text-purple">
                    <Compass size={15} />
                  </span>
                  <span className="nav-drop-text">
                    <span className="nav-drop-title">
                      通用解题方法库 <span className="nav-drop-code">AXIS-B</span>
                    </span>
                    <span className="nav-drop-desc">跨章节聚合同类破题动作与标准流程</span>
                  </span>
                </NavLink>

                <NavLink
                  to="/dashboard"
                  className={({ isActive }) => `nav-drop-item ${isActive ? 'active' : ''}`}
                >
                  <span className="nav-drop-icon text-yellow">
                    <BarChart3 size={15} />
                  </span>
                  <span className="nav-drop-text">
                    <span className="nav-drop-title">
                      命题结构大盘 <span className="nav-drop-code">DATA</span>
                    </span>
                    <span className="nav-drop-desc">历年各章实考分值热力矩阵与规律对照</span>
                  </span>
                </NavLink>
              </div>
            )}
          </div>

          <NavLink to="/mock" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span className="nav-idx">04</span>
            <Timer size={14} /> 全真模考
            {state.activeMock && <span className="nav-dot" title="有进行中的模考" />}
          </NavLink>

          <NavLink to="/wrong-book" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span className="nav-idx">05</span>
            <BookMarked size={14} /> 错题笔记
            {wrongCount > 0 && <span className="nav-pill">{wrongCount}</span>}
          </NavLink>

          <NavLink to="/formulas" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span className="nav-idx">06</span>
            <FileSpreadsheet size={14} /> 公式手册
          </NavLink>
        </nav>

        <div className="header-actions">
          {companionCtx && (
            <NavLink
              to="/companion"
              className={({ isActive }) => `nav-fish-chip ${isActive ? 'active' : ''}`}
              title="小鱼干补给站 · 每日任务、兑换商店与角色图鉴"
            >
              <Fish size={14} />
              <span>{companionCtx.companion.fish}</span>
              {companionCtx.claimableCount > 0 && (
                <span className="nav-fish-badge">{companionCtx.claimableCount}</span>
              )}
            </NavLink>
          )}
          <NavLink
            to="/progress"
            className={({ isActive }) => `nav-util-chip ${isActive ? 'active' : ''}`}
            title="我的掌握进度与热力图"
          >
            <Activity size={13} /> 进度
          </NavLink>
          <NavLink
            to="/workshop"
            className={({ isActive }) => `nav-util-chip ${isActive ? 'active' : ''}`}
            title="创意工坊：专业课试卷包与角色包"
          >
            <Package size={13} /> 工坊
          </NavLink>
          <NavLink
            to="/board"
            className={({ isActive }) => `nav-util-chip ${isActive ? 'active' : ''}`}
            title="查看站点公告与考研留言板"
          >
            <Megaphone size={13} /> 公告
            {hasUnreadAnnouncement && <span className="nav-dot" title="有最新站点公告" />}
          </NavLink>
          <button
            type="button"
            className={`nav-util-chip account-chip ${user ? 'authed' : ''}`}
            onClick={() => openAccountModal('sync')}
            aria-label={user ? `账号：${user.displayName}` : '登录或注册账号'}
            title={
              user
                ? `已登录账号：${user.displayName}（@${user.username}），点击管理云端同步与私密投递`
                : '登录或注册账号以跨设备同步进度与查看私密投递'
            }
          >
            {user ? <UserCheck size={13} /> : <User size={13} />}
            <span className="account-chip-name">{user ? user.displayName : '登录'}</span>
            {user && (syncConflict || syncStatus === 'error') && (
              <span className="nav-dot" title="云端同步需要处理" />
            )}
            {user && !syncConflict && repliedAccountInboxCount > 0 && (
              <span className="nav-fish-badge">{repliedAccountInboxCount}</span>
            )}
          </button>
          <button
            type="button"
            className="icon-btn theme-toggle-btn"
            onClick={handleQuickThemeToggle}
            title={resolvedTheme === 'dark' ? '切换为工业晒图白昼（浅色）' : '切换为深海战术终端（深色）'}
            aria-label="切换深浅色主题"
          >
            {resolvedTheme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          </button>
          <button
            type="button"
            className="icon-btn"
            onClick={onOpenSettings}
            title="终端偏好设置与数据备份"
            aria-label="设置"
          >
            <Settings size={16} />
          </button>
          <button
            type="button"
            className="icon-btn mobile-menu-btn"
            onClick={() => setMobileOpen((v) => !v)}
            aria-label="打开菜单"
          >
            {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="mobile-drawer">
          <div className="mobile-course-row">
            <span className="mobile-course-lbl">MODULE // 当前板块：</span>
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
          <button
            type="button"
            className={`mobile-account-card ${user ? 'authed' : ''}`}
            onClick={() => {
              setMobileOpen(false);
              openAccountModal(repliedAccountInboxCount > 0 && !syncConflict ? 'inbox' : 'sync');
            }}
          >
            <span className="mobile-account-icon">
              {user ? <UserCheck size={18} /> : <User size={18} />}
            </span>
            <span className="mobile-account-text">
              <span className="mobile-account-title">
                <span>{user ? user.displayName : '登录 / 注册云端账号'}</span>
                {user && <span className="hud-code">@{user.username}</span>}
              </span>
              <span className="mobile-account-sub">
                {user
                  ? syncConflict
                    ? '存在双端差异，点击处理'
                    : repliedAccountInboxCount > 0
                      ? `收到 ${repliedAccountInboxCount} 条站长私密回复`
                      : '云端同步已开启 · 管理进度与私密投递'
                  : '跨设备同步刷题记录、图鉴与私密投递'}
              </span>
            </span>
            <span className="mobile-account-cta">
              <span>{user ? '管理' : '去登录'}</span>
              {user && (syncConflict || syncStatus === 'error') && <span className="nav-dot" />}
              {user && !syncConflict && repliedAccountInboxCount > 0 && (
                <span className="nav-fish-badge">{repliedAccountInboxCount}</span>
              )}
            </span>
          </button>
          <NavLink to="/practice" className="mobile-nav-link">
            <Sparkles size={16} /> 01 · 逐题刷题
          </NavLink>
          <NavLink to="/year" className="mobile-nav-link">
            <BookOpen size={16} /> 02 · 按年整卷
          </NavLink>
          <NavLink to="/chapters" className="mobile-nav-link">
            <Layers size={16} /> 03A · 考纲章节练习
          </NavLink>
          <NavLink to="/methods" className="mobile-nav-link">
            <Compass size={16} /> 03B · 通用解题方法库
          </NavLink>
          <NavLink to="/dashboard" className="mobile-nav-link">
            <BarChart3 size={16} /> 03C · 命题结构大盘
          </NavLink>
          <NavLink to="/mock" className="mobile-nav-link">
            <Timer size={16} /> 04 · 全真限时模考
          </NavLink>
          <NavLink to="/wrong-book" className="mobile-nav-link">
            <BookMarked size={16} /> 05 · 错题本 / 收藏 / 笔记 {wrongCount > 0 ? `(${wrongCount})` : ''}
          </NavLink>
          <NavLink to="/formulas" className="mobile-nav-link">
            <FileSpreadsheet size={16} /> 06 · 核心公式速记手册
          </NavLink>
          <NavLink to="/progress" className="mobile-nav-link">
            <Activity size={16} /> 我的进度与掌握热力图
          </NavLink>
          {companionCtx && (
            <NavLink to="/companion" className="mobile-nav-link">
              <Fish size={16} /> 补给站 · 小鱼干 ({companionCtx.companion.fish}) 与角色图鉴
              {companionCtx.claimableCount > 0 && (
                <span className="nav-fish-badge">{companionCtx.claimableCount}</span>
              )}
            </NavLink>
          )}
          <NavLink to="/board" className="mobile-nav-link">
            <Megaphone size={16} /> 站点公告与考研留言板
            {hasUnreadAnnouncement && <span className="nav-dot" />}
          </NavLink>
          <NavLink to="/workshop" className="mobile-nav-link">
            <Package size={16} /> 创意工坊 · 专业课与角色包
          </NavLink>
          <NavLink to="/about" className="mobile-nav-link">
            <Info size={16} /> 关于本站 · 鸣谢 Gemini 与角色图鉴
          </NavLink>
        </div>
      )}
    </header>
  );
};
