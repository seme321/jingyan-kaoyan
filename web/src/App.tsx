import React, { useEffect, useState } from 'react';
import { HashRouter, Link, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { DataProvider, useData } from './context/DataContext';
import { StudyProvider } from './context/StudyContext';
import { CompanionProvider, useCompanion } from './context/CompanionContext';
import { WorkshopProvider } from './context/WorkshopContext';
import { Header } from './components/Header';
import { SettingsModal } from './components/SettingsModal';
import { RewardToastHost } from './components/RewardToastHost';
import { Mascot } from './components/Mascot';
import { TacticalBackground } from './components/TacticalBackground';
import { RouteTransitionHUD } from './components/RouteTransitionHUD';
import { BRAND } from './brand';
import { HomePage } from './pages/HomePage';
import { YearPage } from './pages/YearPage';
import { ChaptersPage } from './pages/ChaptersPage';
import { MethodsPage } from './pages/MethodsPage';
import { PracticePage } from './pages/PracticePage';
import { MockPage } from './pages/MockPage';
import { WrongBookPage } from './pages/WrongBookPage';
import { ProgressPage } from './pages/ProgressPage';
import { DashboardPage } from './pages/DashboardPage';
import { FormulasPage } from './pages/FormulasPage';
import { BoardPage } from './pages/BoardPage';
import { AboutPage } from './pages/AboutPage';
import { CompanionPage } from './pages/CompanionPage';
import { WorkshopPage } from './pages/WorkshopPage';

const AppShell: React.FC = () => {
  const { loading, error, currentCourse } = useData();
  const { companion, activeMascot } = useCompanion();
  const [settingsOpen, setSettingsOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    if (!location.search.includes('section=')) {
      window.scrollTo(0, 0);
    }
  }, [location.pathname, location.search]);

  return (
    <div className="app-root">
      <TacticalBackground />
      <Header onOpenSettings={() => setSettingsOpen(true)} />
      <RouteTransitionHUD />
      <main className="main-content">
        {loading ? (
          <div className="loading-screen">
            <Mascot pose="study" size={140} float />
            <span className="loading-code">SYS // SYNCING COURSE MODULE [{currentCourse.id.toUpperCase()}]</span>
            <p>
              {companion.applyGlobally ? activeMascot.name : BRAND.mascotName}正在加载「{currentCourse.name}」真题与公式库…
            </p>
          </div>
        ) : error ? (
          <div className="page-container">
            <div className="empty-state-card">
              <Mascot pose="think" size={120} />
              <span className="hud-code">ERR // MODULE_LOAD_FAILED</span>
              <h3>题库加载失败</h3>
              <p>{error}</p>
            </div>
          </div>
        ) : (
          <div key={`${currentCourse.id}-${location.pathname}`} className="route-stage">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/year" element={<YearPage />} />
              <Route path="/chapters" element={<ChaptersPage />} />
              <Route path="/methods" element={<MethodsPage />} />
              <Route path="/practice" element={<PracticePage />} />
              <Route path="/mock" element={<MockPage />} />
              <Route path="/wrong-book" element={<WrongBookPage />} />
              <Route path="/favorites" element={<Navigate to="/wrong-book" replace />} />
              <Route path="/progress" element={<ProgressPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/formulas" element={<FormulasPage />} />
              <Route path="/board" element={<BoardPage />} />
              <Route path="/companion" element={<CompanionPage />} />
              <Route path="/workshop" element={<WorkshopPage />} />
              <Route path="/gallery" element={<Navigate to="/companion?tab=codex" replace />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        )}
      </main>
      <footer className="site-footer">
        <div className="site-footer-inner">
          <div className="footer-brand">
            <div className="footer-sys-line">
              <span className="footer-sys-tag">JINGYAN // {currentCourse.id.toUpperCase()}</span>
              <span>
                © {new Date().getFullYear()} {BRAND.fullName} · 当前板块：{currentCourse.name}（非官方个人学习工具）
              </span>
            </div>
            <span className="footer-sub">
              联系邮箱：<a href={`mailto:${BRAND.contact}`}>{BRAND.contact}</a> · 考研交流 QQ 群：{BRAND.qqGroup} ·
              解析由 Gemini 等 AI 辅助整理，仅供学习参考
            </span>
          </div>
          <div className="footer-links">
            <Link to="/companion" className="footer-link">
              小鱼干补给站
            </Link>
            <span aria-hidden="true">/</span>
            <Link to="/workshop" className="footer-link">
              创意工坊
            </Link>
            <span aria-hidden="true">/</span>
            <Link to="/board" className="footer-link">
              公告与留言板
            </Link>
            <span aria-hidden="true">/</span>
            <Link to="/companion?tab=codex" className="footer-link">
              鸣谢与角色图鉴
            </Link>
            <span aria-hidden="true">/</span>
            <Link to="/about" className="footer-link">
              关于 · 版权 · 侵删
            </Link>
          </div>
        </div>
      </footer>
      <RewardToastHost />
      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
};

export const App: React.FC = () => (
  <WorkshopProvider>
    <DataProvider>
      <StudyProvider>
        <CompanionProvider>
          <HashRouter>
            <AppShell />
          </HashRouter>
        </CompanionProvider>
      </StudyProvider>
    </DataProvider>
  </WorkshopProvider>
);

export default App;
