import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Fish, Sparkles, X } from 'lucide-react';
import { useCompanion } from '../context/CompanionContext';

export const RewardToastHost: React.FC = () => {
  const { toasts, dismissToast } = useCompanion();
  const navigate = useNavigate();

  if (toasts.length === 0) return null;

  return (
    <div className="reward-toast-host" aria-live="polite" aria-label="补给与任务通知">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`reward-toast tone-${t.tone ?? 'info'}`}
          role="status"
          onClick={() => {
            dismissToast(t.id);
            navigate('/companion');
          }}
        >
          <div className="reward-toast-icon">
            {t.fishDelta ? <Fish size={16} /> : <Sparkles size={16} />}
          </div>
          <div className="reward-toast-body">
            <div className="reward-toast-top">
              <strong>{t.title}</strong>
              {t.fishDelta && t.fishDelta > 0 && (
                <span className="reward-toast-delta">+{t.fishDelta} 小鱼干</span>
              )}
            </div>
            {t.subtitle && <div className="reward-toast-sub">{t.subtitle}</div>}
          </div>
          <button
            type="button"
            className="reward-toast-close"
            aria-label="关闭通知"
            onClick={(e) => {
              e.stopPropagation();
              dismissToast(t.id);
            }}
          >
            <X size={13} />
          </button>
        </div>
      ))}
    </div>
  );
};
