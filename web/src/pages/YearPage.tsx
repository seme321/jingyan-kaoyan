import React, { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  AlertTriangle,
  Bookmark,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Eye,
  EyeOff,
  Play,
  Timer,
} from 'lucide-react';
import { useData } from '../context/DataContext';
import { useStudy } from '../context/StudyContext';
import { Mascot } from '../components/Mascot';
import { MathText } from '../components/MathText';
import { FigureGallery } from '../components/FigureGallery';
import { scrollToElement } from '../utils/scroll';

type BrowseMode = 'paper' | 'full' | 'recite';

export const YearPage: React.FC = () => {
  const { currentCourse, yearsMeta, papersByYear, chapterMap } = useData();
  const { getRecord, toggleFavorite } = useStudy();
  const [searchParams, setSearchParams] = useSearchParams();

  const readyYears = useMemo(
    () => yearsMeta.filter((y) => y.status === 'ready').map((y) => y.year),
    [yearsMeta]
  );
  const firstReady = readyYears[0] ?? 0;
  const urlYearParam = Number(searchParams.get('year')) || 0;
  const selectedYear = urlYearParam && papersByYear[urlYearParam] ? urlYearParam : firstReady;

  const [mode, setMode] = useState<BrowseMode>('paper');
  const [openIds, setOpenIds] = useState<Record<string, boolean>>({});

  useEffect(() => {
    setOpenIds({});
  }, [selectedYear, currentCourse.id]);

  useEffect(() => {
    if (urlYearParam && !papersByYear[urlYearParam] && firstReady) {
      setSearchParams({ year: String(firstReady) }, { replace: true });
    }
  }, [urlYearParam, papersByYear, firstReady, setSearchParams]);

  const paper = papersByYear[selectedYear];

  const toggleSingle = (qid: string) => {
    setOpenIds((prev) => ({ ...prev, [qid]: !prev[qid] }));
  };

  const statusBadge = (qid: string) => {
    const r = getRecord(qid);
    if (r.status === 'mastered') return <span className="q-status mastered">已掌握</span>;
    if (r.status === 'partial') return <span className="q-status partial">半会</span>;
    if (r.status === 'wrong') return <span className="q-status wrong">错题</span>;
    return null;
  };

  const sectionQuestions = useMemo(() => {
    if (!paper) return [];
    return paper.sections.map((sec) => ({
      section: sec,
      items: paper.questions.filter((q) => q.no >= sec.range[0] && q.no <= sec.range[1]),
    }));
  }, [paper]);

  return (
    <div className="page-container reading-narrow">
      {/* Year Dossier Switcher Bar */}
      <div className="page-header-card">
        <div className="page-kicker">EXAM ARCHIVE // {currentCourse.id.toUpperCase()}</div>
        <div className="year-tabs-scroll">
          {yearsMeta.map((ym) => {
            const isReady = ym.status === 'ready';
            return (
              <button
                key={ym.year}
                type="button"
                className={`year-tab ${selectedYear === ym.year && isReady ? 'active' : ''} ${
                  !isReady ? 'disabled' : ''
                }`}
                onClick={() => {
                  if (!isReady || ym.year === selectedYear) return;
                  setOpenIds({});
                  setSearchParams({ year: String(ym.year) }, { replace: true });
                }}
                title={isReady ? ym.title : `${ym.year} 真题待导入`}
              >
                <span className="year-num">{ym.year}</span>
                <span className="year-sub">
                  {isReady ? `${ym.questionCount}题·${ym.totalScore}分` : '待导入'}
                </span>
              </button>
            );
          })}
        </div>

        {paper && (
          <div className="paper-toolbar">
            <div className="seg-group">
              <button
                type="button"
                className={`seg-btn ${mode === 'paper' ? 'active' : ''}`}
                onClick={() => setMode('paper')}
              >
                <EyeOff size={14} /> 原卷看题
              </button>
              <button
                type="button"
                className={`seg-btn ${mode === 'recite' ? 'active' : ''}`}
                onClick={() => setMode('recite')}
              >
                <CheckCircle2 size={14} /> 答案速查
              </button>
              <button
                type="button"
                className={`seg-btn ${mode === 'full' ? 'active' : ''}`}
                onClick={() => setMode('full')}
              >
                <Eye size={14} /> 精讲全解
              </button>
            </div>

            <div className="paper-toolbar-actions">
              <Link to={`/practice?year=${paper.year}`} className="btn btn-tactical btn-sm">
                <Play size={14} /> 逐题刷本卷
              </Link>
              <Link to={`/mock?year=${paper.year}`} className="btn btn-primary btn-sm">
                <Timer size={14} /> 限时模考
              </Link>
            </div>
          </div>
        )}
      </div>

      {!paper ? (
        <div className="empty-state-card">
          <Mascot pose="study" size={140} />
          <h3>「{currentCourse.name}」真题包待导入</h3>
          <p>
            当前已登记 {yearsMeta.length} 个年份占位，按照项目内《生成说明书》与《导入说明书》处理原始试卷后，即可一键激活整卷浏览。
          </p>
          <div className="hero-cta-row">
            <Link to="/chapters" className="btn btn-secondary">
              查看考纲章节
            </Link>
            <Link to="/formulas" className="btn btn-primary">
              背诵本科目公式
            </Link>
          </div>
        </div>
      ) : (
        <>
          <div className="exam-notice-box">
            <div className="exam-notice-head">
              <div>
                <div className="hud-code">PAPER DOSSIER // {paper.year} · CODE {paper.code}</div>
                <h2>
                  {paper.year} 年{paper.school} {paper.code} {paper.subject}考研真题
                </h2>
              </div>
              <div className="section-jump-pills">
                {paper.sections.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    className="jump-pill"
                    onClick={(e) => {
                      e.currentTarget.blur();
                      scrollToElement(`sec-${s.id}`, 78);
                    }}
                  >
                    {s.title} ({s.totalScore}分)
                  </button>
                ))}
              </div>
            </div>
            <ul className="exam-notes-list">
              {paper.examNotes.map((n, idx) => (
                <li key={idx}>
                  <MathText text={n} inline />
                </li>
              ))}
            </ul>
          </div>

          {sectionQuestions.map(({ section, items }) => (
            <section key={section.id} id={`sec-${section.id}`} className="paper-section">
              <div className="paper-section-banner">
                <h3>{section.title}</h3>
                <span>{section.description}</span>
              </div>

              <div className="question-stack">
                {items.map((q) => {
                  const rec = getRecord(q.id);
                  const showFull = mode === 'full' || Boolean(openIds[q.id]);
                  const showShort = mode === 'recite' && !showFull;
                  const chInfo = chapterMap[q.chapter];

                  return (
                    <article key={q.id} className="q-card">
                      <div className="q-card-header">
                        <div className="q-meta-left">
                          <span className="q-no-badge">T{String(q.no).padStart(2, '0')}</span>
                          <span className="q-score-badge">{q.score} 分</span>
                          {statusBadge(q.id)}
                          {(showFull || mode === 'recite') && chInfo && (
                            <Link to={`/practice?chapter=${q.chapter}`} className="q-tag chapter-tag">
                              第{q.chapter}章 · {chInfo.name}
                            </Link>
                          )}
                          {(showFull || mode === 'recite') &&
                            q.kps.map((kp) => (
                              <Link
                                key={kp}
                                to={`/practice?kp=${encodeURIComponent(kp)}`}
                                className="q-tag kp-tag"
                              >
                                {kp}
                              </Link>
                            ))}
                        </div>

                        <div className="q-meta-right">
                          <button
                            type="button"
                            className={`icon-action-btn ${rec.favorite ? 'fav-active' : ''}`}
                            onClick={() => toggleFavorite(q.id)}
                            title={rec.favorite ? '取消收藏' : '收藏本题'}
                          >
                            <Bookmark size={15} fill={rec.favorite ? 'currentColor' : 'none'} />
                          </button>
                          <Link
                            to={`/practice?qid=${q.id}`}
                            className="btn-inline-link"
                            title="进入沉浸式逐题练习台"
                          >
                            单题精练 →
                          </Link>
                        </div>
                      </div>

                      {q.note && (
                        <div className="q-calc-const-note">
                          <MathText text={q.note} inline />
                        </div>
                      )}

                      <div className="q-stem-body">
                        <MathText text={q.stem} />
                        {q.type === 'judge' && <span className="judge-brackets">（　　）</span>}
                      </div>

                      {q.options && q.options.length > 0 && (
                        <div className="choice-options-grid">
                          {q.options.map((opt) => (
                            <div key={opt.label} className="choice-opt-static">
                              <strong>{opt.label}.</strong> <MathText text={opt.text} inline />
                            </div>
                          ))}
                        </div>
                      )}

                      {q.figures.length > 0 && <FigureGallery figures={q.figures} variant="exam" />}

                      {showShort && (
                        <div className="q-recite-bar">
                          <span className="recite-label">核心答案：</span>
                          <MathText text={q.shortAnswer || q.answer} inline />
                          <span className="recite-method">方法：{q.method}</span>
                        </div>
                      )}

                      {mode !== 'full' && (
                        <div className="q-toggle-row">
                          <button
                            type="button"
                            className="btn-expand-sol"
                            onClick={() => toggleSingle(q.id)}
                          >
                            {openIds[q.id] ? (
                              <>
                                <ChevronUp size={15} /> 收起解析
                              </>
                            ) : (
                              <>
                                <ChevronDown size={15} /> 查看答案与规范解析
                              </>
                            )}
                          </button>
                        </div>
                      )}

                      {showFull && (
                        <div className="q-solution-panel">
                          <div className="sol-topic-row">
                            <span className="sol-topic-title">
                              命题立意：<MathText text={q.title} inline />
                            </span>
                            <Link
                              to={`/practice?method=${encodeURIComponent(q.method)}`}
                              className="q-tag method-tag"
                            >
                              方法：{q.method}
                            </Link>
                          </div>

                          <div className="sol-answer-box">
                            <span className="sol-badge">ANSWER // 参考答案</span>
                            <div className="sol-answer-content">
                              <MathText text={q.answer} />
                            </div>
                          </div>

                          <div className="sol-detail-box">
                            <div className="sol-section-label-row">
                              <div className="sol-section-label">DERIVATION // 规范推导与精解</div>
                              <span className="ai-gen-notice">AI 辅助精解 · 仅供学习参考</span>
                            </div>
                            <MathText text={q.analysis} />
                            {q.analysisFigures.length > 0 && (
                              <FigureGallery figures={q.analysisFigures} variant="solution" />
                            )}
                          </div>

                          {q.pitfalls && (
                            <div className="sol-pitfall-box">
                              <div className="pitfall-title">
                                <AlertTriangle size={15} /> CAUTION // 考点与易错提示
                              </div>
                              <MathText text={q.pitfalls} />
                            </div>
                          )}
                        </div>
                      )}
                    </article>
                  );
                })}
              </div>
            </section>
          ))}
        </>
      )}
    </div>
  );
};
