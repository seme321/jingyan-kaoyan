import React, { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { BarChart3, CheckCircle2, Flame, Star } from 'lucide-react';
import { useData } from '../context/DataContext';

function getScoreHeatClass(score: number): string {
  if (score <= 0) return 'score-cell score-zero';
  if (score >= 25) return 'score-cell heat-4';
  if (score >= 15) return 'score-cell heat-3';
  if (score >= 7) return 'score-cell heat-2';
  return 'score-cell heat-1';
}

export const DashboardPage: React.FC = () => {
  const { currentCourse, chaptersPayload, chapters, allQuestions } = useData();

  const years = useMemo(
    () => Array.from(new Set(allQuestions.map((q) => q.year))).sort((a, b) => b - a),
    [allQuestions]
  );

  const comparisonRows = useMemo(() => {
    return chapters.map((ch) => {
      const qs = allQuestions.filter((q) => q.chapter === ch.chapter);
      const bigTypes = new Set(['calc', 'proof']);
      const calcCnt = qs.filter((q) => bigTypes.has(q.type)).length;
      const smallCnt = qs.length - calcCnt;
      const totalScore = qs.reduce((s, q) => s + q.score, 0);
      const byYear: Record<number, number> = {};
      for (const y of years) {
        byYear[y] = qs.filter((q) => q.year === y).reduce((s, q) => s + q.score, 0);
      }
      const avgScore = years.length > 0 ? +(totalScore / years.length).toFixed(1) : 0;
      return {
        ...ch,
        smallCnt,
        calcCnt,
        totalCnt: qs.length,
        totalScore,
        avgScore,
        byYear,
      };
    });
  }, [chapters, allQuestions, years]);

  const maxAvg = useMemo(
    () => Math.max(1, ...comparisonRows.map((r) => r.avgScore)),
    [comparisonRows]
  );

  return (
    <div className="page-container">
      <div className="page-header-card">
        <div className="page-kicker">PROPOSITION ANALYTICS // {currentCourse.id.toUpperCase()}</div>
        <h1 className="page-title">
          <BarChart3 size={22} className="text-sky" /> {currentCourse.name} · 命题结构大盘
        </h1>
        <p className="page-desc">
          {chaptersPayload?.syllabusTitle ?? '章节考察规律与历年真题实考分值对照'}
          {years.length > 0
            ? `（已纳入 ${years[years.length - 1]}–${years[0]} 共 ${years.length} 年 ${allQuestions.length} 道真题实测数据）`
            : '（当前板块已配置考纲规律，导入真题后将自动统计历年实考分值）'}
        </p>

        {chaptersPayload && chaptersPayload.highlights.length > 0 && (
          <div className="law-verify-grid">
            {chaptersPayload.highlights.slice(0, 2).map((hl, idx) => (
              <div key={idx} className="law-card verified">
                {years.length > 0 ? (
                  <CheckCircle2 size={18} className="text-emerald" style={{ flexShrink: 0, marginTop: 2 }} />
                ) : (
                  <Flame size={18} className="text-amber" style={{ flexShrink: 0, marginTop: 2 }} />
                )}
                <div>
                  <strong>INSIGHT 0{idx + 1} // 核心命题特征</strong>
                  <p>{hl}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card-panel">
        <div className="panel-head-flex">
          <h3 className="panel-title">SCORE HEAT MATRIX // 章节考察规律 vs 历年真题实测分布（单位：分）</h3>
          <span className="hud-code">
            HEAT: 1–6 浅青 · 7–14 中青 · 15–24 深青 · 25+ 警示黄峰值（可横向滑动）
          </span>
        </div>

        <div className="diag-table-wrap">
          <table className="data-table dashboard-table">
            <thead>
              <tr>
                <th>具体章节</th>
                <th>常见题型</th>
                <th>参考分值</th>
                <th>难度</th>
                {years.map((y) => (
                  <th key={y} style={{ textAlign: 'center' }}>
                    {years.length > 6 ? y : `${y}分值`}
                  </th>
                ))}
                {years.length > 1 && <th>年均分</th>}
                {years.length > 0 && <th>实考题型累计</th>}
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {comparisonRows.map((r) => (
                <tr key={r.chapter}>
                  <td>
                    <span className="hud-code" style={{ marginRight: '0.45rem' }}>
                      CH.{String(r.chapter).padStart(2, '0')}
                    </span>
                    <strong>{r.name}</strong>
                  </td>
                  <td>{r.questionTypes}</td>
                  <td className="font-mono">{r.scoreLabel} 分</td>
                  <td>
                    <span className="stars-inline">
                      {Array.from({ length: r.stars }).map((_, i) => (
                        <Star key={i} size={12} fill="currentColor" className="text-amber" />
                      ))}
                    </span>
                  </td>
                  {years.map((y) => (
                    <td key={y} className={getScoreHeatClass(r.byYear[y])}>
                      {years.length > 6 ? (r.byYear[y] > 0 ? r.byYear[y] : '—') : `${r.byYear[y]} 分`}
                    </td>
                  ))}
                  {years.length > 1 && (
                    <td>
                      <div className="inline-bar-cell">
                        <div className="mini-bar" style={{ width: '56px' }}>
                          <div
                            style={{
                              width: `${Math.round((r.avgScore / maxAvg) * 100)}%`,
                              background: r.avgScore >= 15 ? 'var(--yellow)' : 'var(--primary)',
                            }}
                          />
                        </div>
                        <strong className={`font-mono ${r.calcCnt > 0 ? 'text-sky' : ''}`}>
                          {r.avgScore}
                        </strong>
                      </div>
                    </td>
                  )}
                  {years.length > 0 && (
                    <td>
                      {r.smallCnt > 0 && <span className="mini-type-chip">小题×{r.smallCnt}</span>}
                      {r.calcCnt > 0 && <span className="mini-type-chip big">计算/推导×{r.calcCnt}</span>}
                    </td>
                  )}
                  <td>
                    <Link to={`/practice?chapter=${r.chapter}`} className="btn-inline-link">
                      刷题 ({r.totalCnt}) →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {chaptersPayload?.omittedChapterNote && (
          <p className="omitted-note" style={{ marginTop: '0.75rem' }}>
            {chaptersPayload.omittedChapterNote}
          </p>
        )}
      </div>
    </div>
  );
};
