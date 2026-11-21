import React, { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Compass, Play, Search } from 'lucide-react';
import { useData } from '../context/DataContext';
import { useStudy } from '../context/StudyContext';
import { Mascot } from '../components/Mascot';
import { MathText } from '../components/MathText';

export const MethodsPage: React.FC = () => {
  const { currentCourse, allQuestions, chapterMap } = useData();
  const { getRecord } = useStudy();
  const [query, setQuery] = useState('');

  const methodsList = useMemo(() => {
    const groups = new Map<
      string,
      { method: string; questions: typeof allQuestions; chapters: Set<number>; scoreSum: number }
    >();
    for (const q of allQuestions) {
      const existing = groups.get(q.method);
      if (existing) {
        existing.questions.push(q);
        existing.chapters.add(q.chapter);
        existing.scoreSum += q.score;
      } else {
        groups.set(q.method, {
          method: q.method,
          questions: [q],
          chapters: new Set([q.chapter]),
          scoreSum: q.score,
        });
      }
    }
    return Array.from(groups.values()).sort(
      (a, b) => b.scoreSum - a.scoreSum || b.questions.length - a.questions.length
    );
  }, [allQuestions]);

  const filtered = useMemo(() => {
    const kw = query.trim().toLowerCase();
    if (!kw) return methodsList;
    return methodsList.filter(
      (m) =>
        m.method.toLowerCase().includes(kw) ||
        m.questions.some(
          (q) =>
            q.title.toLowerCase().includes(kw) ||
            q.kps.some((kp) => kp.toLowerCase().includes(kw))
        )
    );
  }, [methodsList, query]);

  return (
    <div className="page-container">
      <div className="page-header-card">
        <div className="page-kicker">AXIS-B // METHOD REPOSITORY</div>
        <div className="header-flex">
          <div>
            <h1 className="page-title">
              <Compass size={22} className="text-purple" /> {currentCourse.shortLabel} · 解题方法库
            </h1>
            <p className="page-desc">
              按通用解题动作与判据归类历年真题：看到题目条件，就能联想到对应的标准破题流程
            </p>
          </div>
          {methodsList.length > 0 && (
            <div className="search-input-wrap">
              <Search size={15} />
              <input
                type="text"
                placeholder="搜索方法、题型或考点…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
          )}
        </div>
      </div>

      {methodsList.length === 0 ? (
        <div className="empty-state-card">
          <Mascot pose="study" size={130} />
          <h3>「{currentCourse.name}」暂未导入真题包</h3>
          <p>先去浏览已初始化的章节体系与核心公式手册，真题导入后将自动聚合全部解题方法。</p>
          <div className="hero-cta-row">
            <Link to="/chapters" className="btn btn-secondary">
              查看考纲章节
            </Link>
            <Link to="/formulas" className="btn btn-primary">
              背诵核心公式
            </Link>
          </div>
        </div>
      ) : (
        <div className="methods-grid">
          {filtered.map((item, idx) => {
            const masteredCount = item.questions.filter(
              (q) => getRecord(q.id).status === 'mastered'
            ).length;

            return (
              <div key={item.method} className="method-card">
                <div className="method-card-head">
                  <div className="method-rank">M-{String(idx + 1).padStart(2, '0')}</div>
                  <span className="method-score-pill">
                    {item.questions.length} 题 · 共 {item.scoreSum} 分
                  </span>
                </div>

                <h3 className="method-title">{item.method}</h3>

                <div className="method-chapters">
                  {Array.from(item.chapters).map((ch) => (
                    <span key={ch} className="q-tag chapter-tag">
                      第{ch}章 {chapterMap[ch]?.name}
                    </span>
                  ))}
                </div>

                <ul className="method-q-list">
                  {item.questions.map((q) => (
                    <li key={q.id}>
                      <Link
                        to={`/practice?qid=${q.id}`}
                        className="method-q-link"
                        title={`${q.year} 第 ${q.no} 题：${q.title}`}
                      >
                        <span className="mq-id">
                          {q.year}·T{q.no}
                        </span>
                        <span className="mq-title">
                          <MathText text={q.title} inline />
                        </span>
                        <span className="mq-pts">{q.score}分</span>
                      </Link>
                    </li>
                  ))}
                </ul>

                <div className="method-card-foot">
                  <span className="method-mastery">
                    MASTERED {masteredCount}/{item.questions.length}
                  </span>
                  <Link
                    to={`/practice?method=${encodeURIComponent(item.method)}`}
                    className="btn btn-secondary btn-sm"
                  >
                    <Play size={13} /> 专练此法
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
