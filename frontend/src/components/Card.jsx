/**
 * Card - Reusable card wrapper component.
 */

export default function Card({ children, className = '', onClick }) {
  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 ${className}`}
      onClick={onClick}
    >
      {children}
    </div>
  );
}
