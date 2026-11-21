import React, { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  AlertCircle,
  Award,
  Check,
  CheckCircle2,
  Clock,
  Flag,
  Pause,
  Play,
  Send,
  Timer,
  X,
} from 'lucide-react';
import { useData } from '../context/DataContext';
import { useStudy } from '../context/StudyContext';
import { Mascot } from '../components/Mascot';
import { MathText } from '../components/MathText';
import { FigureGallery } from '../components/FigureGallery';
import { scrollToElement } from '../utils/scroll';
import type { ActiveMockSession, MockAttempt, Question, SectionScoreSummary } from '../types';

function formatSeconds(sec: number): string {
  const s = Math.max(0, sec);
  const hh = Math.floor(s / 3600);
  const mm = Math.floor((s % 3600) / 60);
  const ss = s % 60;
  return `${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}`;
}

function getScoreStepPresets(maxPts: number): number[] {
  if (maxPts <= 3) {
    const arr: number[] = [];
    for (let p = maxPts; p >= 0; p--) arr.push(p);
    return arr;
  }
  const presets = new Set<number>([
    maxPts,
    Math.round(maxPts * 0.8),
    Math.round(maxPts * 0.5),
    Math.round(maxPts * 0.25),
    0,
  ]);
  return Array.from(presets).sort((a, b) => b - a);
}

function getRankGrade(pct: number): { rank: string; label: string } {
  if (pct >= 90) return { rank: 'S', label: 'TOP CLEAR' };
  if (pct >= 80) return { rank: 'A', label: 'EXCELLENT' };
  if (pct >= 70) return { rank: 'B', label: 'SOLID PASS' };
  if (pct >= 60) return { rank: 'C', label: 'QUALIFIED' };
  return { rank: 'D', label: 'RETRAIN' };
}

