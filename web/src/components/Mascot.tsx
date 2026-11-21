import React, { useEffect, useState } from 'react';
import { BRAND } from '../brand';
import { WhaleLogo } from './WhaleLogo';
import { useCompanionOptional } from '../context/CompanionContext';

export type MascotPose = 'hero' | 'think' | 'cheer' | 'study';

interface MascotProps {
  pose: MascotPose;
  size?: number;
  className?: string;
  float?: boolean;
  isHomeStage?: boolean;
  forceDefault?: boolean;
}

/** 看板娘立绘（支持全局/首页替换为图鉴角色，图片缺失时回退为原创矢量小胖鲸）。 */
export const Mascot: React.FC<MascotProps> = ({
  pose,
  size = 160,
  className = '',
  float = false,
  isHomeStage = false,
  forceDefault = false,
}) => {
  const ctx = useCompanionOptional();
  const [failed, setFailed] = useState(false);

  const shouldUseCustom =
    !forceDefault &&
    ctx !== null &&
    !ctx.activeMascot.isDefaultDafeyu &&
    (isHomeStage || ctx.companion.applyGlobally);

  const imgSrc = shouldUseCustom ? ctx.activeMascot.sprite : `./mascot/${pose}.webp`;
  const altText = shouldUseCustom ? ctx.activeMascot.name : BRAND.mascotName;

  useEffect(() => {
    setFailed(false);
  }, [imgSrc]);

  return (
    <div
      className={`mascot ${float ? 'mascot-float' : ''} ${className}`}
      style={{ width: size, height: size }}
    >
      {failed ? (
        <WhaleLogo size={Math.round(size * 0.82)} />
      ) : (
        <img
          src={imgSrc}
          alt={altText}
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
  forceDefault?: boolean;
}

/** 看板娘 + 战术终端提示条。 */
export const MascotTip: React.FC<MascotTipProps> = ({
  pose,
  children,
  size = 76,
  tone = 'info',
  className = '',
  forceDefault = false,
}) => {
  const ctx = useCompanionOptional();
  const useCustom =
    !forceDefault &&
    ctx !== null &&
    !ctx.activeMascot.isDefaultDafeyu &&
    ctx.companion.applyGlobally;

  const badgeText = useCustom
    ? `${ctx.activeMascot.code} // ${ctx.activeMascot.name}${ctx.activeMascot.bondLevel >= 4 ? ' · ✦ 默契连携' : ''}`
    : `UNIT DF-01 // ${BRAND.mascotName}`;

  const isSynergy = useCustom && ctx.activeMascot.bondLevel >= 4;

  return (
    <div className={`mascot-tip tone-${tone} ${isSynergy ? 'bond-synergy' : ''} ${className}`}>
      <Mascot pose={pose} size={size} forceDefault={forceDefault} />
      <div className="mascot-bubble">
        <span className="mascot-bubble-name">{badgeText}</span>
        <div>{children}</div>
      </div>
    </div>
  );
};
