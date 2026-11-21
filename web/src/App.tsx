import React, { useState } from 'react';
import { HashRouter, Link, Navigate, Route, Routes } from 'react-router-dom';
import { DataProvider, useData } from './context/DataContext';
import { StudyProvider } from './context/StudyContext';
import { Header } from './components/Header';
import { SettingsModal } from './components/SettingsModal';
import { Mascot } from './components/Mascot';
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

const AppShell: React.FC = () => {
  const { loading, error, currentCourse } = useData();
  const [settingsOpen, setSettingsOpen] = useState(false);

  return (
    <div className="app-root">
      <div className="ocean-bg" aria-hidden="true" />
      <Header onOpenSettings={() => setSettingsOpen(true)} />
      <main className="main-content">
        {loading ? (
          <div className="loading-screen">
            <Mascot pose="study" size={140} float />
            <p>
              {BRAND.mascotName}正在加载「{currentCourse.name}」真题与公式库…
            </p>
          </div>
        ) : error ? (
          <div className="page-container">
            <div className="empty-state-card">
              <Mascot pose="think" size={120} />
              <h3>题库加载失败</h3>
              <p>{error}</p>
            </div>
          </div>
        ) : (
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
            <Route path="/gallery" element={<Navigate to="/about?section=codex" replace />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        )}
      </main>
      <footer className="site-footer">
        <div className="footer-brand">
          <span>
            © {new Date().getFullYear()} {BRAND.fullName} · 当前板块：{currentCourse.name}（非官方个人学习工具）
          </span>
          <span className="footer-sub">
            联系邮箱：<a href={`mailto:${BRAND.contact}`}>{BRAND.contact}</a> · 考研交流 QQ 群：{BRAND.qqGroup} ·
            解析由 Gemini 等 AI 辅助整理，仅供学习参考
          </span>
        </div>
        <div className="footer-links">
          <Link to="/board" className="footer-link">
            公告与留言板
          </Link>
          <span aria-hidden="true">·</span>
          <Link to="/about?section=codex" className="footer-link">
            鸣谢 Gemini / 角色图鉴
          </Link>
          <span aria-hidden="true">·</span>
          <Link to="/about" className="footer-link">
            关于 / 版权 / 侵删
          </Link>
        </div>
      </footer>
      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
};

export const App: React.FC = () => (
  <DataProvider>
    <StudyProvider>
      <HashRouter>
        <AppShell />
      </HashRouter>
    </StudyProvider>
  </DataProvider>
);

export default App;
