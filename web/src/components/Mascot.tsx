import React, { useState } from 'react';
import { BRAND } from '../brand';
import { WhaleLogo } from './WhaleLogo';

export type MascotPose = 'hero' | 'think' | 'cheer' | 'study';

interface MascotProps {
  pose: MascotPose;
  size?: number;
  className?: string;
  float?: boolean;
}

/** 看板娘「大肥鱼」立绘；图片缺失时回退为原创矢量小胖鲸。 */
export const Mascot: React.FC<MascotProps> = ({ pose, size = 160, className = '', float = false }) => {
  const [failed, setFailed] = useState(false);
  return (
    <div
      className={`mascot ${float ? 'mascot-float' : ''} ${className}`}
      style={{ width: size, height: size }}
    >
      {failed ? (
        <WhaleLogo size={Math.round(size * 0.82)} />
      ) : (
        <img
          src={`./mascot/${pose}.webp`}
          alt={`${BRAND.mascotName}`}
          draggable={false}
          onError={() => setFailed(true)}
        />
      )}
    </div>
  );
};

interface MascotTipProps {
  pose: MascotPose;
  children: React.ReactNode;
  size?: number;
  tone?: 'info' | 'ok' | 'warn';
  className?: string;
}

/** 看板娘 + 战术终端提示条。 */
export const MascotTip: React.FC<MascotTipProps> = ({
  pose,
  children,
  size = 76,
  tone = 'info',
  className = '',
}) => (
  <div className={`mascot-tip tone-${tone} ${className}`}>
    <Mascot pose={pose} size={size} />
    <div className="mascot-bubble">
      <span className="mascot-bubble-name">
        UNIT DF-01 // {BRAND.mascotName}
      </span>
      <div>{children}</div>
    </div>
  </div>
);
