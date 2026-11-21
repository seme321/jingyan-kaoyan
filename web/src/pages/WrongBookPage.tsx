import React, { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  Bookmark,
  BookMarked,
  CheckCircle2,
  Eye,
  NotebookPen,
  Play,
  Trash2,
} from 'lucide-react';
import { useData } from '../context/DataContext';
import { useStudy } from '../context/StudyContext';
import { Mascot } from '../components/Mascot';
import { MathText } from '../components/MathText';
import { FigureGallery } from '../components/FigureGallery';

type TabKey = 'wrong' | 'fav' | 'notes';

export const WrongBookPage: React.FC = () => {
  const { currentCourse, allQuestions, chapterMap } = useData();
  const { getRecord, removeFromWrongBook, toggleFavorite, saveQuestionNote, trackQuestionReviewed } =
    useStudy();
  const [tab, setTab] = useState<TabKey>('wrong');
  const [openAns, setOpenAns] = useState<Record<string, boolean>>({});

  const wrongList = useMemo(
    () => allQuestions.filter((q) => getRecord(q.id).inWrongBook),
    [allQuestions, getRecord]
  );

  const favList = useMemo(
    () => allQuestions.filter((q) => getRecord(q.id).favorite),
    [allQuestions, getRecord]
  );

  const notesList = useMemo(
    () => allQuestions.filter((q) => Boolean(getRecord(q.id).note?.trim())),
    [allQuestions, getRecord]
  );

  const activeList = tab === 'wrong' ? wrongList : tab === 'fav' ? favList : notesList;

  return (
    <div className="page-container reading-narrow">
      <div className="page-header-card">
        <div className="page-kicker">ERRATA LOOP // REVIEW & NOTES</div>
        <div className="header-flex">
          <div>
            <h1 className="page-title">
              <BookMarked size={22} className="text-coral" /> {currentCourse.shortLabel} · 错题 / 收藏 / 笔记墙
            </h1>
            <p className="page-desc">
              判错的客观题与自评「不会 / 半会」的题目自动归集至此，攻克后可「斩题」移出
            </p>
          </div>

          <div className="seg-group">
            <button
              type="button"
              className={`seg-btn ${tab === 'wrong' ? 'active' : ''}`}
              onClick={() => setTab('wrong')}
            >
              错题本 ({wrongList.length})
            </button>
            <button
              type="button"
              className={`seg-btn ${tab === 'fav' ? 'active' : ''}`}
              onClick={() => setTab('fav')}
            >
              收藏夹 ({favList.length})
            </button>
            <button
              type="button"
              className={`seg-btn ${tab === 'notes' ? 'active' : ''}`}
              onClick={() => setTab('notes')}
            >
              笔记墙 ({notesList.length})
            </button>
          </div>
        </div>

        {tab === 'wrong' && wrongList.length > 0 && (
          <div className="review-cta-bar">
            <span>
              PENDING // 共 <strong className="font-mono text-coral">{wrongList.length}</strong> 道待攻克错题 / 半会题
            </span>
            <Link to="/practice?pool=wrong" className="btn btn-tactical btn-sm">
              <Play size={14} /> 集中重刷全部错题
            </Link>
          </div>
        )}
        {tab === 'fav' && favList.length > 0 && (
          <div className="review-cta-bar">
            <span>
              STARRED // 共收藏 <strong className="font-mono text-sky">{favList.length}</strong> 道重点真题
            </span>
            <Link to="/practice?pool=fav" className="btn btn-primary btn-sm">
              <Play size={14} /> 集中刷收藏夹
            </Link>
          </div>
        )}
      </div>

      {activeList.length === 0 ? (
        <div className="empty-state-card">
          <Mascot pose={tab === 'wrong' ? 'cheer' : 'think'} size={130} />
          <span className="hud-code">STATUS // ALL_CLEAR</span>
          <h3>
            {tab === 'wrong'
              ? '太棒了！当前错题本已清零'
              : tab === 'fav'
                ? '尚未收藏题目'
                : '尚未写下复习笔记'}
          </h3>
          <p>
            {tab === 'wrong'
              ? '去逐题刷题或进行一次整卷限时模考，检验真实薄弱点吧。'
              : '在浏览试卷或逐题练习时，点击右上角书签或笔记图标即可随时收录。'}
          </p>
          <Link to="/practice" className="btn btn-tactical">
            前往逐题刷题
          </Link>
        </div>
      ) : (
        <div className="question-stack">
          {activeList.map((q) => {
            const rec = getRecord(q.id);
            const isOpen = Boolean(openAns[q.id]);
            return (
              <article key={q.id} className="q-card">
                <div className="q-card-header">
                  <div className="q-meta-left">
                    <span className="q-year-pill">{q.year} 真题</span>
                    <span className="q-no-badge">T{String(q.no).padStart(2, '0')}</span>
                    <span className="q-score-badge">{q.score} 分</span>
                    <span className="q-tag chapter-tag">
                      第{q.chapter}章 · {chapterMap[q.chapter]?.name}
                    </span>
                    {rec.wrongCount > 0 && (
                      <span className="wrong-count-pill">累计错 {rec.wrongCount} 次</span>
                    )}
                  </div>

                  <div className="q-meta-right">
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => {
                        if (!isOpen) trackQuestionReviewed(q.id);
                        setOpenAns((p) => ({ ...p, [q.id]: !p[q.id] }));
                      }}
                    >
                      <Eye size={13} /> {isOpen ? '收起答案' : '看答案'}
                    </button>
                    <Link to={`/practice?qid=${q.id}`} className="btn btn-primary btn-sm">
                      重做本题
                    </Link>
                    {tab === 'wrong' && (
                      <button
                        type="button"
                        className="btn btn-ghost-emerald btn-sm"
                        onClick={() => removeFromWrongBook(q.id, true)}
                        title="已彻底弄懂，标为已掌握并移出错题本"
                      >
                        <CheckCircle2 size={14} /> 斩题移出
                      </button>
                    )}
                    {tab === 'fav' && (
                      <button
                        type="button"
                        className="icon-action-btn fav-active"
                        onClick={() => toggleFavorite(q.id)}
                        title="取消收藏"
                      >
                        <Bookmark size={15} fill="currentColor" />
                      </button>
                    )}
                  </div>
                </div>

                {q.note && (
                  <div className="q-calc-const-note">
                    <MathText text={q.note} inline />
                  </div>
                )}

                <div className="q-stem-body">
                  <MathText text={q.stem} />
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

                {(rec.note || tab === 'notes') && (
                  <div className="personal-note-box" style={{ marginTop: '0.85rem' }}>
                    <div className="note-box-head">
                      <span className="note-box-label">
                        <NotebookPen size={13} /> 我的复习笔记
                      </span>
                      {rec.note && (
                        <button
                          type="button"
                          className="btn-inline-danger"
                          onClick={() => saveQuestionNote(q.id, '')}
                        >
                          <Trash2 size={12} /> 删除笔记
                        </button>
                      )}
                    </div>
                    <textarea
                      rows={2}
                      value={rec.note ?? ''}
                      onChange={(e) => saveQuestionNote(q.id, e.target.value)}
                      placeholder="补充本题易错心得…"
                    />
                  </div>
                )}

                {isOpen && (
                  <div className="q-solution-panel">
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
      )}
    </div>
  );
};
