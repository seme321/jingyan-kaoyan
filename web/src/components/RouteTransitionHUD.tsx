import React, { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { useData } from '../context/DataContext';

const ROUTE_META: Record<string, { code: string; label: string }> = {
  '/': { code: '00 // TERMINAL', label: '备考指挥终端' },
  '/practice': { code: '01 // PRACTICE', label: '逐题精练台' },
  '/year': { code: '02 // ARCHIVE', label: '历年真题整卷' },
  '/chapters': { code: '03A // SYLLABUS', label: '考纲章节练习' },
  '/methods': { code: '03B // METHODS', label: '通用解题方法库' },
  '/dashboard': { code: '03C // ANALYTICS', label: '命题结构大盘' },
  '/mock': { code: '04 // SIMULATION', label: '全真限时模考' },
  '/wrong-book': { code: '05 // ERRATA', label: '错题与笔记墙' },
  '/formulas': { code: '06 // CODEX', label: '核心公式手册' },
  '/progress': { code: 'SYS // MATRIX', label: '进度与掌握热力图' },
  '/board': { code: 'COM // BROADCAST', label: '站点公告与留言' },
  '/about': { code: 'ARC // DOSSIER', label: '角色图鉴与关于' },
};

export const RouteTransitionHUD: React.FC = () => {
  const location = useLocation();
  const { currentCourse } = useData();
  const initializedRef = useRef(false);
  const [pulse, setPulse] = useState<{
    id: number;
    code: string;
    label: string;
    kind: 'route' | 'course';
  } | null>(null);

  const prevPathRef = useRef(location.pathname);
  const prevCourseRef = useRef(currentCourse.id);

  useEffect(() => {
    if (!initializedRef.current) {
      initializedRef.current = true;
      prevPathRef.current = location.pathname;
      prevCourseRef.current = currentCourse.id;
      return;
    }

    const courseChanged = prevCourseRef.current !== currentCourse.id;
    const pathChanged = prevPathRef.current !== location.pathname;
    prevPathRef.current = location.pathname;
    prevCourseRef.current = currentCourse.id;

    if (!courseChanged && !pathChanged) return;

    const meta = ROUTE_META[location.pathname] ?? { code: 'SYS // VIEW', label: '页面切换' };
    const nextPulse = courseChanged
      ? {
          id: Date.now(),
          code: `MODULE // ${currentCourse.id.toUpperCase()}`,
          label: `已切换至 ${currentCourse.shortLabel}`,
          kind: 'course' as const,
        }
      : {
          id: Date.now(),
          code: meta.code,
          label: meta.label,
          kind: 'route' as const,
        };

    setPulse(nextPulse);
    const timer = window.setTimeout(() => {
      setPulse((cur) => (cur?.id === nextPulse.id ? null : cur));
    }, 560);

    return () => window.clearTimeout(timer);
  }, [location.pathname, currentCourse.id, currentCourse.shortLabel]);

  if (!pulse) return null;

  return (
    <div key={pulse.id} className={`route-transition-layer kind-${pulse.kind}`} aria-hidden="true">
      <div className="route-scan-bar" />
      <div className="route-diag-wipe" />
      <div className="route-hud-toast">
        <span className="route-hud-dot" />
        <span className="route-hud-code">{pulse.code}</span>
        <span className="route-hud-sep">/</span>
        <span className="route-hud-label">{pulse.label}</span>
      </div>
    </div>
  );
};
