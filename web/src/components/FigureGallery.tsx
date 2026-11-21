import React, { useEffect, useState } from 'react';
import { Contrast, Maximize2, X } from 'lucide-react';
import type { DiagramDarkMode, QuestionFigure } from '../types';
import { useStudy } from '../context/StudyContext';
import { useData } from '../context/DataContext';

interface FigureGalleryProps {
  figures: QuestionFigure[];
  variant?: 'exam' | 'solution';
}

export const FigureGallery: React.FC<FigureGalleryProps> = ({ figures, variant = 'exam' }) => {
  const { state, resolvedTheme } = useStudy();
  const { resolveCourseAsset } = useData();
  const [zoomFig, setZoomFig] = useState<QuestionFigure | null>(null);
  const [lightboxBlueprint, setLightboxBlueprint] = useState(false);

  const diagramMode: DiagramDarkMode =
    state.settings.diagramDarkMode ?? (state.settings.softDiagramInDark ? 'blueprint' : 'original');

  useEffect(() => {
    if (!zoomFig) return;
    setLightboxBlueprint(resolvedTheme === 'dark' && diagramMode === 'blueprint');
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setZoomFig(null);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [zoomFig, resolvedTheme, diagramMode]);

  if (!figures || figures.length === 0) return null;

  const modeClass = `fig-mode-${diagramMode}`;
  const prefix = variant === 'solution' ? 'SOL.FIG' : 'FIG';

  return (
    <>
      <div className={`fig-grid ${variant === 'solution' ? 'fig-grid-sol' : ''}`}>
        {figures.map((fig, idx) => {
          const resolvedUrl = resolveCourseAsset(fig.src);
          return (
            <figure
              key={`${fig.src}-${idx}`}
              className={`fig-card ${modeClass}`}
              onClick={() => setZoomFig(fig)}
              title="点击放大查看高清工程示意图"
            >
              <div className="fig-img-wrap">
                <img src={resolvedUrl} alt={fig.caption || '题目附图'} loading="lazy" />
                <button type="button" className="fig-zoom-btn" aria-label="放大查看">
                  <Maximize2 size={12} /> ZOOM
                </button>
              </div>
              <figcaption className="fig-caption">
                <span className="fig-cap-code">
                  {prefix}.{String(idx + 1).padStart(2, '0')}
                </span>
                <span>{fig.caption || (variant === 'solution' ? '解析示意图' : '题目示意图')}</span>
              </figcaption>
            </figure>
          );
        })}
      </div>

      {zoomFig && (
        <div className="lightbox-backdrop" onClick={() => setZoomFig(null)}>
          <div className="lightbox-content" onClick={(e) => e.stopPropagation()}>
            <div className="lightbox-toolbar">
              <span className="hud-code">
                SCHEMATIC VIEWER // {zoomFig.caption || '工程高清大图'}
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => setLightboxBlueprint((v) => !v)}
                  title="切换蓝图夜视与原始白底视图"
                >
                  <Contrast size={14} /> {lightboxBlueprint ? '切回原始白底' : '蓝图夜视模式'}
                </button>
                <button
                  type="button"
                  className="lightbox-close"
                  onClick={() => setZoomFig(null)}
                  aria-label="关闭大图"
                >
                  <X size={18} />
                </button>
              </div>
            </div>
            <div className={`lightbox-stage ${lightboxBlueprint ? 'blueprint' : ''}`}>
              <img src={resolveCourseAsset(zoomFig.src)} alt={zoomFig.caption || '高清大图'} />
            </div>
            {zoomFig.caption && <div className="lightbox-caption">{zoomFig.caption}</div>}
          </div>
        </div>
      )}
    </>
  );
};
