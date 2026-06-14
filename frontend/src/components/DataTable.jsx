/**
 * DataTable - Generic sortable, paginated table component.
 */

import { useState, useMemo } from 'react';

const defaultPerPageOptions = [10, 25, 50, 100];

export default function DataTable({
  columns,
  data,
  loading = false,
  emptyMessage = 'No results found',
  perPageOptions = defaultPerPageOptions,
  sortColumn,
  sortDirection,
  onSort,
  currentPage,
  totalPages,
  onPageChange,
  perPage,
  onPerPageChange,
  filterable,
  filters,
  onFilterChange,
  actions,
}) {
  const [localPage, setLocalPage] = useState(1);
  const [localPerPage, setLocalPerPage] = useState(perPage || perPageOptions[0]);
  const [searchTerm, setSearchTerm] = useState('');

  const displayedPage = currentPage !== undefined ? currentPage : localPage;
  const displayedPerPage = perPage || localPerPage;

  const filteredData = useMemo(() => {
    if (!searchTerm) return data || [];
    const lower = searchTerm.toLowerCase();
    return (data || []).filter(row =>
      Object.values(row).some(val =>
        String(val).toLowerCase().includes(lower)
      )
    );
  }, [data, searchTerm]);

  const paginatedData = useMemo(() => {
    const start = (displayedPage - 1) * displayedPerPage;
    return filteredData.slice(start, start + displayedPerPage);
  }, [filteredData, displayedPage, displayedPerPage]);

  const totalPagesCalc = useMemo(() => {
    return Math.ceil(filteredData.length / displayedPerPage) || 1;
  }, [filteredData, displayedPerPage]);

  return (
    <div>
      {/* Search + Per Page */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4">
        {filterable && (
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 flex-1 w-full sm:w-auto">
            <input
              type="text"
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full sm:w-64 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
            {filters && filters.map(filter => (
              <select
                key={filter.name}
                value={filter.value || ''}
                onChange={(e) => onFilterChange(filter.name, e.target.value)}
                className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">All</option>
                {filter.options.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            ))}
          </div>
        )}
        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          <span>Rows:</span>
          <select
            value={displayedPerPage}
            onChange={(e) => {
              setLocalPerPage(Number(e.target.value));
              setLocalPage(1);
              onPerPageChange?.(Number(e.target.value));
            }}
            className="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          >
            {perPageOptions.map(opt => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto border border-gray-200 dark:border-gray-700 rounded-lg">
        <table className="w-full text-sm text-left">
          <thead className="bg-gray-50 dark:bg-gray-900 text-gray-600 dark:text-gray-400 font-medium">
            <tr>
              {columns.map(col => (
                <th
                  key={col.key}
                  className="px-4 py-3 whitespace-nowrap cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  onClick={() => onSort?.(col.key)}
                >
                  <div className="flex items-center gap-1">
                    {col.header}
                    {col.sortable && (
                      <span className="text-xs">
                        {sortColumn === col.key
                          ? sortDirection === 'asc' ? '↑' : '↓'
                          : '↕'
                        }
                      </span>
                    )}
                  </div>
                </th>
              ))}
              {actions && <th className="px-4 py-3">Actions</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {loading ? (
              <tr>
                <td colSpan={columns.length + (actions ? 1 : 0)} className="px-4 py-8 text-center">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600 mx-auto" />
                </td>
              </tr>
            ) : paginatedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length + (actions ? 1 : 0)} className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              paginatedData.map((row, idx) => (
                <tr key={row.id || idx} className="hover:bg-gray-50 dark:hover:bg-gray-900/50 transition-colors">
                  {columns.map(col => (
                    <td key={col.key} className="px-4 py-3">
                      {col.render ? col.render(row[col.key], row) : row[col.key]}
                    </td>
                  ))}
                  {actions && (
                    <td className="px-4 py-3">
                      {actions(row)}
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between mt-4 text-sm text-gray-600 dark:text-gray-400">
        <span>
          Showing {(displayedPage - 1) * displayedPerPage + 1} to {Math.min(displayedPage * displayedPerPage, filteredData.length)} of {filteredData.length} results
        </span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              const p = Math.max(1, displayedPage - 1);
              setLocalPage(p);
              onPageChange?.(p);
            }}
            disabled={displayedPage <= 1}
            className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Previous
          </button>
          <span className="px-2">
            Page {displayedPage} of {totalPages || totalPagesCalc}
          </span>
          <button
            onClick={() => {
              const p = Math.min((totalPages || totalPagesCalc), displayedPage + 1);
              setLocalPage(p);
              onPageChange?.(p);
            }}
            disabled={displayedPage >= (totalPages || totalPagesCalc)}
            className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