export const MockPage: React.FC = () => {
  const { currentCourse, yearsMeta, papersByYear, chapterMap } = useData();
  const { state, setActiveMock, saveMockAttempt, recordAttempt, trackQuestionReviewed } = useStudy();
  const [searchParams, setSearchParams] = useSearchParams();

  const readyYears = useMemo(
    () => yearsMeta.filter((ym) => ym.status === 'ready'),
    [yearsMeta]
  );
  const firstReady = readyYears[0]?.year ?? 0;
  const urlYearParam = Number(searchParams.get('year')) || 0;
  const selectedYear =
    urlYearParam && papersByYear[urlYearParam]
      ? urlYearParam
      : state.activeMock?.year && papersByYear[state.activeMock.year]
        ? state.activeMock.year
        : firstReady;

  const paper = papersByYear[selectedYear];

  const [paused, setPaused] = useState(false);
  const [finishedAttempt, setFinishedAttempt] = useState<MockAttempt | null>(null);

  useEffect(() => {
    if (urlYearParam && !papersByYear[urlYearParam] && firstReady) {
      setSearchParams({ year: String(firstReady) }, { replace: true });
    }
  }, [urlYearParam, papersByYear, firstReady, setSearchParams]);

  useEffect(() => {
    setFinishedAttempt(null);
    setPaused(false);
  }, [currentCourse.id]);

  const session = state.activeMock?.year === paper?.year ? state.activeMock : null;

  useEffect(() => {
    if (!session || session.phase !== 'answering' || paused) return;
    const id = window.setInterval(() => {
      setActiveMock((prev) =>
        prev && prev.phase === 'answering'
          ? { ...prev, elapsedSeconds: prev.elapsedSeconds + 1 }
          : prev
      );
    }, 1000);
    return () => window.clearInterval(id);
  }, [session?.year, session?.phase, paused, setActiveMock]);

  const startNewMock = () => {
    if (!paper) return;
    const fresh: ActiveMockSession = {
      year: paper.year,
      startedAt: Date.now(),
      elapsedSeconds: 0,
      phase: 'answering',
      judgeChoices: {},
      choiceAnswers: {},
      textAnswers: {},
      flagged: {},
      selfScores: {},
      rubricChecks: {},
    };
    setFinishedAttempt(null);
    setPaused(false);
    setActiveMock(fresh);
  };

  const enterGradingPhase = () => {
    if (!paper || !session) return;
    const initialScores: Record<string, number> = {};
    const initialRubrics: Record<string, boolean[]> = {};

    for (const q of paper.questions) {
      if (q.type === 'judge') {
        const picked = session.judgeChoices[q.id];
        const hasAns = picked !== undefined && picked !== null;
        if (hasAns) trackQuestionReviewed(q.id);
        initialScores[q.id] = hasAns && picked === q.judgeAnswer ? q.score : 0;
      } else if (q.type === 'single_choice') {
        const picked = (session.choiceAnswers?.[q.id] ?? '').trim().toUpperCase();
        const ans = (q.choiceAnswer ?? '').trim().toUpperCase();
        if (picked) trackQuestionReviewed(q.id);
        initialScores[q.id] = picked && picked === ans ? q.score : 0;
      } else if (q.rubric && q.rubric.length > 0) {
        if ((session.textAnswers[q.id] ?? '').trim()) trackQuestionReviewed(q.id);
        initialRubrics[q.id] = q.rubric.map(() => false);
        initialScores[q.id] = 0;
      } else {
        const txt = (session.textAnswers[q.id] ?? '').trim();
        if (txt) trackQuestionReviewed(q.id);
        initialScores[q.id] = txt ? q.score : 0;
      }
    }

    setActiveMock({
      ...session,
      phase: 'grading',
      selfScores: initialScores,
      rubricChecks: initialRubrics,
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const toggleRubricItem = (qid: string, idx: number, rubricPts: number[]) => {
    if (!session) return;
    const cur = session.rubricChecks[qid] ?? rubricPts.map(() => false);
    const next = cur.map((v, i) => (i === idx ? !v : v));
    const sum = next.reduce((acc, checked, i) => acc + (checked ? rubricPts[i] : 0), 0);
    setActiveMock({
      ...session,
      rubricChecks: { ...session.rubricChecks, [qid]: next },
      selfScores: { ...session.selfScores, [qid]: sum },
    });
  };

  const finalizeMock = () => {
    if (!paper || !session) return;
    let totalScore = 0;
    const answersByQid: Record<string, string> = {};

    for (const q of paper.questions) {
      const sc = session.selfScores[q.id] ?? 0;
      totalScore += sc;
      if (q.type === 'judge') {
        const c = session.judgeChoices[q.id];
        answersByQid[q.id] = c === true ? '√' : c === false ? '×' : '未作答';
      } else if (q.type === 'single_choice') {
        answersByQid[q.id] = session.choiceAnswers?.[q.id] || '未作答';
      } else {
        answersByQid[q.id] = session.textAnswers[q.id] || '纸面作答';
      }

      if (sc >= q.score) recordAttempt(q.id, 'mastered');
      else if (sc > 0) recordAttempt(q.id, 'partial');
      else recordAttempt(q.id, 'wrong');
    }

    const sectionScores: SectionScoreSummary[] = paper.sections.map((sec) => {
      const secQs = paper.questions.filter((q) => q.no >= sec.range[0] && q.no <= sec.range[1]);
      const earned = secQs.reduce((sum, q) => sum + (session.selfScores[q.id] ?? 0), 0);
      return {
        id: sec.id,
        title: sec.title,
        earned,
        max: sec.totalScore,
      };
    });

    const attempt: MockAttempt = {
      id: `mock-${Date.now()}`,
      year: paper.year,
      startedAt: session.startedAt,
      submittedAt: Date.now(),
      elapsedSeconds: session.elapsedSeconds,
      totalScore,
      maxScore: paper.totalScore,
      sectionScores,
      scoresByQid: { ...session.selfScores },
      answersByQid,
    };

    saveMockAttempt(attempt);
    setFinishedAttempt(attempt);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const chapterBreakdown = useMemo(() => {
    if (!finishedAttempt || !paper) return [];
    const map = new Map<number, { earned: number; max: number; qCount: number }>();
    for (const q of paper.questions) {
      const cur = map.get(q.chapter) ?? { earned: 0, max: 0, qCount: 0 };
      cur.earned += finishedAttempt.scoresByQid[q.id] ?? 0;
      cur.max += q.score;
      cur.qCount += 1;
      map.set(q.chapter, cur);
    }
    return Array.from(map.entries()).sort((a, b) => a[0] - b[0]);
  }, [finishedAttempt, paper]);

  if (!paper) {
    return (
      <div className="page-container">
        <div className="empty-state-card">
          <Mascot pose="study" size={140} />
          <h3>「{currentCourse.name}」模考卷待导入</h3>
          <p>导入第一套真题 JSON 后即可开启 180 分钟全真限时模考与采分点自评。</p>
          <Link to="/formulas" className="btn btn-primary">
            先去背诵核心公式
          </Link>
        </div>
      </div>
    );
  }

  const remainingSec = session ? paper.durationMinutes * 60 - session.elapsedSeconds : paper.durationMinutes * 60;

  // 1. Tactical Rank Evaluation Scorecard View
  if (finishedAttempt) {
    const pct = Math.round((finishedAttempt.totalScore / finishedAttempt.maxScore) * 100);
    const { rank, label } = getRankGrade(pct);
    const secList = finishedAttempt.sectionScores ?? [];
    return (
      <div className="page-container reading-narrow">
        <div className="scorecard-hero">
          <Mascot pose={pct >= 60 ? 'cheer' : 'study'} size={146} float />
          <div className="scorecard-badge">
            <Award size={16} /> EVALUATION REPORT // {finishedAttempt.year} · {currentCourse.shortLabel}
          </div>

          <div className="scorecard-rank-row">
            <div className="scorecard-rank-stamp">
              <strong>{rank}</strong>
              <span>{label}</span>
            </div>
            <div className="scorecard-main-num">
              <strong>{finishedAttempt.totalScore}</strong>
              <span>/ {finishedAttempt.maxScore} 分</span>
            </div>
          </div>

          <p className="scorecard-sub">
            得分率 {pct}% · 用时 {formatSeconds(finishedAttempt.elapsedSeconds)} ·
            失分题已自动同步至错题本与掌握度记录
          </p>

          {secList.length > 0 && (
            <div
              className="scorecard-sections-row"
              style={{ gridTemplateColumns: `repeat(${Math.min(secList.length, 4)}, minmax(0, 1fr))` }}
            >
              {secList.map((sec) => (
                <div key={sec.id} className="sc-box">
                  <span>{sec.title}</span>
                  <strong>
                    {sec.earned} / {sec.max}
                  </strong>
                </div>
              ))}
            </div>
          )}

          <div className="hero-cta-row" style={{ justifyContent: 'center' }}>
            <Link to="/wrong-book" className="btn btn-tactical">
              前往错题本复盘失分题
            </Link>
            <button type="button" className="btn btn-secondary" onClick={() => setFinishedAttempt(null)}>
              返回模考中心
            </button>
          </div>
        </div>

        <div className="card-panel">
          <h3 className="panel-title">CHAPTER DIAGNOSTICS // 各章节得分诊断</h3>
          <div className="diag-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>章节</th>
                  <th>题数</th>
                  <th>得分 / 满分</th>
                  <th>得分率</th>
                </tr>
              </thead>
              <tbody>
                {chapterBreakdown.map(([ch, d]) => {
                  const rate = Math.round((d.earned / d.max) * 100);
                  return (
                    <tr key={ch}>
                      <td>
                        第 {ch} 章 · {chapterMap[ch]?.name}
                      </td>
                      <td>{d.qCount} 题</td>
                      <td>
                        <strong>{d.earned}</strong> / {d.max} 分
                      </td>
                      <td>
                        <div className="inline-bar-cell">
                          <div className="mini-bar">
                            <div style={{ width: `${rate}%` }} />
                          </div>
                          <span className="font-mono">{rate}%</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }

  // 2. Lobby View
  if (!session) {
    return (
      <div className="page-container reading-narrow">
        <div className="mock-lobby-card">
          <Mascot pose="study" size={146} float />
          <div className="mock-lobby-badge">
            <Timer size={16} /> SIMULATION CHAMBER // 考场全真模拟
          </div>

          {readyYears.length > 1 && (
            <div className="seg-group mock-year-selector" style={{ marginBottom: '1rem' }}>
              {readyYears.map((ym) => (
                <button
                  key={ym.year}
                  type="button"
                  className={`seg-btn ${selectedYear === ym.year ? 'active' : ''}`}
                  onClick={() => setSearchParams({ year: String(ym.year) }, { replace: true })}
                >
                  {ym.year} 卷
                </button>
              ))}
            </div>
          )}

          {state.activeMock &&
            state.activeMock.year !== paper.year &&
            papersByYear[state.activeMock.year] && (
              <div className="mock-active-banner">
                <span>
                  当前有未交卷的 {state.activeMock.year} 年模拟考场（已用时{' '}
                  {formatSeconds(state.activeMock.elapsedSeconds)}）
                </span>
                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  onClick={() =>
                    setSearchParams({ year: String(state.activeMock!.year) }, { replace: true })
                  }
                >
                  返回 {state.activeMock.year} 考场
                </button>
              </div>
            )}

          <h1 className="page-title" style={{ justifyContent: 'center', fontSize: '1.6rem' }}>
            {paper.year} 年{paper.school} {paper.code} {paper.subject}整卷模考
          </h1>
          <p className="hero-subtitle" style={{ textAlign: 'center', marginBottom: '1.1rem' }}>
            严格复刻考场节奏：满分 <strong>{paper.totalScore} 分</strong> · 限时{' '}
            <strong>{paper.durationMinutes} 分钟</strong>
            {!paper.calculatorAllowed && (
              <>
                {' '}
                · <strong>禁用计算器</strong>
              </>
            )}
          </p>

          <div className="mock-rules-box">
            {paper.examNotes.map((note, idx) => (
              <div key={idx} className="rule-item">
                {idx === 0 ? (
                  <AlertCircle size={16} className="text-amber" style={{ flexShrink: 0, marginTop: 2 }} />
                ) : (
                  <CheckCircle2 size={16} className="text-emerald" style={{ flexShrink: 0, marginTop: 2 }} />
                )}
                <MathText text={note} inline />
              </div>
            ))}
          </div>

          <button type="button" className="btn btn-tactical btn-lg" onClick={startNewMock}>
            <Play size={17} /> 启动 {paper.durationMinutes} 分钟全真计时模考
          </button>
        </div>

        {state.mockHistory.length > 0 && (
          <div className="card-panel">
            <h3 className="panel-title">HISTORY // 「{currentCourse.shortLabel}」历次模考成绩记录</h3>
            <div className="diag-table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>交卷时间</th>
                    <th>试卷</th>
                    <th>总成绩</th>
                    <th>分项得分</th>
                    <th>耗时</th>
                  </tr>
                </thead>
                <tbody>
                  {state.mockHistory.map((m) => (
                    <tr key={m.id}>
                      <td className="font-mono">{new Date(m.submittedAt).toLocaleString('zh-CN')}</td>
                      <td>{m.year} 真题</td>
                      <td className="font-mono">
                        <strong className="text-sky">{m.totalScore}</strong> / {m.maxScore} 分
                      </td>
                      <td className="font-mono">
                        {m.sectionScores
                          ? m.sectionScores.map((s) => `${s.earned}/${s.max}`).join(' · ')
                          : `${m.judgeScore ?? 0} / ${m.fillScore ?? 0} / ${m.calcScore ?? 0}`}
                      </td>
                      <td className="font-mono">{formatSeconds(m.elapsedSeconds)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  }

  // 3. Self-Grading Phase
  if (session.phase === 'grading') {
    const runningTotal = Object.values(session.selfScores).reduce((a, b) => a + b, 0);
    return (
      <div className="page-container reading-narrow">
        <div className="mock-sticky-bar grading-mode">
          <div className="mock-grading-meta">
            <strong>GRADING // 交卷自评与采分点核分</strong>
            <span className="grading-sub">
              当前累计：
              <strong className="text-yellow font-mono">
                {' '}
                {runningTotal} / {paper.totalScore} 分
              </strong>
            </span>
            <span className="ai-gen-notice">AI 辅助精解与自拟采分点 · 仅供学习参考</span>
          </div>
          <button type="button" className="btn btn-tactical btn-sm" onClick={finalizeMock}>
            <CheckCircle2 size={15} /> 完成核分 · 生成报告
          </button>
        </div>

        <div className="question-stack">
          {paper.questions.map((q: Question) => {
            const curScore = session.selfScores[q.id] ?? 0;
            const userJudge = session.judgeChoices[q.id];
            const userChoice = session.choiceAnswers?.[q.id] ?? '';
            const userTxt = session.textAnswers[q.id] ?? '';
            const isAutoObjective = q.type === 'judge' || q.type === 'single_choice';

            return (
              <div key={q.id} className="q-card grading-card">
                <div className="q-card-header">
                  <div className="q-meta-left">
                    <span className="q-no-badge">T{String(q.no).padStart(2, '0')}</span>
                    <span className="q-score-badge">满分 {q.score} 分</span>
                    <MathText text={q.title} inline className="grading-q-title" />
                  </div>
                  <div className="grading-score-pill">本题得分：{curScore} 分</div>
                </div>

                <div className="grading-compare-grid">
                  <div className="grading-user-box">
                    <span className="grading-box-lbl">YOUR ANSWER // 你的考场作答</span>
                    <div>
                      {q.type === 'judge'
                        ? userJudge === true
                          ? '正确（√）'
                          : userJudge === false
                            ? '错误（×）'
                            : '未作答'
                        : q.type === 'single_choice'
                          ? userChoice || '未作答'
                          : userTxt || '（纸面作答 / 未填）'}
                    </div>
                  </div>
                  <div className="grading-std-box">
                    <span className="grading-box-lbl">REFERENCE // 标准参考答案</span>
                    <MathText text={q.answer} />
                  </div>
                </div>

                {isAutoObjective ? (
                  <div className={`judge-auto-tag ${curScore > 0 ? 'ok' : 'err'}`}>
                    {curScore > 0 ? `✓ 系统自动判分：+${q.score} 分` : '✗ 系统自动判分：0 分'}
                  </div>
                ) : q.rubric && q.rubric.length > 0 ? (
                  <div className="calc-rubric-grader">
                    <div className="sol-section-label">勾选做对的步骤采分点（自动累加得分）：</div>
                    <div className="rubric-check-list">
                      {q.rubric.map((r, idx) => {
                        const checked = session.rubricChecks[q.id]?.[idx] ?? false;
                        const ptsArr = q.rubric!.map((x) => x.pts);
                        return (
                          <label key={idx} className={`rubric-check-row ${checked ? 'checked' : ''}`}>
                            <input
                              type="checkbox"
                              checked={checked}
                              onChange={() => toggleRubricItem(q.id, idx, ptsArr)}
                            />
                            <span className="rubric-pts">+{r.pts}分</span>
                            <MathText text={r.label} inline />
                          </label>
                        );
                      })}
                    </div>
                  </div>
                ) : (
                  <div className="fill-score-selector">
                    <span>对照答案赋分：</span>
                    <div className="seg-group">
                      {getScoreStepPresets(q.score).map((pts) => (
                        <button
                          key={pts}
                          type="button"
                          className={`seg-btn ${curScore === pts ? 'active' : ''}`}
                          onClick={() =>
                            setActiveMock({
                              ...session,
                              selfScores: { ...session.selfScores, [q.id]: pts },
                            })
                          }
                        >
                          {pts} 分
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {q.analysis && (
                  <details className="grading-details" style={{ marginTop: '0.7rem' }}>
                    <summary>展开完整规范推导与解析图核对过程</summary>
                    <div className="sol-detail-box" style={{ marginTop: '0.65rem' }}>
                      <div className="sol-section-label-row">
                        <div className="sol-section-label">DERIVATION // 规范推导与解析核对</div>
                        <span className="ai-gen-notice">AI 辅助精解与自拟采分点 · 仅供学习参考</span>
                      </div>
                      <MathText text={q.analysis} />
                      {q.analysisFigures.length > 0 && (
                        <FigureGallery figures={q.analysisFigures} variant="solution" />
                      )}
                    </div>
                  </details>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // 4. Live Answering Phase (Tactical HUD + Sectioned Answer Sheet)
  const answeredCount = paper.questions.filter((q) => {
    if (q.type === 'judge') {
      return session.judgeChoices[q.id] !== undefined && session.judgeChoices[q.id] !== null;
    }
    if (q.type === 'single_choice') {
      return Boolean(session.choiceAnswers?.[q.id]);
    }
    return Boolean((session.textAnswers[q.id] ?? '').trim());
  }).length;

  const answeredPct = paper.questions.length > 0 ? Math.round((answeredCount / paper.questions.length) * 100) : 0;
  const timerTone = remainingSec < 900 ? 'urgent' : remainingSec < 1800 ? 'warn' : '';

  return (
    <div className="page-container">
      <div className="mock-sticky-bar">
        <div className="mock-timer-left">
          <Clock
            size={18}
            className={timerTone === 'urgent' ? 'text-coral' : timerTone === 'warn' ? 'text-yellow' : 'text-sky'}
          />
          <span className={`timer-digits ${timerTone}`}>
            {remainingSec >= 0 ? formatSeconds(remainingSec) : `超时 ${formatSeconds(-remainingSec)}`}
          </span>
          <span className="mock-progress-tag">
            已答 {answeredCount} / {paper.questions.length} ({answeredPct}%)
          </span>
          {!paper.calculatorAllowed && <span className="no-calc-chip">禁用计算器</span>}
        </div>

        <div className="mock-bar-actions">
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => setPaused((p) => !p)}>
            {paused ? <Play size={14} /> : <Pause size={14} />}
            {paused ? '继续计时' : '暂停'}
          </button>
          <button
            type="button"
            className="btn btn-ghost-danger btn-sm"
            onClick={() => setActiveMock(null)}
          >
            放弃本场
          </button>
          <button type="button" className="btn btn-tactical btn-sm" onClick={enterGradingPhase}>
            <Send size={14} /> 交卷判分
          </button>
        </div>

        <div className="mock-hud-progress">
          <i style={{ width: `${answeredPct}%` }} />
        </div>
      </div>

      <div className="mock-layout">
        <div className="mock-questions-col">
          {paper.questions.map((q) => {
            const isFlagged = Boolean(session.flagged[q.id]);
            const jVal = session.judgeChoices[q.id];
            const cVal = session.choiceAnswers?.[q.id] ?? '';
            const tVal = session.textAnswers[q.id] ?? '';

            return (
              <article key={q.id} id={`mock-q-${q.no}`} className="q-card">
                <div className="q-card-header">
                  <div className="q-meta-left">
                    <span className="q-no-badge">T{String(q.no).padStart(2, '0')}</span>
                    <span className="q-score-badge">{q.score} 分</span>
                  </div>
                  <button
                    type="button"
                    className={`flag-btn ${isFlagged ? 'flagged' : ''}`}
                    onClick={() =>
                      setActiveMock({
                        ...session,
                        flagged: { ...session.flagged, [q.id]: !isFlagged },
                      })
                    }
                  >
                    <Flag size={13} /> {isFlagged ? '已标待查' : '标记待查'}
                  </button>
                </div>

                {q.note && (
                  <div className="q-calc-const-note">
                    <MathText text={q.note} inline />
                  </div>
                )}

                <div className="q-stem-body">
                  <MathText text={q.stem} />
                </div>

                {q.figures.length > 0 && <FigureGallery figures={q.figures} variant="exam" />}

                {q.type === 'judge' ? (
                  <div className="mock-judge-row">
                    <button
                      type="button"
                      className={`mock-judge-btn ${jVal === true ? 'active' : ''}`}
                      onClick={() =>
                        setActiveMock({
                          ...session,
                          judgeChoices: { ...session.judgeChoices, [q.id]: true },
                        })
                      }
                    >
                      <Check size={16} /> 正确（√）
                    </button>
                    <button
                      type="button"
                      className={`mock-judge-btn ${jVal === false ? 'active' : ''}`}
                      onClick={() =>
                        setActiveMock({
                          ...session,
                          judgeChoices: { ...session.judgeChoices, [q.id]: false },
                        })
                      }
                    >
                      <X size={16} /> 错误（×）
                    </button>
                  </div>
                ) : q.type === 'single_choice' && q.options ? (
                  <div className="choice-options-grid interactive" style={{ marginTop: '0.85rem' }}>
                    {q.options.map((opt) => (
                      <button
                        key={opt.label}
                        type="button"
                        className={`choice-opt-btn ${
                          cVal.trim().toUpperCase() === opt.label.trim().toUpperCase() ? 'selected' : ''
                        }`}
                        onClick={() =>
                          setActiveMock({
                            ...session,
                            choiceAnswers: { ...(session.choiceAnswers ?? {}), [q.id]: opt.label },
                          })
                        }
                      >
                        <span className="opt-badge">{opt.label}</span>
                        <MathText text={opt.text} inline />
                      </button>
                    ))}
                  </div>
                ) : (
                  <textarea
                    className="draft-textarea"
                    style={{ marginTop: '0.85rem', maxWidth: 'var(--reading-max)' }}
                    rows={['calc', 'proof', 'short'].includes(q.type) ? 3 : 2}
                    placeholder={
                      ['calc', 'proof'].includes(q.type)
                        ? '在演算纸写出完整推导后，在此录入最终得数（或填“已纸面作答”）以便交卷核分…'
                        : '输入本题答案或简答要点…'
                    }
                    value={tVal}
                    onChange={(e) =>
                      setActiveMock({
                        ...session,
                        textAnswers: { ...session.textAnswers, [q.id]: e.target.value },
                      })
                    }
                  />
                )}
              </article>
            );
          })}
        </div>

        {/* Sectioned Tactical Answer Sheet Palette */}
        <aside className="mock-palette">
          <div className="palette-title">
            <span>答题卡导航</span>
            <span className="hud-code">
              {answeredCount}/{paper.questions.length}
            </span>
          </div>

          {paper.sections.map((sec) => {
            const secQs = paper.questions.filter((q) => q.no >= sec.range[0] && q.no <= sec.range[1]);
            if (secQs.length === 0) return null;
            return (
              <div key={sec.id} className="palette-section-block">
                <span className="palette-section-lbl">{sec.title}</span>
                <div className="palette-grid">
                  {secQs.map((q) => {
                    const answered =
                      q.type === 'judge'
                        ? session.judgeChoices[q.id] !== undefined && session.judgeChoices[q.id] !== null
                        : q.type === 'single_choice'
                          ? Boolean(session.choiceAnswers?.[q.id])
                          : Boolean((session.textAnswers[q.id] ?? '').trim());
                    const flagged = Boolean(session.flagged[q.id]);
                    return (
                      <button
                        key={q.id}
                        type="button"
                        className={`palette-cell ${answered ? 'done' : ''} ${flagged ? 'flagged' : ''}`}
                        onClick={(e) => {
                          e.currentTarget.blur();
                          scrollToElement(`mock-q-${q.no}`, 142);
                        }}
                      >
                        {q.no}
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}

          <div className="palette-legend">
            <span>
              <i className="dot done" /> 已答
            </span>
            <span>
              <i className="dot flagged" /> 待查
            </span>
            <span>
              <i className="dot" /> 未答
            </span>
          </div>
        </aside>
      </div>
    </div>
  );
};
