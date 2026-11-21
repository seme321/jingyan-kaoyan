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
  Fish,
  Flame,
  Heart,
  Layers,
  Megaphone,
  Sparkles,
  Timer,
  UserCheck,
  Users,
} from 'lucide-react';
import { useData } from '../context/DataContext';
import { useStudy } from '../context/StudyContext';
import { useCompanion } from '../context/CompanionContext';
import { BRAND } from '../brand';
import { Mascot } from '../components/Mascot';
import { copyText } from '../utils/clipboard';

function getExamCountdown(): { examYear: number; dateStr: string; daysLeft: number } {
  const now = new Date();
  const candidates = [
    { examYear: 2027, date: new Date('2026-12-19T08:30:00+08:00'), label: '2026-12-19' },
    { examYear: 2028, date: new Date('2027-12-18T08:30:00+08:00'), label: '2027-12-18' },
  ];
  const target = candidates.find((c) => c.date.getTime() >= now.getTime()) ?? candidates[candidates.length - 1];
  const diffMs = Math.max(0, target.date.getTime() - now.getTime());
  const daysLeft = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
  return { examYear: target.examYear, dateStr: target.label, daysLeft };
}

const EXTRA_QUIPS = [
  '伯努利方程先定基准面、再找渐变流断面，水头损失一项都别漏！',
  '静水总压力曲面算水平与铅垂分力，压力体虚实一定先画箭头判断方向～',
  '明渠非均匀流 12 条水面线：先判坡度（缓/陡），再看水深落在 1/2/3 哪一区！',
  '刷错的题会自动同步进错题本，考前清零错题本就能稳稳上岸！',
];

