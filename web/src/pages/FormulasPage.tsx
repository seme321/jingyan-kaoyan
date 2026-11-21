import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ChevronLeft,
  ChevronRight,
  Eye,
  FileSpreadsheet,
  Layers,
  RotateCw,
  Search,
  Star,
} from 'lucide-react';
import { useData } from '../context/DataContext';
import { useStudy } from '../context/StudyContext';
import { Mascot } from '../components/Mascot';
import { KaTeXFormula, MathText } from '../components/MathText';

export const FormulasPage: React.FC = () => {
  const { currentCourse, formulas, chapters, chapterMap } = useData();
  const { state, toggleFavoriteFormula } = useStudy();

  const [chapterFilter, setChapterFilter] = useState<number>(0);
  const [onlyFav, setOnlyFav] = useState(false);
  const [query, setQuery] = useState('');
  const [cardMode, setCardMode] = useState(false);
  const [cardIdx, setCardIdx] = useState(0);
  const [cardFlipped, setCardFlipped] = useState(false);

  const filtered = useMemo(() => {
    return formulas.filter((f) => {
      if (chapterFilter > 0 && f.chapter !== chapterFilter) return false;
      if (onlyFav && !state.favoriteFormulas.includes(f.id)) return false;
      const kw = query.trim().toLowerCase();
      if (!kw) return true;
      return (
        f.name.toLowerCase().includes(kw) ||
        f.variables.toLowerCase().includes(kw) ||
        f.note.toLowerCase().includes(kw)
      );
    });
  }, [formulas, chapterFilter, onlyFav, state.favoriteFormulas, query]);

  useEffect(() => {
    setCardIdx(0);
    setCardFlipped(false);
  }, [chapterFilter, onlyFav, query, cardMode]);

  // Keyboard navigation in Flashcard mode
  useEffect(() => {
    if (!cardMode || filtered.length === 0) return;
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === 'INPUT' || tag === 'SELECT') return;
      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        setCardFlipped(false);
        setCardIdx((i) => (i > 0 ? i - 1 : filtered.length - 1));
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        setCardFlipped(false);
        setCardIdx((i) => (i + 1 < filtered.length ? i + 1 : 0));
      } else if (e.key === ' ') {
        e.preventDefault();
        setCardFlipped((f) => !f);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [cardMode, filtered.length]);

  const activeCard = filtered[cardIdx] ?? null;

  return (
    <div className="page-container">
      <div className="page-header-card">
        <div className="header-flex">
          <div>
            <h1 className="page-title">
              <FileSpreadsheet size={22} className="text-amber" /> {currentCourse.name} · 核心公式速记手册
            </h1>
            <p className="page-desc">
              精选 {formulas.length} 组考场必背核心方程、物理量纲与适用边界，支持列表精读与闪卡默写自测
            </p>
          </div>

          <div className="seg-group">
            <button
              type="button"
              className={`seg-btn ${!cardMode ? 'active' : ''}`}
              onClick={() => setCardMode(false)}
            >
              <Layers size={14} /> 列表精读模式
            </button>
            <button
              type="button"
              className={`seg-btn ${cardMode ? 'active' : ''}`}
              onClick={() => setCardMode(true)}
            >
              <RotateCw size={14} /> 闪卡默写模式
            </button>
          </div>
        </div>

        <div className="practice-filter-bar" style={{ marginTop: '0.85rem', padding: 0, border: 'none', background: 'transparent' }}>
          <div className="filter-selects">
            <select
              className="ui-select"
              value={chapterFilter}
              onChange={(e) => setChapterFilter(Number(e.target.value))}
              aria-label="按章节筛选公式"
            >
              <option value={0}>全部章节 ({formulas.length})</option>
              {chapters.map((c) => (
                <option key={c.chapter} value={c.chapter}>
                  第 {c.chapter} 章 · {c.name}
                </option>
              ))}
            </select>

            <button
              type="button"
              className={`btn btn-sm ${onlyFav ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setOnlyFav((v) => !v)}
            >
              <Star size={14} fill={onlyFav ? 'currentColor' : 'none'} /> 收藏 ({state.favoriteFormulas.length})
            </button>
          </div>

          <div className="search-input-wrap">
            <Search size={15} />
            <input
              type="text"
              placeholder="搜索公式名称、水击、曼宁、比能、流网…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state-card">
          <Mascot pose="think" size={120} />
          <h3>没有匹配的公式</h3>
          <p>请尝试切换章节或清空搜索关键词。</p>
        </div>
      ) : cardMode && activeCard ? (
        <div className="flashcard-stage">
          <div className="flashcard-box" onClick={() => setCardFlipped((f) => !f)}>
            <div className="flashcard-top">
              <span className="q-tag chapter-tag">
                第{activeCard.chapter}章 · {chapterMap[activeCard.chapter]?.name}
              </span>
              <span className="studio-counter">
                卡片 {cardIdx + 1} / {filtered.length}
              </span>
              <button
                type="button"
                className={`icon-action-btn ${
                  state.favoriteFormulas.includes(activeCard.id) ? 'fav-active' : ''
                }`}
                onClick={(e) => {
                  e.stopPropagation();
                  toggleFavoriteFormula(activeCard.id);
                }}
              >
                <Star
                  size={16}
                  fill={state.favoriteFormulas.includes(activeCard.id) ? 'currentColor' : 'none'}
                />
              </button>
            </div>

            <h2 className="flashcard-name">{activeCard.name}</h2>

            {!cardFlipped ? (
              <div className="flashcard-prompt">
                <p>请先在脑海中或草稿纸上默写该公式及其适用条件</p>
                <span className="btn btn-primary btn-sm">
                  <Eye size={14} /> 点击或按空格键翻面核对
                </span>
              </div>
            ) : (
              <div className="flashcard-answer" onClick={(e) => e.stopPropagation()}>
                <div className="formula-math-box">
                  <KaTeXFormula latex={activeCard.latex} />
                </div>
                <div className="formula-vars">
                  <strong>符号说明：</strong>
                  <MathText text={activeCard.variables} inline />
                </div>
                <div className="formula-note">
                  <strong>适用边界与考场提醒：</strong>
                  <MathText text={activeCard.note} inline />
                </div>
              </div>
            )}
          </div>

          <div className="flashcard-controls">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => {
                setCardFlipped(false);
                setCardIdx((i) => (i > 0 ? i - 1 : filtered.length - 1));
              }}
            >
              <ChevronLeft size={16} /> 上一张 (←)
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => setCardFlipped((f) => !f)}
            >
              {cardFlipped ? '盖上重默 (Space)' : '翻开看公式 (Space)'}
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => {
                setCardFlipped(false);
                setCardIdx((i) => (i + 1 < filtered.length ? i + 1 : 0));
              }}
            >
              下一张 (→) <ChevronRight size={16} />
            </button>
          </div>
        </div>
      ) : (
        <div className="formulas-stack">
          {filtered.map((f) => {
            const isFav = state.favoriteFormulas.includes(f.id);
            return (
              <article key={f.id} className="formula-card">
                <div className="formula-card-head">
                  <div className="q-meta-left">
                    <Link to={`/practice?chapter=${f.chapter}`} className="q-tag chapter-tag">
                      第{f.chapter}章 · {chapterMap[f.chapter]?.name}
                    </Link>
                    <h3 className="formula-title">{f.name}</h3>
                  </div>
                  <button
                    type="button"
                    className={`icon-action-btn ${isFav ? 'fav-active' : ''}`}
                    onClick={() => toggleFavoriteFormula(f.id)}
                    title={isFav ? '取消收藏公式' : '收藏重点公式'}
                  >
                    <Star size={16} fill={isFav ? 'currentColor' : 'none'} />
                  </button>
                </div>

                <div className="formula-math-box">
                  <KaTeXFormula latex={f.latex} />
                </div>

                <div className="formula-vars">
                  <strong>物理量与量纲：</strong>
                  <MathText text={f.variables} inline />
                </div>

                <div className="formula-note">
                  <strong>考场边界与易错点：</strong>
                  <MathText text={f.note} inline />
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
};
