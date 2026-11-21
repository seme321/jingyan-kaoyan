import React, { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, CheckCircle2, ChevronDown, ChevronRight, Clock, Grid } from 'lucide-react';
import { useData } from '../context/DataContext';
import { useStudy } from '../context/StudyContext';
import { MathText } from '../components/MathText';

export const ProgressPage: React.FC = () => {
  const { currentCourse, allQuestions, questionsById, chapters } = useData();
  const { state, getRecord } = useStudy();
  const activeYears = useMemo(
    () => Array.from(new Set(allQuestions.map((q) => q.year))).sort((a, b) => b - a),
    [allQuestions]
  );

  const [expandedYears, setExpandedYears] = useState<Record<number, boolean>>({});
  const [expandAll, setExpandAll] = useState(false);

  const isYearOpen = (yr: number, idx: number) => {
    if (yr in expandedYears) return expandedYears[yr];
    return expandAll || idx < 3;
  };

  const toggleYear = (yr: number, idx: number) => {
    const cur = isYearOpen(yr, idx);
    setExpandedYears((prev) => ({ ...prev, [yr]: !cur }));
  };

  const handleToggleAll = () => {
    const next = !expandAll;
    setExpandAll(next);
    setExpandedYears({});
  };

  const summary = useMemo(() => {
    let mastered = 0;
    let partial = 0;
    let wrong = 0;
    let unseen = 0;
    let masteredScore = 0;
    const totalScore = allQuestions.reduce((s, q) => s + q.score, 0);

    for (const q of allQuestions) {
      const st = getRecord(q.id).status;
      if (st === 'mastered') {
        mastered++;
        masteredScore += q.score;
      } else if (st === 'partial') {
        partial++;
        masteredScore += Math.round(q.score * 0.5);
      } else if (st === 'wrong') {
        wrong++;
      } else {
        unseen++;
      }
    }
    return { mastered, partial, wrong, unseen, masteredScore, totalScore };
  }, [allQuestions, getRecord]);

  return (
    <div className="page-container">
      <div className="page-header-card">
        <div className="page-kicker">TELEMETRY // MASTERY MATRIX</div>
        <h1 className="page-title">
          <Activity size={22} className="text-emerald" /> {currentCourse.shortLabel} · 复习进度与掌握热力图
        </h1>
        <p className="page-desc">
          全方位追踪「{currentCourse.name}」共 {allQuestions.length} 道真题掌握矩阵、折算分值与做题流水
        </p>

        <div className="progress-kpi-grid">
          <div className="kpi-card c-emerald">
            <span className="hud-code">MASTERED</span>
            <span className="kpi-val text-emerald">{summary.mastered} 题</span>
            <span className="kpi-lbl">已完全掌握</span>
          </div>
          <div className="kpi-card c-yellow">
            <span className="hud-code">PARTIAL</span>
            <span className="kpi-val text-amber">{summary.partial} 题</span>
            <span className="kpi-lbl">半会待巩固</span>
          </div>
          <div className="kpi-card c-coral">
            <span className="hud-code">ERRATA</span>
            <span className="kpi-val text-coral">{summary.wrong} 题</span>
            <span className="kpi-lbl">未掌握 / 错题</span>
          </div>
          <div className="kpi-card c-cyan">
            <span className="hud-code">ESTIMATED SCORE</span>
            <span className="kpi-val text-sky">
              {summary.masteredScore} / {summary.totalScore}
            </span>
            <span className="kpi-lbl">当前掌握折算分值</span>
          </div>
        </div>
      </div>

      {/* Collapsible Multi-Year Compact Heatmap Matrix */}
      <div className="card-panel">
        <div className="panel-head-flex">
          <h3 className="panel-title">
            <Grid size={18} className="text-sky" /> 历年真题逐题掌握矩阵（点击题号直达精练）
          </h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.8rem' }}>
            <div className="palette-legend" style={{ paddingTop: 0, borderTop: 'none' }}>
              <span><i className="dot mastered" /> 已掌握</span>
              <span><i className="dot partial" /> 半会</span>
              <span><i className="dot wrong" /> 错题</span>
              <span><i className="dot" /> 未刷</span>
            </div>
            {activeYears.length > 3 && (
              <button type="button" className="btn btn-secondary btn-sm" onClick={handleToggleAll}>
                {expandAll ? '仅展开近 3 年' : `展开全部 ${activeYears.length} 年`}
              </button>
            )}
          </div>
        </div>

        {activeYears.length === 0 ? (
          <p className="muted-empty">当前板块暂未导入真题，导入后自动生成逐题热力图。</p>
        ) : (
          activeYears.map((yr, idx) => {
            const yrQs = allQuestions.filter((q) => q.year === yr);
            const open = isYearOpen(yr, idx);
            let mCnt = 0;
            let pCnt = 0;
            let wCnt = 0;
            for (const q of yrQs) {
              const st = getRecord(q.id).status;
              if (st === 'mastered') mCnt++;
              else if (st === 'partial') pCnt++;
              else if (st === 'wrong') wCnt++;
            }
            const pct = yrQs.length > 0 ? Math.round((mCnt / yrQs.length) * 100) : 0;

            return (
              <div key={yr} className="year-heatmap-block">
                <button
                  type="button"
                  className="year-heatmap-head"
                  onClick={() => toggleYear(yr, idx)}
                  aria-expanded={open}
                >
                  <span className="year-hm-title">
                    {open ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
                    {yr} 年真题（{yrQs.length} 题）
                  </span>
                  <span className="year-hm-summary">
                    <span className="text-emerald">掌握 {mCnt}</span>
                    <span>·</span>
                    <span>掌握率 {pct}%</span>
                    <span className="mini-bar" style={{ width: '72px' }}>
                      <div style={{ width: `${pct}%`, background: 'var(--emerald)' }} />
                    </span>
                  </span>
                </button>

                {open && (
                  <div className="heatmap-grid">
                    {yrQs.map((q) => {
                      const rec = getRecord(q.id);
                      return (
                        <Link
                          key={q.id}
                          to={`/practice?qid=${q.id}`}
                          className={`heatmap-cell status-${rec.status}`}
                          title={`${q.year} 第 ${q.no} 题 (${q.score}分)：${q.title}`}
                        >
                          <span className="hm-no">T{q.no}</span>
                          <span className="hm-pts">{q.score}分</span>
                        </Link>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Chapter Mastery Bars */}
      <div className="card-panel">
        <h3 className="panel-title">
          <CheckCircle2 size={18} className="text-emerald" /> {chapters.length} 个考纲章节掌握度进度条
        </h3>
        <div className="ch-bars-list">
          {chapters.map((ch) => {
            const qs = allQuestions.filter((q) => q.chapter === ch.chapter);
            const mCount = qs.filter((q) => getRecord(q.id).status === 'mastered').length;
            const pCount = qs.filter((q) => getRecord(q.id).status === 'partial').length;
            const wCount = qs.filter((q) => getRecord(q.id).status === 'wrong').length;
            const total = qs.length || 1;
            return (
              <div key={ch.chapter} className="ch-bar-row">
                <Link to={`/practice?chapter=${ch.chapter}`} className="ch-bar-name">
                  <span className="hud-code" style={{ marginRight: '0.4rem' }}>
                    CH.{String(ch.chapter).padStart(2, '0')}
                  </span>
                  {ch.name}
                </Link>
                <div className="progress-bar-track">
                  <div className="progress-seg mastered" style={{ width: `${(mCount / total) * 100}%` }} />
                  <div className="progress-seg partial" style={{ width: `${(pCount / total) * 100}%` }} />
                  <div className="progress-seg wrong" style={{ width: `${(wCount / total) * 100}%` }} />
                </div>
                <span className="ch-bar-stat">
                  {mCount}/{qs.length} 掌握
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent Practice Log */}
      <div className="card-panel">
        <h3 className="panel-title">
          <Clock size={18} className="text-sky" /> LOGS // 最近做题流水
        </h3>
        {state.practiceLogs.length === 0 ? (
          <p className="muted-empty">暂无做题流水，开始刷第一道题后自动记录。</p>
        ) : (
          <ul className="log-timeline">
            {state.practiceLogs.slice(0, 25).map((log) => {
              const q = questionsById[log.qid];
              if (!q) return null;
              return (
                <li key={log.id} className="log-item">
                  <span className="log-time">
                    {new Date(log.timestamp).toLocaleString('zh-CN', {
                      month: '2-digit',
                      day: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                  <span className={`q-status ${log.result}`}>
                    {log.result === 'mastered' ? '掌握' : log.result === 'partial' ? '半会' : '错题'}
                  </span>
                  <Link to={`/practice?qid=${q.id}`} className="log-q-link">
                    [{q.year}·T{q.no}] <MathText text={q.title} inline />
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
};