export const HomePage: React.FC = () => {
  const {
    courses,
    currentCourse,
    setCourseId,
    allQuestions,
    papersByYear,
    chapters,
    formulas,
    yearsMeta,
    latestAnnouncement,
  } = useData();
  const { state, getRecord } = useStudy();
  const { companion, activeMascot, claimableCount, unlockedCodexCount, interactWithMascot } =
    useCompanion();
  const countdown = useMemo(getExamCountdown, []);
  const [copiedQq, setCopiedQq] = useState(false);
  const [quipIdx, setQuipIdx] = useState<number>(-1);

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

  const bestMockByYear = useMemo(() => {
    const map: Record<number, { score: number; max: number }> = {};
    for (const m of state.mockHistory) {
      if (!map[m.year] || m.totalScore > map[m.year].score) {
        map[m.year] = { score: m.totalScore, max: m.maxScore };
      }
    }
    return map;
  }, [state.mockHistory]);

  const readyYears = useMemo(() => yearsMeta.filter((y) => y.status === 'ready'), [yearsMeta]);
  const plannedYears = useMemo(() => yearsMeta.filter((y) => y.status !== 'ready'), [yearsMeta]);

  const progressPct = stats.total > 0 ? Math.round((stats.practiced / stats.total) * 100) : 0;
  const masteryPct = stats.total > 0 ? Math.round((stats.mastered / stats.total) * 100) : 0;
  const wrongPct = stats.total > 0 ? Math.min(100, Math.round((stats.wrongBook / stats.total) * 100)) : 0;
  const mockPct = readyYears.length > 0 ? Math.min(100, Math.round((state.mockHistory.length / readyYears.length) * 100)) : 0;

  const unlockedQuotes = useMemo(() => {
    const quotes = activeMascot.studyQuotes.length > 0 ? activeMascot.studyQuotes : EXTRA_QUIPS;
    return activeMascot.bondLevel >= 2 ? quotes : quotes.slice(0, 3);
  }, [activeMascot.bondLevel, activeMascot.studyQuotes]);

  const defaultGreeting =
    stats.total === 0
      ? `「${currentCourse.shortLabel}」考纲与 ${formulas.length} 组公式已就位，导入真题即可开刷！`
      : stats.practiced === 0
        ? activeMascot.greetTemplate
        : stats.wrongBook > 0
          ? `${activeMascot.name}检测到 ${stats.wrongBook} 道待斩错题，先把它们逐一击破吧！`
          : masteryPct >= 80
            ? `掌握率突破 80% 啦！${activeMascot.name}邀你来一场 180 分钟全真模考检验实力！`
            : `已累计突破 ${stats.practiced} 题，${activeMascot.name}陪你稳住节奏拿下专业课！`;

  const activeDialogue =
    quipIdx >= 0 ? unlockedQuotes[quipIdx % unlockedQuotes.length] : defaultGreeting;

  return (
    <div className="page-container">
      {/* PRTS Command Terminal Hero */}
      <section className="hero-terminal">
        <div className="hero-terminal-bg" aria-hidden="true" />
        <div className="hero-watermark" aria-hidden="true">
          {currentCourse.code}
        </div>

        {/* Top System Telemetry Bar */}
        <div className="hero-sys-bar">
          <div className="hero-countdown-block">
            <span className="countdown-tag">COUNTDOWN</span>
            <Flame size={14} className="text-yellow" />
            <span>距 {countdown.examYear} 考研初试</span>
            <strong className="countdown-days">T-{countdown.daysLeft} DAYS</strong>
            <span className="countdown-date">// {countdown.dateStr}</span>
          </div>
          <div className="hero-meta-code">
            <span className="hide-xs">MODULE // {currentCourse.id.toUpperCase()}</span>
            <span className="hide-xs">·</span>
            <span>{currentCourse.examMetaBadge}</span>
          </div>
        </div>

        {/* Main Hero Grid */}
        <div className="hero-body-grid">
          <div className="hero-main">
            <h1 className="hero-title">
              <span className="hero-title-main">
                <span className="hero-title-code">{currentCourse.code}</span>
                {currentCourse.subject} · {BRAND.fullName}
              </span>
              <span className="hero-title-sub">
                适用目标院校：{currentCourse.school}（非官方个人复习工具）
              </span>
            </h1>

            <p className="hero-subtitle">
              {BRAND.tagline} —— 结构化真题精析 · <strong>章节 × 方法</strong>双轴串联 · 采分点与错题自评闭环
            </p>

            {/* Quick Course Module Switcher */}
            {courses.length > 1 && (
              <div className="hero-course-pills">
                <span className="hero-course-lbl">MODULE //</span>
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
              <Link to="/practice" className="btn btn-tactical btn-lg">
                <Sparkles size={16} /> 开始逐题刷题
              </Link>
              <Link to="/mock" className="btn btn-primary btn-lg">
                <Timer size={16} /> {state.activeMock ? '继续全真模考' : '180 分钟全真模考'}
              </Link>
              <Link to="/year" className="btn btn-secondary btn-lg">
                <BookOpen size={16} /> 历年真题整卷
              </Link>
              <Link to="/formulas" className="btn btn-ghost btn-lg">
                <FileSpreadsheet size={16} /> 公式闪卡 ({formulas.length})
              </Link>
            </div>
          </div>

          {/* Operator Mascot Terminal Stage */}
          <div
            className={`hero-operator-stage frame-${companion.equippedFrame} ${
              activeMascot.bondLevel >= 10
                ? 'bond-tier-10'
                : activeMascot.bondLevel >= 6
                  ? 'bond-tier-6'
                  : ''
            }`}
            style={{ '--operator-accent': activeMascot.color } as React.CSSProperties}
          >
            <div
              className="operator-stage-clickzone"
              role="button"
              tabIndex={0}
              title={`点击切换${activeMascot.name}备考提示（每日首次互动可领小鱼干）`}
              onClick={() => {
                setQuipIdx((i) => (i + 1) % unlockedQuotes.length);
                interactWithMascot();
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  setQuipIdx((i) => (i + 1) % unlockedQuotes.length);
                  interactWithMascot();
                }
              }}
            >
              <div className="operator-stage-top">
                <span>
                  ASSISTANT // <strong>{activeMascot.code}</strong>
                </span>
                <span className="operator-stage-badge">
                  {activeMascot.rarity} · <Heart size={10} /> Lv.{activeMascot.bondLevel}
                  {activeMascot.bondLevel >= 10 && <span className="oath-chip">✦ 誓约</span>}
                  {activeMascot.bondLevel >= 6 && activeMascot.bondLevel < 10 && ' ✦'}
                </span>
              </div>
              <Mascot
                pose={stats.practiced > 0 && masteryPct >= 80 ? 'cheer' : 'hero'}
                size={196}
                float
                isHomeStage
              />
              <div className="operator-dialogue-strip">
                <div className="operator-dialogue-head">
                  <span>{activeMascot.name} // BRIEFING</span>
                  <span>NEXT ▸</span>
                </div>
                <span>{activeDialogue}</span>
              </div>
            </div>
            <div className="operator-quick-bar">
              <Link to="/companion?tab=missions" className="op-quick-link">
                <Fish size={12} />
                <span>任务</span>
                {claimableCount > 0 && <span className="op-quick-dot">{claimableCount}</span>}
              </Link>
              <Link to="/companion?tab=codex" className="op-quick-link">
                <Layers size={12} />
                <span>图鉴 {unlockedCodexCount}/42</span>
              </Link>
              <Link to="/companion?tab=stage" className="op-quick-link">
                <UserCheck size={12} />
                <span>换看板</span>
              </Link>
            </div>
          </div>
        </div>

        {/* 4-Cell Precision Telemetry Strip */}
        <div className="hero-telemetry-grid">
          <div className="telemetry-cell">
            <span className="telemetry-code">PROGRESS // 01</span>
            <div className="telemetry-val-row">
              <span className="telemetry-val">{stats.practiced}</span>
              <span className="telemetry-unit">/ {stats.total} 题</span>
            </div>
            <span className="telemetry-lbl">已刷真题 ({progressPct}%)</span>
            <span className="telemetry-bar">
              <i style={{ width: `${progressPct}%` }} />
            </span>
          </div>

          <div className="telemetry-cell">
            <span className="telemetry-code">MASTERY // 02</span>
            <div className="telemetry-val-row">
              <span className="telemetry-val text-emerald">{stats.mastered}</span>
              <span className="telemetry-unit">{masteryPct}%</span>
            </div>
            <span className="telemetry-lbl">已完全掌握</span>
            <span className="telemetry-bar ok">
              <i style={{ width: `${masteryPct}%` }} />
            </span>
          </div>

          <div className="telemetry-cell">
            <span className="telemetry-code">ERRATA // 03</span>
            <div className="telemetry-val-row">
              <span className={`telemetry-val ${stats.wrongBook > 0 ? 'text-coral' : 'text-emerald'}`}>
                {stats.wrongBook}
              </span>
              <span className="telemetry-unit">{stats.wrongBook > 0 ? 'PENDING' : 'CLEAR'}</span>
            </div>
            <span className="telemetry-lbl">错题待攻克</span>
            <span className={`telemetry-bar ${stats.wrongBook > 0 ? 'warn' : 'ok'}`}>
              <i style={{ width: `${stats.wrongBook > 0 ? Math.max(8, wrongPct) : 100}%` }} />
            </span>
          </div>

          <div className="telemetry-cell">
            <span className="telemetry-code">SIMULATION // 04</span>
            <div className="telemetry-val-row">
              <span className="telemetry-val text-sky">{state.mockHistory.length}</span>
              <span className="telemetry-unit">场 / {readyYears.length} 卷</span>
            </div>
            <span className="telemetry-lbl">已完成全真模考</span>
            <span className="telemetry-bar yellow">
              <i style={{ width: `${Math.max(state.mockHistory.length > 0 ? 10 : 0, mockPct)}%` }} />
            </span>
          </div>
        </div>
      </section>

      {/* System Broadcast Strip */}
      {latestAnnouncement && (
        <section className="broadcast-bar" aria-label="最新站点公告">
          <div className="broadcast-left">
            <Megaphone size={16} className="text-yellow" style={{ flexShrink: 0 }} />
            <span className="broadcast-tag">{latestAnnouncement.tag}</span>
            <div className="broadcast-copy">
              <strong className="broadcast-title">{latestAnnouncement.title}</strong>
              <span className="broadcast-summary">{latestAnnouncement.summary}</span>
            </div>
          </div>
          <div className="broadcast-actions">
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

      {/* De-Nested 5-Layer Architecture Map */}
      <section className="arch-section">
        <div className="section-head">
          <h2 className="section-title">复习体系作战图 · {currentCourse.shortLabel}</h2>
          <span className="section-hint">
            {readyYears.length > 0
              ? `ONLINE ${readyYears.length} SETS // ${stats.total} QUESTIONS${
                  plannedYears.length > 0 ? ` (+${plannedYears.length} PLANNED)` : ''
                }`
              : `SYLLABUS ${chapters.length} CH // ${formulas.length} FORMULAS`}
          </span>
        </div>

        <div className="arch-stack">
          {/* Layer 01: Live Year Dossier Pool */}
          <div className="arch-group">
            <div className="arch-group-head">
              <div className="arch-layer-tag">
                <span className="arch-layer-num">01</span>
                <span>底座 · 历年真题档案池（已上线 {readyYears.length} 套 / 共 {yearsMeta.length} 套）</span>
              </div>
              {yearsMeta.length > 6 && (
                <Link to="/year" className="btn-inline-link">
                  查看全部 {yearsMeta.length} 套真题 →
                </Link>
              )}
            </div>

            <div className="arch-cards-grid cols-3">
              {yearsMeta.slice(0, 6).map((ym) => {
                const isReady = ym.status === 'ready';
                const paper = papersByYear[ym.year];
                const qs = paper?.questions ?? [];
                let mCnt = 0;
                let pCnt = 0;
                let wCnt = 0;
                for (const q of qs) {
                  const st = getRecord(q.id).status;
                  if (st === 'mastered') mCnt++;
                  else if (st === 'partial') pCnt++;
                  else if (st === 'wrong') wCnt++;
                }
                const doneCnt = mCnt + pCnt + wCnt;
                const totalCnt = qs.length || ym.questionCount || 1;
                const yrMasteryPct = qs.length > 0 ? Math.round((mCnt / qs.length) * 100) : 0;
                const bestMock = bestMockByYear[ym.year];

                return (
                  <Link
                    key={ym.year}
                    to={isReady ? `/year?year=${ym.year}` : '/year'}
                    className={`year-dossier-card ${!isReady ? 'muted-card' : ''}`}
                  >
                    <span className="year-dossier-wm" aria-hidden="true">
                      {ym.year}
                    </span>
                    <div className="year-dossier-head">
                      <span className="year-dossier-num">
                        {ym.year} <small style={{ fontSize: '0.72rem', fontWeight: 600 }}>真题卷</small>
                      </span>
                      <span className={`status-chip ${isReady ? 'ready' : 'planned'}`}>
                        {isReady ? 'ONLINE' : 'PENDING'}
                      </span>
                    </div>

                    <div className="year-dossier-meta">
                      <span>{ym.questionCount} 题</span>
                      <span>·</span>
                      <span>满分 {ym.totalScore} 分</span>
                      {bestMock && (
                        <>
                          <span>·</span>
                          <span className="text-sky">
                            模考最高 {bestMock.score}/{bestMock.max}
                          </span>
                        </>
                      )}
                    </div>

                    <div className="year-dossier-foot">
                      <div className="progress-bar-track">
                        <div className="progress-seg mastered" style={{ width: `${(mCnt / totalCnt) * 100}%` }} />
                        <div className="progress-seg partial" style={{ width: `${(pCnt / totalCnt) * 100}%` }} />
                        <div className="progress-seg wrong" style={{ width: `${(wCnt / totalCnt) * 100}%` }} />
                      </div>
                      <div className="year-dossier-stat">
                        <span>
                          已练 {doneCnt}/{qs.length || ym.questionCount}
                        </span>
                        <span>掌握 {yrMasteryPct}%</span>
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Layer 02 & 03: Orthogonal Axes */}
          <div className="arch-dual-row">
            <div className="arch-group">
              <div className="arch-group-head">
                <div className="arch-layer-tag">
                  <span className="arch-layer-num">02</span>
                  <span>轴一 · 按考纲章节体系</span>
                </div>
                <span className="hud-code">AXIS-A // SYLLABUS</span>
              </div>
              <div className="arch-cards-grid cols-2">
                <Link to="/chapters" className="arch-card accent-cyan">
                  <div className="arch-card-top">
                    <span className="arch-card-title">{chapters.length} 章考纲练习</span>
                    <Layers size={16} className="text-sky" />
                  </div>
                  <p className="arch-card-desc">
                    围绕「{currentCourse.shortLabel}」重点章节与分值比重，定向突破薄弱板块。
                  </p>
                </Link>
                <Link to="/dashboard" className="arch-card accent-cyan">
                  <div className="arch-card-top">
                    <span className="arch-card-title">命题结构大盘</span>
                    <BarChart3 size={16} className="text-sky" />
                  </div>
                  <p className="arch-card-desc">
                    历年真题实考分值热力矩阵同屏对照，锁定高性价比大题重镇。
                  </p>
                </Link>
              </div>
            </div>

            <div className="arch-group">
              <div className="arch-group-head">
                <div className="arch-layer-tag">
                  <span className="arch-layer-num">03</span>
                  <span>轴二 · 按通用解题方法</span>
                </div>
                <span className="hud-code">AXIS-B // METHOD</span>
              </div>
              <div className="arch-cards-grid cols-2">
                <Link to="/methods" className="arch-card accent-purple">
                  <div className="arch-card-top">
                    <span className="arch-card-title">解题方法库 ({stats.uniqueMethods} 种)</span>
                    <Compass size={16} className="text-purple" />
                  </div>
                  <p className="arch-card-desc">
                    跳出章节壁垒，将历年高频同类设问归纳为标准破题流程集中训练。
                  </p>
                </Link>
                <Link to="/practice?type=calc" className="arch-card accent-purple">
                  <div className="arch-card-top">
                    <span className="arch-card-title">计算与推导大题专练</span>
                    <ArrowRight size={16} className="text-purple" />
                  </div>
                  <p className="arch-card-desc">
                    专攻高分值计算与推导大题，配套分步采分点规范考场书写步骤。
                  </p>
                </Link>
              </div>
            </div>
          </div>

          {/* Layer 04 & 05: Closed-Loop & Exam Tools */}
          <div className="arch-dual-row">
            <div className="arch-group">
              <div className="arch-group-head">
                <div className="arch-layer-tag">
                  <span className="arch-layer-num">04</span>
                  <span>闭环 · 错题诊断与掌握追踪</span>
                </div>
                <span className="hud-code">LOOP // DIAGNOSTICS</span>
              </div>
              <div className="arch-cards-grid cols-2">
                <Link to="/wrong-book" className="arch-card accent-emerald">
                  <div className="arch-card-top">
                    <span className="arch-card-title">错题本 & 私人笔记</span>
                    <BookMarked size={16} className="text-coral" />
                  </div>
                  <p className="arch-card-desc">
                    判错与自评「不会 / 半会」自动归档，支持分板块独立斩题与笔记沉淀。
                  </p>
                </Link>
                <Link to="/progress" className="arch-card accent-emerald">
                  <div className="arch-card-top">
                    <span className="arch-card-title">掌握度热力图</span>
                    <CheckCircle2 size={16} className="text-emerald" />
                  </div>
                  <p className="arch-card-desc">
                    分年份折叠矩阵与章节掌握进度条，完整记录做题流水与折算得分。
                  </p>
                </Link>
              </div>
            </div>

            <div className="arch-group">
              <div className="arch-group-head">
                <div className="arch-layer-tag">
                  <span className="arch-layer-num">05</span>
                  <span>工具 · 考场模拟与公式背诵</span>
                </div>
                <span className="hud-code">TOOLS // COMBAT</span>
              </div>
              <div className="arch-cards-grid cols-2">
                <Link to="/mock" className="arch-card accent-yellow">
                  <div className="arch-card-top">
                    <span className="arch-card-title">整卷限时模考</span>
                    <Timer size={16} className="text-amber" />
                  </div>
                  <p className="arch-card-desc">
                    180 分钟全真计时、分段答题卡、交卷秒判 + 采分点自评生成评级报告。
                  </p>
                </Link>
                <Link to="/formulas" className="arch-card accent-yellow">
                  <div className="arch-card-top">
                    <span className="arch-card-title">公式速记手册 ({formulas.length} 组)</span>
                    <FileSpreadsheet size={16} className="text-amber" />
                  </div>
                  <p className="arch-card-desc">
                    整理本科目核心必背方程、量纲与边界，支持精读与 3D 翻面闪卡抽背。
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
