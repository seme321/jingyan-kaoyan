import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  AlertTriangle,
  Bookmark,
  Check,
  ChevronLeft,
  ChevronRight,
  Eye,
  EyeOff,
  HelpCircle,
  NotebookPen,
  Shuffle,
  X,
} from 'lucide-react';
import { useData } from '../context/DataContext';
import { useStudy } from '../context/StudyContext';
import { Mascot, MascotTip } from '../components/Mascot';
import { MathText } from '../components/MathText';
import { FigureGallery } from '../components/FigureGallery';
import { QUESTION_TYPE_LABELS, type Question, type QuestionType } from '../types';

export const PracticePage: React.FC = () => {
  const { currentCourse, allQuestions, yearsMeta, papersByYear, chapters, chapterMap } = useData();
  const {
    state,
    getRecord,
    recordAttempt,
    toggleFavorite,
    saveQuestionNote,
    saveQuestionDraft,
    updateSettings,
  } = useStudy();
  const [searchParams, setSearchParams] = useSearchParams();
  const railRef = useRef<HTMLDivElement | null>(null);

  const availableTypes = useMemo(
    () => Array.from(new Set(allQuestions.map((q) => q.type))),
    [allQuestions]
  );

  const rawYear = searchParams.get('year') ? Number(searchParams.get('year')) : 0;
  const rawChapter = searchParams.get('chapter') ? Number(searchParams.get('chapter')) : 0;
  const rawType = (searchParams.get('type') as QuestionType | 'all') || 'all';
  const rawPool = searchParams.get('pool') || 'all';

  const yearFilter = rawYear && papersByYear[rawYear] ? rawYear : 0;
  const chapterFilter = rawChapter && chapterMap[rawChapter] ? rawChapter : 0;
  const typeFilter: QuestionType | 'all' =
    rawType !== 'all' && availableTypes.includes(rawType) ? rawType : 'all';
  const poolFilter: 'all' | 'unmastered' | 'wrong' | 'fav' =
    rawPool === 'unmastered' || rawPool === 'wrong' || rawPool === 'fav' ? rawPool : 'all';
  const kpFilter = searchParams.get('kp') || '';
  const methodFilter = searchParams.get('method') || '';
  const paramQid = searchParams.get('qid') || '';

  const [shuffledIds, setShuffledIds] = useState<string[] | null>(null);

  // Reset shuffle order cleanly if switching courses
  useEffect(() => {
    setShuffledIds(null);
  }, [currentCourse.id]);

  const updateFilters = useCallback(
    (patch: Record<string, string | number | null>) => {
      const next = new URLSearchParams(searchParams);
      next.delete('qid');
      for (const [k, v] of Object.entries(patch)) {
        if (v === null || v === '' || v === 0 || v === '0' || v === 'all') {
          next.delete(k);
        } else {
          next.set(k, String(v));
        }
      }
      setShuffledIds(null);
      setSearchParams(next, { replace: true });
    },
    [searchParams, setSearchParams]
  );

  const baseQueue = useMemo(() => {
    let list: Question[] = allQuestions;
    if (yearFilter > 0) list = list.filter((q) => q.year === yearFilter);
    if (chapterFilter > 0) list = list.filter((q) => q.chapter === chapterFilter);
    if (typeFilter !== 'all') list = list.filter((q) => q.type === typeFilter);
    if (kpFilter) list = list.filter((q) => q.kps.includes(kpFilter));
    if (methodFilter) list = list.filter((q) => q.method === methodFilter);
    if (poolFilter === 'unmastered') {
      list = list.filter((q) => getRecord(q.id).status !== 'mastered');
    } else if (poolFilter === 'wrong') {
      list = list.filter((q) => getRecord(q.id).inWrongBook);
    } else if (poolFilter === 'fav') {
      list = list.filter((q) => getRecord(q.id).favorite);
    }
    if (shuffledIds) {
      const orderMap = new Map(shuffledIds.map((id, i) => [id, i]));
      list = [...list].sort((a, b) => (orderMap.get(a.id) ?? 999) - (orderMap.get(b.id) ?? 999));
    }
    return list;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allQuestions, yearFilter, chapterFilter, typeFilter, kpFilter, methodFilter, poolFilter, shuffledIds]);

  const [currentIndex, setCurrentIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [judgePicked, setJudgePicked] = useState<boolean | null>(null);
  const [choicePicked, setChoicePicked] = useState<string>('');
  const [peekTags, setPeekTags] = useState(false);
  const [noteOpen, setNoteOpen] = useState(false);

  useEffect(() => {
    if (paramQid && baseQueue.length > 0) {
      const idx = baseQueue.findIndex((q) => q.id === paramQid);
      if (idx >= 0) {
        setCurrentIndex(idx);
        return;
      }
    }
    setCurrentIndex(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramQid, yearFilter, chapterFilter, typeFilter, kpFilter, methodFilter, poolFilter, currentCourse.id]);

  useEffect(() => {
    if (baseQueue.length > 0 && currentIndex >= baseQueue.length) {
      setCurrentIndex(baseQueue.length - 1);
    }
  }, [baseQueue.length, currentIndex]);

  useEffect(() => {
    const rail = railRef.current;
    if (!rail) return;
    const activeDot = rail.querySelector<HTMLElement>('.q-rail-dot.current');
    if (!activeDot) return;
    const dotTop = activeDot.offsetTop;
    const dotBottom = dotTop + activeDot.offsetHeight;
    if (dotTop < rail.scrollTop) {
      rail.scrollTop = Math.max(0, dotTop - 4);
    } else if (dotBottom > rail.scrollTop + rail.clientHeight) {
      rail.scrollTop = dotBottom - rail.clientHeight + 4;
    }
  }, [currentIndex, baseQueue.length]);

  const currentQuestion = baseQueue[currentIndex] ?? null;

  useEffect(() => {
    setRevealed(false);
    setJudgePicked(null);
    setChoicePicked('');
    setPeekTags(false);
    if (currentQuestion) {
      const rec = getRecord(currentQuestion.id);
      setNoteOpen(Boolean(rec.note));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentQuestion?.id]);

  const goPrev = useCallback(() => {
    setCurrentIndex((idx) => (idx > 0 ? idx - 1 : idx));
  }, []);

  const goNext = useCallback(() => {
    setCurrentIndex((idx) => (idx + 1 < baseQueue.length ? idx + 1 : idx));
  }, [baseQueue.length]);

  const handleJudgeAnswer = useCallback(
    (choice: boolean) => {
      if (!currentQuestion || currentQuestion.type !== 'judge') return;
      setJudgePicked(choice);
      setRevealed(true);
      const isCorrect = choice === currentQuestion.judgeAnswer;
      recordAttempt(currentQuestion.id, isCorrect ? 'mastered' : 'wrong', { judgeChoice: choice });
    },
    [currentQuestion, recordAttempt]
  );

  const handleSingleChoice = useCallback(
    (label: string) => {
      if (!currentQuestion || currentQuestion.type !== 'single_choice') return;
      setChoicePicked(label);
      setRevealed(true);
      const ans = (currentQuestion.choiceAnswer ?? '').trim().toUpperCase();
      const isCorrect = label.toUpperCase() === ans;
      recordAttempt(currentQuestion.id, isCorrect ? 'mastered' : 'wrong', { choice: label });
    },
    [currentQuestion, recordAttempt]
  );

  const handleSelfRate = useCallback(
    (status: 'mastered' | 'partial' | 'wrong') => {
      if (!currentQuestion) return;
      const curRec = getRecord(currentQuestion.id);
      recordAttempt(currentQuestion.id, status, { draft: curRec.userDraft });
      if (currentIndex + 1 < baseQueue.length) {
        setCurrentIndex((idx) => idx + 1);
      }
    },
    [currentQuestion, getRecord, recordAttempt, currentIndex, baseQueue.length]
  );

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
      if (!currentQuestion) return;

      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        goPrev();
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        goNext();
      } else if (e.key === ' ') {
        e.preventDefault();
        setRevealed((v) => !v);
      } else if (e.key.toLowerCase() === 's') {
        e.preventDefault();
        toggleFavorite(currentQuestion.id);
      } else if (currentQuestion.type === 'judge' && !revealed) {
        if (e.key === '1' || e.key.toLowerCase() === 't') handleJudgeAnswer(true);
        else if (e.key === '2' || e.key.toLowerCase() === 'f') handleJudgeAnswer(false);
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [currentQuestion, revealed, goPrev, goNext, toggleFavorite, handleJudgeAnswer]);

  const handleShuffle = () => {
    const ids = baseQueue.map((q) => q.id);
    for (let i = ids.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [ids[i], ids[j]] = [ids[j], ids[i]];
    }
    setShuffledIds(ids);
    setCurrentIndex(0);
  };

  const clearSpecialFilters = useCallback(() => {
    setShuffledIds(null);
    setSearchParams({}, { replace: true });
  }, [setSearchParams]);

  if (allQuestions.length === 0) {
    return (
      <div className="page-container">
        <div className="empty-state-card">
          <Mascot pose="study" size={140} />
          <h3>「{currentCourse.name}」真题包待导入</h3>
          <p>当前板块考纲与核心公式已就绪，导入第一套真题 JSON 后即可开始逐题刷题。</p>
          <div className="hero-cta-row">
            <Link to="/chapters" className="btn btn-secondary">
              浏览考纲章节
            </Link>
            <Link to="/formulas" className="btn btn-primary">
              背诵核心公式
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const rec = currentQuestion ? getRecord(currentQuestion.id) : null;
  const chInfo = currentQuestion ? chapterMap[currentQuestion.chapter] : null;
  const tagsVisible = !state.settings.hideTagsBeforeAnswer || revealed || peekTags;

  return (
    <div className="page-container">
      <div className="practice-filter-bar">
        <div className="filter-selects">
          <select
            className="ui-select"
            value={yearFilter}
            onChange={(e) => updateFilters({ year: Number(e.target.value) })}
            aria-label="按年份筛选"
          >
            <option value={0}>全部年份 ({allQuestions.length}题)</option>
            {yearsMeta
              .filter((ym) => ym.status === 'ready')
              .map((ym) => (
                <option key={ym.year} value={ym.year}>
                  {ym.year} 真题 ({ym.questionCount}题)
                </option>
              ))}
          </select>

          <select
            className="ui-select"
            value={chapterFilter}
            onChange={(e) => updateFilters({ chapter: Number(e.target.value) })}
            aria-label="按章节筛选"
          >
            <option value={0}>全部章节 ({chapters.length}章)</option>
            {chapters.map((c) => (
              <option key={c.chapter} value={c.chapter}>
                第 {c.chapter} 章 · {c.name}
              </option>
            ))}
          </select>

          <select
            className="ui-select"
            value={typeFilter}
            onChange={(e) => updateFilters({ type: e.target.value })}
            aria-label="按题型筛选"
          >
            <option value="all">全部题型</option>
            {availableTypes.map((tp) => (
              <option key={tp} value={tp}>
                {QUESTION_TYPE_LABELS[tp] ?? tp}
              </option>
            ))}
          </select>

          <select
            className="ui-select"
            value={poolFilter}
            onChange={(e) => updateFilters({ pool: e.target.value })}
            aria-label="按范围筛选"
          >
            <option value="all">全部题目</option>
            <option value="unmastered">仅刷未掌握</option>
            <option value="wrong">仅刷错题本</option>
            <option value="fav">仅刷收藏夹</option>
          </select>

          {(kpFilter || methodFilter) && (
            <button
              type="button"
              className="active-filter-chip"
              onClick={() => updateFilters({ kp: null, method: null })}
            >
              <span>{kpFilter ? `考点：${kpFilter}` : `方法：${methodFilter}`}</span>
              <X size={13} />
            </button>
          )}
        </div>

        <div className="filter-right-tools">
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() =>
              updateSettings({ hideTagsBeforeAnswer: !state.settings.hideTagsBeforeAnswer })
            }
          >
            {state.settings.hideTagsBeforeAnswer ? <EyeOff size={14} /> : <Eye size={14} />}
            {state.settings.hideTagsBeforeAnswer ? '考点：答前藏起' : '考点：始终显示'}
          </button>
          <button type="button" className="btn btn-secondary btn-sm" onClick={handleShuffle}>
            <Shuffle size={14} /> 随机乱序
          </button>
        </div>
      </div>

      {baseQueue.length === 0 ? (
        <div className="empty-state-card">
          <Mascot pose="think" size={130} />
          <h3>当前筛选条件下暂无题目</h3>
          <p>可能是该范围题目已全部掌握，或尚未添加收藏 / 错题。</p>
          <button type="button" className="btn btn-primary" onClick={clearSpecialFilters}>
            重置筛选条件
          </button>
        </div>
      ) : (
        currentQuestion &&
        rec && (
          <>
            <div ref={railRef} className="q-rail">
              {baseQueue.map((q, idx) => {
                const r = getRecord(q.id);
                return (
                  <button
                    key={q.id}
                    type="button"
                    className={`q-rail-dot ${idx === currentIndex ? 'current' : ''} status-${r.status}`}
                    onClick={() => setCurrentIndex(idx)}
                    title={`${q.year} 第 ${q.no} 题`}
                  >
                    {yearFilter === 0 && baseQueue.length > 30
                      ? `${String(q.year).slice(-2)}·${q.no}`
                      : q.no}
                  </button>
                );
              })}
            </div>

            <article className="studio-card">
              <div className="studio-header">
                <div className="q-meta-left">
                  <span className="q-year-pill">{currentQuestion.year} 真题</span>
                  <span className="q-no-badge">
                    第 {currentQuestion.no} 题 · {QUESTION_TYPE_LABELS[currentQuestion.type]}
                  </span>
                  <span className="q-score-badge">{currentQuestion.score} 分</span>
                  <span className="q-diff-badge">难度 {'★'.repeat(currentQuestion.difficulty)}</span>

                  {tagsVisible ? (
                    <>
                      {chInfo && (
                        <Link
                          to={`/practice?chapter=${currentQuestion.chapter}`}
                          className="q-tag chapter-tag"
                        >
                          第{currentQuestion.chapter}章 · {chInfo.name}
                        </Link>
                      )}
                      {currentQuestion.kps.map((kp) => (
                        <Link
                          key={kp}
                          to={`/practice?kp=${encodeURIComponent(kp)}`}
                          className="q-tag kp-tag"
                        >
                          {kp}
                        </Link>
                      ))}
                      <Link
                        to={`/practice?method=${encodeURIComponent(currentQuestion.method)}`}
                        className="q-tag method-tag"
                      >
                        方法：{currentQuestion.method}
                      </Link>
                    </>
                  ) : (
                    <button
                      type="button"
                      className="peek-tags-btn"
                      onClick={() => setPeekTags(true)}
                    >
                      <HelpCircle size={13} /> 提示考点与方法
                    </button>
                  )}
                </div>

                <div className="q-meta-right">
                  <span className="studio-counter">
                    {currentIndex + 1} / {baseQueue.length}
                  </span>
                  <button
                    type="button"
                    className={`icon-action-btn ${rec.favorite ? 'fav-active' : ''}`}
                    onClick={() => toggleFavorite(currentQuestion.id)}
                    title="收藏本题 (快捷键 S)"
                  >
                    <Bookmark size={16} fill={rec.favorite ? 'currentColor' : 'none'} />
                  </button>
                  <button
                    type="button"
                    className={`icon-action-btn ${noteOpen ? 'note-active' : ''}`}
                    onClick={() => setNoteOpen((v) => !v)}
                    title="记录本题私人笔记"
                  >
                    <NotebookPen size={16} />
                  </button>
                </div>
              </div>

              {currentQuestion.note && (
                <div className="q-calc-const-note">
                  <MathText text={currentQuestion.note} inline />
                </div>
              )}

              <div className="studio-stem">
                <MathText text={currentQuestion.stem} />
              </div>

              {currentQuestion.figures.length > 0 && (
                <FigureGallery figures={currentQuestion.figures} variant="exam" />
              )}

              {/* Interactive Answering Zone */}
              {currentQuestion.type === 'judge' ? (
                <div className="judge-action-zone">
                  <button
                    type="button"
                    className={`judge-choice-btn ${
                      judgePicked === true
                        ? currentQuestion.judgeAnswer === true
                          ? 'correct'
                          : 'wrong'
                        : revealed && currentQuestion.judgeAnswer === true
                          ? 'correct-outline'
                          : ''
                    }`}
                    onClick={() => handleJudgeAnswer(true)}
                  >
                    <Check size={18} /> 正确（√） <kbd>1</kbd>
                  </button>
                  <button
                    type="button"
                    className={`judge-choice-btn ${
                      judgePicked === false
                        ? currentQuestion.judgeAnswer === false
                          ? 'correct'
                          : 'wrong'
                        : revealed && currentQuestion.judgeAnswer === false
                          ? 'correct-outline'
                          : ''
                    }`}
                    onClick={() => handleJudgeAnswer(false)}
                  >
                    <X size={18} /> 错误（×） <kbd>2</kbd>
                  </button>

                  {judgePicked !== null && (
                    <MascotTip
                      pose={judgePicked === currentQuestion.judgeAnswer ? 'cheer' : 'think'}
                      tone={judgePicked === currentQuestion.judgeAnswer ? 'ok' : 'warn'}
                      size={64}
                      className="judge-mascot-tip"
                    >
                      {judgePicked === currentQuestion.judgeAnswer
                        ? '判断正确！这一题已标记为掌握，继续冲～'
                        : '哎呀判断反了！已帮你收进错题本，看看下面的解析找找陷阱吧。'}
                    </MascotTip>
                  )}
                </div>
              ) : currentQuestion.type === 'single_choice' && currentQuestion.options ? (
                <div className="choice-options-grid interactive">
                  {currentQuestion.options.map((opt) => {
                    const ans = (currentQuestion.choiceAnswer ?? '').trim().toUpperCase();
                    const optLabel = opt.label.trim().toUpperCase();
                    const picked = choicePicked.trim().toUpperCase() === optLabel;
                    const cls = picked
                      ? optLabel === ans
                        ? 'correct'
                        : 'wrong'
                      : revealed && optLabel === ans
                        ? 'correct-outline'
                        : '';
                    return (
                      <button
                        key={opt.label}
                        type="button"
                        className={`choice-opt-btn ${cls}`}
                        onClick={() => handleSingleChoice(opt.label)}
                      >
                        <span className="opt-badge">{opt.label}</span>
                        <MathText text={opt.text} inline />
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="subjective-draft-zone">
                  <textarea
                    className="draft-textarea"
                    rows={['calc', 'proof', 'short'].includes(currentQuestion.type) ? 3 : 2}
                    placeholder={
                      ['calc', 'proof'].includes(currentQuestion.type)
                        ? '手算草稿核对区：可先在纸上演算，在此记下各问最终得数或关键方程再对答案…'
                        : '在此输入你的答案或分析要点，再展开标准解析比对…'
                    }
                    value={rec.userDraft ?? ''}
                    onChange={(e) => saveQuestionDraft(currentQuestion.id, e.target.value)}
                  />
                </div>
              )}

              <div className="studio-action-bar">
                <button
                  type="button"
                  className="btn btn-secondary"
                  disabled={currentIndex === 0}
                  onClick={goPrev}
                >
                  <ChevronLeft size={16} /> 上一题
                </button>

                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => setRevealed((v) => !v)}
                >
                  {revealed ? '收起答案与解析 (Space)' : '查看答案与规范解析 (Space)'}
                </button>

                <button
                  type="button"
                  className="btn btn-secondary"
                  disabled={currentIndex + 1 >= baseQueue.length}
                  onClick={goNext}
                >
                  下一题 <ChevronRight size={16} />
                </button>
              </div>

              {noteOpen && (
                <div className="personal-note-box">
                  <label className="note-box-label">
                    <NotebookPen size={14} /> 我的本题心得 / 易错笔记（自动保存在本地）
                  </label>
                  <textarea
                    rows={2}
                    placeholder="记录自己卡壳的步骤、易混公式或二刷提醒…"
                    value={rec.note ?? ''}
                    onChange={(e) => saveQuestionNote(currentQuestion.id, e.target.value)}
                  />
                </div>
              )}

              {revealed && (
                <div className="q-solution-panel studio-sol">
                  <div className="sol-topic-row">
                    <span className="sol-topic-title">
                      核心考点：<MathText text={currentQuestion.title} inline />
                    </span>
                    <span className="ai-gen-notice">AI 辅助精解与自拟采分点 · 仅供学习参考</span>
                  </div>

                  <div className="sol-answer-box">
                    <span className="sol-badge">参考答案</span>
                    <div className="sol-answer-content">
                      <MathText text={currentQuestion.answer} />
                    </div>
                  </div>

                  {currentQuestion.rubric && (
                    <div className="sol-rubric-preview">
                      <div className="sol-section-label">
                        步骤采分点参考（满分 {currentQuestion.score} 分）
                      </div>
                      <ul className="rubric-list">
                        {currentQuestion.rubric.map((rItem, i) => (
                          <li key={i}>
                            <span className="rubric-pts">+{rItem.pts}分</span>
                            <MathText text={rItem.label} inline />
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="sol-detail-box">
                    <div className="sol-section-label">规范推导与详细解析</div>
                    <MathText text={currentQuestion.analysis} />
                    {currentQuestion.analysisFigures.length > 0 && (
                      <FigureGallery figures={currentQuestion.analysisFigures} variant="solution" />
                    )}
                  </div>

                  {currentQuestion.pitfalls && (
                    <div className="sol-pitfall-box">
                      <div className="pitfall-title">
                        <AlertTriangle size={15} /> 考点与易错提示
                      </div>
                      <MathText text={currentQuestion.pitfalls} />
                    </div>
                  )}

                  <div className="self-eval-box">
                    <span className="self-eval-prompt">对照解析自评掌握度（记录进度并驱动错题闭环）：</span>
                    <div className="self-eval-btns">
                      <button
                        type="button"
                        className={`eval-btn mastered ${rec.status === 'mastered' ? 'selected' : ''}`}
                        onClick={() => handleSelfRate('mastered')}
                      >
                        ✓ 完全掌握
                      </button>
                      <button
                        type="button"
                        className={`eval-btn partial ${rec.status === 'partial' ? 'selected' : ''}`}
                        onClick={() => handleSelfRate('partial')}
                      >
                        ~ 半会·需巩固
                      </button>
                      <button
                        type="button"
                        className={`eval-btn wrong ${rec.status === 'wrong' ? 'selected' : ''}`}
                        onClick={() => handleSelfRate('wrong')}
                      >
                        ✗ 不会·入错题本
                      </button>
                    </div>
                  </div>
                </div>
              )}

              <div className="shortcut-footer">
                快捷键：<kbd>←</kbd> <kbd>→</kbd> 切换题目 · <kbd>Space</kbd> 显隐解析 · 判断题按{' '}
                <kbd>1</kbd> 正确 / <kbd>2</kbd> 错误 · <kbd>S</kbd> 收藏
              </div>
            </article>
          </>
        )
      )}
    </div>
  );
};
