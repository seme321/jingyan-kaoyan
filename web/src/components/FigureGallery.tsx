import React, { useEffect, useState } from 'react';
import { Maximize2, X } from 'lucide-react';
import type { QuestionFigure } from '../types';
import { useStudy } from '../context/StudyContext';
import { useData } from '../context/DataContext';

interface FigureGalleryProps {
  figures: QuestionFigure[];
  variant?: 'exam' | 'solution';
}

export const FigureGallery: React.FC<FigureGalleryProps> = ({ figures, variant = 'exam' }) => {
  const { state } = useStudy();
  const { resolveCourseAsset } = useData();
  const [zoomFig, setZoomFig] = useState<QuestionFigure | null>(null);

  useEffect(() => {
    if (!zoomFig) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setZoomFig(null);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [zoomFig]);

  if (!figures || figures.length === 0) return null;

  const softClass = state.settings.softDiagramInDark ? 'fig-soft-dark' : '';

  return (
    <>
      <div className={`fig-grid ${variant === 'solution' ? 'fig-grid-sol' : ''}`}>
        {figures.map((fig, idx) => {
          const resolvedUrl = resolveCourseAsset(fig.src);
          return (
            <figure
              key={`${fig.src}-${idx}`}
              className={`fig-card ${softClass}`}
              onClick={() => setZoomFig(fig)}
              title="点击放大查看高清大图"
            >
              <div className="fig-img-wrap">
                <img src={resolvedUrl} alt={fig.caption || '题目附图'} loading="lazy" />
                <button type="button" className="fig-zoom-btn" aria-label="放大查看">
                  <Maximize2 size={14} />
                </button>
              </div>
              {fig.caption && <figcaption className="fig-caption">{fig.caption}</figcaption>}
            </figure>
          );
        })}
      </div>

      {zoomFig && (
        <div className="lightbox-backdrop" onClick={() => setZoomFig(null)}>
          <div className="lightbox-content" onClick={(e) => e.stopPropagation()}>
            <button
              type="button"
              className="lightbox-close"
              onClick={() => setZoomFig(null)}
              aria-label="关闭大图"
            >
              <X size={20} />
            </button>
            <img src={resolveCourseAsset(zoomFig.src)} alt={zoomFig.caption || '高清大图'} />
            {zoomFig.caption && <div className="lightbox-caption">{zoomFig.caption}</div>}
          </div>
        </div>
      )}
    </>
  );
};
