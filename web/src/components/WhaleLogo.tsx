import React from 'react';

/** 本站原创矢量吉祥物标志：一条圆滚滚的小胖鲸 + 水滴喷泉。 */
export const WhaleLogo: React.FC<{ size?: number; className?: string }> = ({ size = 30, className = '' }) => (
  <svg
    className={className}
    width={size}
    height={size}
    viewBox="0 0 64 64"
    role="img"
    aria-label="鲸研水力标志"
  >
    <defs>
      <linearGradient id="wl-body" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stopColor="#4aa8ff" />
        <stop offset="100%" stopColor="#1e5fd8" />
      </linearGradient>
    </defs>
    <path d="M32 6c-2.6 3.4-3.8 6-3.8 8a3.8 3.8 0 0 0 7.6 0c0-2-1.2-4.6-3.8-8z" fill="#3fd0e0" />
    <path
      d="M8 38c0-11 10-18 23-18 12 0 21 6.5 23.5 15.5l4.2-4.6c1.3-1.4 3.6-.4 3.4 1.5l-1 9.3c-.1 1 .3 2 1 2.6l1.3 1.2c1.2 1.1.4 3.2-1.3 3.1l-6-.4C50.6 54 42 58 31 58 17 58 8 50 8 38z"
      fill="url(#wl-body)"
    />
    <path d="M14 44c4 7 10 9.5 17 9.5 8 0 14-3 17.5-8.5-8 3-26 3.6-34.5-1z" fill="#dff3ff" />
    <circle cx="22" cy="36" r="3.2" fill="#0b1e3d" />
    <circle cx="23" cy="35" r="1.1" fill="#fff" />
    <ellipse cx="17.5" cy="42" rx="3" ry="1.8" fill="#ff9db5" opacity=".75" />
    <path d="M27 41.5c1.6 1.6 3.6 1.6 5.2 0" stroke="#0b1e3d" strokeWidth="1.8" fill="none" strokeLinecap="round" />
  </svg>
);
