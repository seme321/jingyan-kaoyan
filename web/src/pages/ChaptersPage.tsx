import React, { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Flame, Layers, Play, Star } from 'lucide-react';
import { useData } from '../context/DataContext';
import { useStudy } from '../context/StudyContext';

export const ChaptersPage: React.FC = () => {
  const { currentCourse, chaptersPayload, chapters, allQuestions, yearsMeta } = useData();
  const { getRecord } = useStudy();
  const [filterScope, setFilterScope] = useState<'all' | 'big' | 'small'>('all');
  const readyYearCount = Math.max(1, yearsMeta.filter((y) => y.status === 'ready').length);
  const bigCount = useMemo(() => chapters.filter((c) => c.hasBigQuestion).length, [chapters]);
  const smallCount = useMemo(() => chapters.filter((c) => !c.hasBigQuestion).length, [chapters]);

  const chapterStats = useMemo(() => {
    const map: Record<
      number,
      { total: number; scoreSum: number; mastered: number; partial: number; wrong: number }
    > = {};
    for (const c of chapters) {
      map[c.chapter] = { total: 0, scoreSum: 0, mastered: 0, partial: 0, wrong: 0 };
    }
    for (const q of allQuestions) {
      const bucket = map[q.chapter];
      if (!bucket) continue;
      bucket.total += 1;
      bucket.scoreSum += q.score;
      const r = getRecord(q.id);
      if (r.status === 'mastered') bucket.mastered += 1;
      else if (r.status === 'partial') bucket.partial += 1;
      else if (r.status === 'wrong') bucket.wrong += 1;
    }
    return map;
  }, [chapters, allQuestions, getRecord]);

  const filteredChapters = useMemo(() => {
    if (filterScope === 'big') return chapters.filter((c) => c.hasBigQuestion);
    if (filterScope === 'small') return chapters.filter((c) => !c.hasBigQuestion);
    return chapters;
  }, [chapters, filterScope]);

  return (
    <div className="page-container">
      <div className="page-header-card">
        <div className="page-kicker">AXIS-A // SYLLABUS BREAKDOWN</div>
        <div className="header-flex">
          <div>
            <h1 className="page-title">
              <Layers size={22} className="text-sky" /> {currentCourse.name} · 章节练习
            </h1>
            <p className="page-desc">
              {chaptersPayload?.syllabusTitle} · {chaptersPayload?.textbook}
            </p>
          </div>

          {bigCount > 0 && smallCount > 0 && (
            <div className="seg-group">
              <button
                type="button"
                className={`seg-btn ${filterScope === 'all' ? 'active' : ''}`}
                onClick={() => setFilterScope('all')}
              >
                全部章节 ({chapters.length})
              </button>
              <button
                type="button"
                className={`seg-btn ${filterScope === 'big' ? 'active' : ''}`}
                onClick={() => setFilterScope('big')}
              >
                大题核心章 ({bigCount})
              </button>
              <button
                type="button"
                className={`seg-btn ${filterScope === 'small' ? 'active' : ''}`}
                onClick={() => setFilterScope('small')}
              >
                小题 / 选考章 ({smallCount})
              </button>
            </div>
          )}
        </div>

        {chaptersPayload && (
          <div className="syllabus-highlights">
            {chaptersPayload.highlights.map((h, i) => (
              <span key={i} className="highlight-chip">
                <Flame size={13} className="text-amber" /> {h}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="chapters-grid">
        {filteredChapters.map((ch) => {
          const st = chapterStats[ch.chapter] ?? {
            total: 0,
            scoreSum: 0,
            mastered: 0,
            partial: 0,
            wrong: 0,
          };
          const done = st.mastered + st.partial + st.wrong;
          const pct = st.total > 0 ? Math.round((st.mastered / st.total) * 100) : 0;

          return (
            <div key={ch.chapter} className={`chapter-card ${ch.hasBigQuestion ? 'is-big' : ''}`}>
              <span className="chapter-watermark" aria-hidden="true">
                CH.{String(ch.chapter).padStart(2, '0')}
              </span>
              <div className="chapter-card-top">
                <div>
                  <div className="chapter-title-row">
                    <span className="chapter-index">CH.{String(ch.chapter).padStart(2, '0')}</span>
                    <h2 className="chapter-name">{ch.name}</h2>
                    {ch.hasBigQuestion ? (
                      <span className="badge-big">大题重镇</span>
                    ) : (
                      <span className="badge-small">仅考小题</span>
                    )}
                  </div>
                  <div className="chapter-meta-line">
                    <span>题型：{ch.questionTypes}</span>
                    <span>·</span>
                    <span>常规分值：{ch.scoreLabel} 分</span>
                    <span>·</span>
                    <span className="stars-inline" title={`考纲难度 ${ch.stars} 星`}>
                      {Array.from({ length: ch.stars }).map((_, idx) => (
                        <Star key={idx} size={13} fill="currentColor" className="text-amber" />
                      ))}
                    </span>
                  </div>
                </div>

                <Link
                  to={`/practice?chapter=${ch.chapter}`}
                  className={ch.hasBigQuestion ? 'btn btn-tactical btn-sm' : 'btn btn-primary btn-sm'}
                >
                  <Play size={13} /> 刷本章 ({st.total})
                </Link>
              </div>

              <p className="chapter-summary">{ch.summary}</p>

              <div className="chapter-kps-row">
                {ch.coreKps.map((kp) => (
                  <Link
                    key={kp}
                    to={`/practice?kp=${encodeURIComponent(kp)}`}
                    className="kp-mini-pill"
                    title={`按考点筛选：${kp}`}
                  >
                    {kp}
                  </Link>
                ))}
              </div>

              <div className="chapter-progress-footer">
                <div className="progress-bar-track">
                  <div
                    className="progress-seg mastered"
                    style={{ width: st.total ? `${(st.mastered / st.total) * 100}%` : '0%' }}
                  />
                  <div
                    className="progress-seg partial"
                    style={{ width: st.total ? `${(st.partial / st.total) * 100}%` : '0%' }}
                  />
                  <div
                    className="progress-seg wrong"
                    style={{ width: st.total ? `${(st.wrong / st.total) * 100}%` : '0%' }}
                  />
                </div>
                <div className="chapter-progress-text">
                  <span>
                    {allQuestions.length > 0 ? (
                      <>
                        历年累计：<strong>{st.total} 题 / {st.scoreSum} 分</strong>（年均{' '}
                        {(st.scoreSum / readyYearCount).toFixed(1)} 分）
                      </>
                    ) : (
                      <>考纲参考分值：{ch.scoreLabel} 分</>
                    )}
                  </span>
                  <span className="font-mono">
                    已练 {done}/{st.total} · 掌握 {pct}%
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {chaptersPayload?.omittedChapterNote && (
        <p className="omitted-note">注：{chaptersPayload.omittedChapterNote}</p>
      )}
    </div>
  );
};
