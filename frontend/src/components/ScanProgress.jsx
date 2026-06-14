import React from 'react'
/**
 * ScanProgress - Displays scan progress with steps and status.
 * Can be driven by WebSocket updates or polling.
 */

import { useEffect, useState } from 'react';

const stepIcons = {
  idle: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4">
      <circle cx="12" cy="12" r="10" />
    </svg>
  ),
  running: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4 animate-spin">
      <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
    </svg>
  ),
  completed: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4">
      <path d="M20 6L9 17l-5-5" />
    </svg>
  ),
  failed: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4">
      <path d="M18 6L6 18M6 6l12 12" />
    </svg>
  ),
};

export default function ScanProgress({ scan, steps = [], compact = false }) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!scan) return;

    const totalSteps = steps.length || 1;
    const currentStep = scan.current_step || 0;
    setProgress(Math.round((currentStep / totalSteps) * 100));
  }, [scan, steps]);

  if (!scan && steps.length === 0) return null;

  const status = scan?.status || 'idle';
  const statusColor = {
    idle: 'text-gray-400',
    running: 'text-blue-600 dark:text-blue-400',
    completed: 'text-green-600 dark:text-green-400',
    failed: 'text-red-600 dark:text-red-400',
    cancelled: 'text-gray-400',
  };

  if (compact) {
    return (
      <div className="flex items-center gap-3">
        <span className={statusColor[status] || statusColor.idle}>
          {stepIcons[status] || stepIcons.idle}
        </span>
        <div className="flex-1">
          <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-300 ${
                status === 'completed' ? 'bg-green-500' :
                status === 'failed' ? 'bg-red-500' :
                status === 'cancelled' ? 'bg-gray-400' :
                'bg-blue-500'
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
        <span className="text-xs text-gray-500 dark:text-gray-400 w-10 text-right">{progress}%</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className={statusColor[status] || statusColor.idle}>
            {stepIcons[status] || stepIcons.idle}
          </span>
          <div>
            <h4 className="text-sm font-medium text-gray-900 dark:text-white">
              {scan?.title || 'Scan in progress'}
            </h4>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {scan?.broker_count || steps.length} brokers · {status}
            </p>
          </div>
        </div>
        <span className={`text-sm font-medium ${statusColor[status] || statusColor.idle}`}>
          {progress}%
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-2.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out ${
            status === 'completed' ? 'bg-green-500' :
            status === 'failed' ? 'bg-red-500' :
            status === 'cancelled' ? 'bg-gray-400' :
            'bg-blue-500'
          }`}
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Steps */}
      {steps.length > 0 && (
        <div className="space-y-2">
          {steps.map((step, idx) => {
            const isComplete = idx < (scan?.current_step || 0);
            const isCurrent = idx === (scan?.current_step || 0) && status === 'running';
            return (
              <div key={idx} className="flex items-center gap-3 text-sm">
                <span className={`flex-shrink-0 ${
                  isComplete ? 'text-green-500' :
                  isCurrent ? 'text-blue-500' :
                  'text-gray-400'
                }`}>
                  {isComplete ? stepIcons.completed :
                   isCurrent ? stepIcons.running :
                   stepIcons.idle}
                </span>
                <span className={
                  isCurrent ? 'text-gray-900 dark:text-white font-medium' :
                  'text-gray-600 dark:text-gray-400'
                }>
                  {step}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
