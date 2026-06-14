import React from 'react'
/**
 * StatusBadge - Displays a colored badge for status values.
 * Reusable across all pages.
 */

const statusStyles = {
  active: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  inactive: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400',
  monitoring: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  flagged: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  completed: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  running: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  failed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  submitted: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  confirmed_removed: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  still_listed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  requires_manual: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
  needs_action: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
  verified_removed: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
  success: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  error: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  info: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  healthy: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  degraded: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  down: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
};

export default function StatusBadge({ status, children }) {
  const label = children || status || 'unknown';
  const style = statusStyles[status] || statusStyles.inactive;

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${style}`}>
      {label}
    </span>
  );
}
