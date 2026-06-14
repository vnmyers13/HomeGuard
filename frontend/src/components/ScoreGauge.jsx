import React from 'react'
/**
 * ScoreGauge - Circular score display for exposure/privacy scores.
 * 0-100 score with color-coded ring.
 */

import { useMemo } from 'react';

const scoreColor = (score) => {
  if (score >= 80) return { ring: 'text-green-500', text: 'text-green-600 dark:text-green-400', bg: 'bg-green-50 dark:bg-green-900/20' };
  if (score >= 60) return { ring: 'text-yellow-500', text: 'text-yellow-600 dark:text-yellow-400', bg: 'bg-yellow-50 dark:bg-yellow-900/20' };
  if (score >= 40) return { ring: 'text-orange-500', text: 'text-orange-600 dark:text-orange-400', bg: 'bg-orange-50 dark:bg-orange-900/20' };
  return { ring: 'text-red-500', text: 'text-red-600 dark:text-red-400', bg: 'bg-red-50 dark:bg-red-900/20' };
};

export default function ScoreGauge({ score, size = 120, label, subtitle }) {
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const colors = scoreColor(score);

  const displayScore = useMemo(() => Math.max(0, Math.min(100, score)), [score]);

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="currentColor"
            strokeWidth="8"
            fill="none"
            className="text-gray-200 dark:text-gray-700"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="currentColor"
            strokeWidth="8"
            fill="none"
            className={colors.ring}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.6s ease' }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <span className={`text-2xl font-bold ${colors.text}`}>{displayScore}</span>
            <span className="text-xs text-gray-500 dark:text-gray-400 block">/ 100</span>
          </div>
        </div>
      </div>
      {label && <span className="mt-2 text-sm font-medium text-gray-700 dark:text-gray-300">{label}</span>}
      {subtitle && <span className="text-xs text-gray-500 dark:text-gray-400">{subtitle}</span>}
    </div>
  );
}
