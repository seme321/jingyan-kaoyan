import React, { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  BarChart3,
  BookMarked,
  BookOpen,
  Check,
  CheckCircle2,
  Compass,
  Copy,
  FileSpreadsheet,
  Flame,
  Layers,
  Megaphone,
  Sparkles,
  Timer,
  Users,
} from 'lucide-react';
import { useData } from '../context/DataContext';
import { useStudy } from '../context/StudyContext';
import { BRAND } from '../brand';
import { Mascot } from '../components/Mascot';
import { copyText } from '../utils/clipboard';

function getExamCountdown(): { examYear: number; dateStr: string; daysLeft: number } {
  const now = new Date();
  const candidates = [
    { examYear: 2027, date: new Date('2026-12-19T08:30:00+08:00'), label: '2026 年 12 月 19 日' },
    { examYear: 2028, date: new Date('2027-12-18T08:30:00+08:00'), label: '2027 年 12 月 18 日' },
  ];
  const target = candidates.find((c) => c.date.getTime() >= now.getTime()) ?? candidates[candidates.length - 1];
  const diffMs = Math.max(0, target.date.getTime() - now.getTime());
  const daysLeft = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
  return { examYear: target.examYear, dateStr: target.label, daysLeft };
}

export const HomePage: React.FC = () => {
  const { courses, currentCourse, setCourseId, allQuestions, chapters, formulas, yearsMeta, latestAnnouncement } =
    useData();
  const { state, getRecord } = useStudy();
  const countdown = useMemo(getExamCountdown, []);
  const [copiedQq, setCopiedQq] = useState(false);

  const handleCopyQq = async () => {
    const ok = await copyText(BRAND.qqGroup);
    if (ok) {
      setCopiedQq(true);
      window.setTimeout(() => setCopiedQq(false), 2000);
    }
  };

  const stats = useMemo(() => {
    let mastered = 0;
    let partial = 0;
    let wrong = 0;
    let wrongBook = 0;
    let fav = 0;
    for (const q of allQuestions) {
      const r = getRecord(q.id);
      if (r.status === 'mastered') mastered++;
      else if (r.status === 'partial') partial++;
      else if (r.status === 'wrong') wrong++;
      if (r.inWrongBook) wrongBook++;
      if (r.favorite) fav++;
    }
    const practiced = mastered + partial + wrong;
    const uniqueMethods = new Set(allQuestions.map((q) => q.method)).size;
    return {
      total: allQuestions.length,
      practiced,
      mastered,
      partial,
      wrong,
      wrongBook,
      fav,
      uniqueMethods,
    };
  }, [allQuestions, getRecord]);

  const readyYears = useMemo(() => yearsMeta.filter((y) => y.status === 'ready'), [yearsMeta]);
  const plannedYears = useMemo(() => yearsMeta.filter((y) => y.status !== 'ready'), [yearsMeta]);

  const progressPct = stats.total > 0 ? Math.round((stats.practiced / stats.total) * 100) : 0;
  const masteryPct = stats.total > 0 ? Math.round((stats.mastered / stats.total) * 100) : 0;

  const greeting =
    stats.total === 0
      ? `「${currentCourse.shortLabel}」板块考纲与 ${formulas.length} 组必背公式已就位！真题包转换导入后就能开刷啦～`
      : stats.practiced === 0
        ? `你好呀，我是${BRAND.mascotName}！今天先从「${currentCourse.shortLabel}」真题第 1 题开始吧～`
        : stats.wrongBook > 0
          ? `还有 ${stats.wrongBook} 道错题在等你，先把它们“斩”掉吧！`
          : masteryPct >= 80
            ? '掌握率超过 80% 啦！来一场 180 分钟全真模考检验一下？'
            : `已经刷了 ${stats.practiced} 题，保持节奏，专业课稳稳拿下！`;

  return (
    <div className="page-container">
      {/* Hero Banner */}
      <section className="hero-card">
        <div className="hero-bubbles" aria-hidden="true">
          <i /><i /><i /><i /><i />
        </div>
        <div className="hero-grid">
          <div className="hero-main">
            <div className="hero-top-row">
              <div className="countdown-pill">
                <Flame size={15} className="accent-amber" />
                <span>
                  距 {countdown.examYear} 考研初试 <strong>{countdown.daysLeft} 天</strong> · {countdown.dateStr}
                </span>
              </div>
              <span className="syllabus-pill">{currentCourse.examMetaBadge}</span>
            </div>

            <h1 className="hero-title">
              <span className="hero-title-grad">
                {currentCourse.code} {currentCourse.subject} · {BRAND.fullName}
              </span>
              <span className="hero-title-sub">
                适用目标院校：{currentCourse.school}（非官方个人复习工具）
              </span>
            </h1>
            <p className="hero-subtitle">
              {BRAND.tagline} —— 结构化真题精析 · <strong>章节 × 方法</strong>双线串联 · 错题自评闭环
            </p>

            {/* Quick Course Pills */}
            {courses.length > 1 && (
              <div className="hero-course-pills">
                <span className="hero-course-lbl">快速切换板块：</span>
                {courses.map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    className={`course-pill ${c.id === currentCourse.id ? 'active' : ''}`}
                    onClick={() => setCourseId(c.id)}
                  >
                    {c.name}
                  </button>
                ))}
              </div>
            )}

            <div className="hero-cta-row">
              <Link to="/practice" className="btn btn-primary btn-lg">
                <Sparkles size={17} /> 开始逐题刷题
              </Link>
              <Link to="/mock" className="btn btn-secondary btn-lg">
                <Timer size={17} /> {state.activeMock ? '继续全真模考' : '180 分钟全真模考'}
              </Link>
              <Link to="/year" className="btn btn-ghost btn-lg">
                <BookOpen size={17} /> 历年真题整卷
              </Link>
              <Link to="/formulas" className="btn btn-ghost btn-lg">
                <FileSpreadsheet size={17} /> 必背公式闪卡 ({formulas.length})
              </Link>
            </div>
          </div>

          <div className="hero-mascot-col">
            <div className="hero-mascot-bubble">{greeting}</div>
            <Mascot pose={stats.practiced > 0 && masteryPct >= 80 ? 'cheer' : 'hero'} size={230} float />
          </div>
        </div>

        {/* Live Personal Progress Strip */}
        <div className="hero-stats-strip">
          <div className="stat-metric">
            <span className="stat-val">{stats.practiced} / {stats.total}</span>
            <span className="stat-lbl">已刷真题 ({progressPct}%)</span>
            <span className="stat-bar"><i style={{ width: `${progressPct}%` }} /></span>
          </div>
          <div className="stat-metric">
            <span className="stat-val text-emerald">{stats.mastered}</span>
            <span className="stat-lbl">已掌握 ({masteryPct}%)</span>
            <span className="stat-bar ok"><i style={{ width: `${masteryPct}%` }} /></span>
          </div>
          <div className="stat-metric">
            <span className="stat-val text-coral">{stats.wrongBook}</span>
            <span className="stat-lbl">错题待攻克</span>
          </div>
          <div className="stat-metric">
            <span className="stat-val text-sky">{state.mockHistory.length}</span>
            <span className="stat-lbl">已完成模考</span>
          </div>
        </div>
        <svg className="hero-wave" viewBox="0 0 1200 80" preserveAspectRatio="none" aria-hidden="true">
          <path d="M0 40 C150 10 300 70 450 40 C600 10 750 70 900 40 C1050 10 1150 55 1200 40 L1200 80 L0 80 Z" />
          <path className="w2" d="M0 55 C200 30 350 80 600 52 C850 25 1000 78 1200 50 L1200 80 L0 80 Z" />
        </svg>
      </section>

      {/* Latest Announcement Strip */}
      {latestAnnouncement && (
        <section className="home-announcement-bar" aria-label="最新站点公告">
          <div className="home-ann-left">
            <span className="home-ann-icon">
              <Megaphone size={16} />
            </span>
            <span className="ann-tag-chip">{latestAnnouncement.tag}</span>
            <div className="home-ann-copy">
              <strong className="home-ann-title">{latestAnnouncement.title}</strong>
              <span className="home-ann-summary">{latestAnnouncement.summary}</span>
            </div>
          </div>
          <div className="home-ann-actions">
            <button
              type="button"
              className={`copy-pill compact ${copiedQq ? 'copied' : ''}`}
              onClick={handleCopyQq}
              title="点击复制考研交流 QQ 群号"
            >
              <Users size={13} />
              <span>QQ 群：{BRAND.qqGroup}</span>
              {copiedQq ? <Check size={12} /> : <Copy size={12} />}
            </button>
            <Link to="/board" className="btn btn-primary btn-sm">
              公告与留言板 <ArrowRight size={13} />
            </Link>
          </div>
        </section>
      )}

      {/* 5-Layer Study Architecture Map */}
      <section className="arch-section">
        <div className="section-head">
          <h2 className="section-title">复习体系导览 · {currentCourse.shortLabel}</h2>
          <span className="section-hint">
            {readyYears.length > 0
              ? `已上线 ${readyYears.length} 套真题（共 ${stats.total} 题）${
                  plannedYears.length > 0 ? `，另有 ${plannedYears.length} 套历年卷待按需导入` : ''
                }`
              : `已预置 ${chapters.length} 章考纲与 ${formulas.length} 组核心公式，共 ${plannedYears.length} 套真题待导入`}
          </span>
        </div>

        <div className="arch-stack">
          {/* Layer 1 */}
          <div className="arch-layer">
            <div className="arch-layer-head">
              <div className="arch-badge layer-1">
                ① 底座 · 历年真题精解池（已上线 {readyYears.length} 套 / 规划 {yearsMeta.length} 套）
              </div>
              {yearsMeta.length > 6 && (
                <Link to="/year" className="btn-inline-link">
                  查看全部 {yearsMeta.length} 套历年真题 →
                </Link>
              )}
            </div>
            <div className="arch-cards-grid cols-3">
              {yearsMeta.slice(0, 6).map((ym) => {
                const isReady = ym.status === 'ready';
                return (
                  <Link
                    key={ym.year}
                    to={isReady ? `/year?year=${ym.year}` : '/year'}
                    className={`arch-card ${!isReady ? 'muted-card' : ''}`}
                  >
                    <div className="arch-card-top">
                      <span className="arch-card-title">
                        {ym.year} {currentCourse.shortLabel} 真题
                      </span>
                      <span className={`status-chip ${isReady ? 'ready' : 'planned'}`}>
                        {isReady ? `已上线 · ${ym.questionCount} 题` : '待导入'}
                      </span>
                    </div>
                    <p className="arch-card-desc">
                      {isReady
                        ? `满分 ${ym.totalScore} 分，含题目配图、规范推导解析与步骤采分点。`
                        : `标准目录接口已就绪，使用一键入库脚本即可激活 ${ym.year} 真题。`}
                    </p>
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Orthogonal Axes Row: Layer 2 & Layer 3 */}
          <div className="arch-dual-row">
            <div className="arch-layer">
              <div className="arch-badge layer-2">② 轴一 · 按考纲章节体系</div>
              <div className="arch-cards-grid cols-2">
                <Link to="/chapters" className="arch-card">
                  <div className="arch-card-top">
                    <span className="arch-card-title">{chapters.length} 章考纲练习</span>
                    <Layers size={16} className="text-sky" />
                  </div>
                  <p className="arch-card-desc">
                    围绕「{currentCourse.shortLabel}」重点章节与分值比重，定向突破薄弱板块。
                  </p>
                </Link>
                <Link to="/dashboard" className="arch-card">
                  <div className="arch-card-top">
                    <span className="arch-card-title">命题结构大盘</span>
                    <BarChart3 size={16} className="text-sky" />
                  </div>
                  <p className="arch-card-desc">
                    章节考察规律与历年真题实考分值同屏对照，精准锁定高性价比复习区。
                  </p>
                </Link>
              </div>
            </div>

            <div className="arch-layer">
              <div className="arch-badge layer-3">③ 轴二 · 按通用解题方法</div>
              <div className="arch-cards-grid cols-2">
                <Link to="/methods" className="arch-card">
                  <div className="arch-card-top">
                    <span className="arch-card-title">解题方法库 ({stats.uniqueMethods} 种)</span>
                    <Compass size={16} className="text-purple" />
                  </div>
                  <p className="arch-card-desc">
                    跳出章节壁垒，将历年高频同类设问归纳为标准化解题方法集中训练。
                  </p>
                </Link>
                <Link to="/practice?type=calc" className="arch-card">
                  <div className="arch-card-top">
                    <span className="arch-card-title">计算与推导大题专练</span>
                    <ArrowRight size={16} className="text-purple" />
                  </div>
                  <p className="arch-card-desc">
                    专攻高分值计算与推导大题，配套分步采分点（Rubric）规范考场书写步骤。
                  </p>
                </Link>
              </div>
            </div>
          </div>

          {/* Layer 4 & Layer 5 */}
          <div className="arch-dual-row">
            <div className="arch-layer">
              <div className="arch-badge layer-4">④ 闭环 · 错题诊断与掌握追踪</div>
              <div className="arch-cards-grid cols-2">
                <Link to="/wrong-book" className="arch-card">
                  <div className="arch-card-top">
                    <span className="arch-card-title">错题本 & 私人笔记</span>
                    <BookMarked size={16} className="text-coral" />
                  </div>
                  <p className="arch-card-desc">
                    客观题判错与主观题自评「不会 / 半会」自动入库，各专业课错题独立管理。
                  </p>
                </Link>
                <Link to="/progress" className="arch-card">
                  <div className="arch-card-top">
                    <span className="arch-card-title">掌握度热力图</span>
                    <CheckCircle2 size={16} className="text-emerald" />
                  </div>
                  <p className="arch-card-desc">
                    分年份、分章节可视化追踪每道真题的掌握状态、做题流水与模考得分曲线。
                  </p>
                </Link>
              </div>
            </div>

            <div className="arch-layer">
              <div className="arch-badge layer-5">⑤ 工具 · 考场模拟与公式背诵</div>
              <div className="arch-cards-grid cols-2">
                <Link to="/mock" className="arch-card">
                  <div className="arch-card-top">
                    <span className="arch-card-title">整卷限时模考</span>
                    <Timer size={16} className="text-amber" />
                  </div>
                  <p className="arch-card-desc">
                    180 分钟全真计时、答题卡标记、交卷后客观题秒判 + 主观题采分点自评生成成绩单。
                  </p>
                </Link>
                <Link to="/formulas" className="arch-card">
                  <div className="arch-card-top">
                    <span className="arch-card-title">公式速记手册 ({formulas.length} 组)</span>
                    <FileSpreadsheet size={16} className="text-amber" />
                  </div>
                  <p className="arch-card-desc">
                    整理本科目核心必背公式、物理量纲与适用边界，支持章节精读与闪卡翻面抽背。
                  </p>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
