import React, { useState, useMemo } from 'react';
import { Skeleton } from '../../atoms/Skeleton';
import { Button } from '../../atoms/Button';
import styles from './DataTable.module.css';

export const DataTable = ({
  data = [],
  columns = [],
  loading = false,
  pagination = true,
  pageSize = 10,
  sortable = true,
  onRowClick,
  emptyMessage = 'No data available',
  className = '',
  ...props
}) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });

  // Sorting logic
  const sortedData = useMemo(() => {
    if (!sortConfig.key) return data;

    return [...data].sort((a, b) => {
      const aVal = a[sortConfig.key];
      const bVal = b[sortConfig.key];

      if (aVal === bVal) return 0;
      
      const comparison = aVal < bVal ? -1 : 1;
      return sortConfig.direction === 'asc' ? comparison : -comparison;
    });
  }, [data, sortConfig]);

  // Pagination logic
  const paginatedData = useMemo(() => {
    if (!pagination) return sortedData;
    
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return sortedData.slice(startIndex, endIndex);
  }, [sortedData, currentPage, pageSize, pagination]);

  const totalPages = Math.ceil(data.length / pageSize);

  const handleSort = (key) => {
    if (!sortable) return;

    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  const getSortIcon = (columnKey) => {
    if (sortConfig.key !== columnKey) {
      return (
        <svg className={styles.sortIcon} viewBox="0 0 20 20" fill="currentColor">
          <path d="M5 12a1 1 0 102 0V6.414l1.293 1.293a1 1 0 001.414-1.414l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L5 6.414V12zM15 8a1 1 0 10-2 0v5.586l-1.293-1.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L15 13.586V8z" />
        </svg>
      );
    }

    return sortConfig.direction === 'asc' ? (
      <svg className={styles.sortIcon} viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
      </svg>
    ) : (
      <svg className={styles.sortIcon} viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clipRule="evenodd" />
      </svg>
    );
  };

  if (loading) {
    return (
      <div className={`${styles.tableContainer} ${className}`} {...props}>
        <table className={styles.table}>
          <thead>
            <tr>
              {columns.map((col, idx) => (
                <th key={idx}>
                  <Skeleton width="80%" height="1rem" />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: 5 }).map((_, idx) => (
              <tr key={idx}>
                {columns.map((_, colIdx) => (
                  <td key={colIdx}>
                    <Skeleton width="90%" height="1rem" />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className={`${styles.tableContainer} ${className}`} {...props}>
        <div className={styles.emptyState}>
          <svg className={styles.emptyIcon} viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
          </svg>
          <p>{emptyMessage}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`${styles.tableContainer} ${className}`} {...props}>
      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={sortable ? styles.sortable : ''}
                  onClick={() => handleSort(column.key)}
                  style={{ width: column.width }}
                >
                  <div className={styles.headerContent}>
                    <span>{column.label}</span>
                    {sortable && getSortIcon(column.key)}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedData.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className={onRowClick ? styles.clickable : ''}
                onClick={() => onRowClick?.(row)}
              >
                {columns.map((column) => (
                  <td key={column.key}>
                    {column.render
                      ? column.render(row[column.key], row)
                      : row[column.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {pagination && totalPages > 1 && (
        <div className={styles.pagination}>
          <div className={styles.paginationInfo}>
            Showing {(currentPage - 1) * pageSize + 1} to{' '}
            {Math.min(currentPage * pageSize, data.length)} of {data.length} results
          </div>
          <div className={styles.paginationControls}>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
            >
              Previous
            </Button>
            <span className={styles.pageInfo}>
              Page {currentPage} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
