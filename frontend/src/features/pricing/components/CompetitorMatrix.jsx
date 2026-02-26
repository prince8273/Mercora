import React, { useState, useMemo } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Button } from '../../../components/atoms/Button';
import { LoadingSkeleton } from '../../../components/molecules/LoadingSkeleton';
import styles from './CompetitorMatrix.module.css';

export const CompetitorMatrix = ({
  data = [],
  competitors = [],
  loading = false,
  error = null,
  onExport,
  className = '',
  ...props
}) => {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const parentRef = React.useRef(null);

  // Sort data
  const sortedData = useMemo(() => {
    if (!sortConfig.key) return data;

    return [...data].sort((a, b) => {
      let aVal = a[sortConfig.key];
      let bVal = b[sortConfig.key];

      // Handle nested competitor prices
      if (sortConfig.key.startsWith('competitor_')) {
        const competitorId = sortConfig.key.replace('competitor_', '');
        aVal = a.competitorPrices?.[competitorId] || Infinity;
        bVal = b.competitorPrices?.[competitorId] || Infinity;
      }

      if (aVal === bVal) return 0;
      
      const comparison = aVal < bVal ? -1 : 1;
      return sortConfig.direction === 'asc' ? comparison : -comparison;
    });
  }, [data, sortConfig]);

  // Virtualization
  const rowVirtualizer = useVirtualizer({
    count: sortedData.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 60,
    overscan: 10,
  });

  const handleSort = (key) => {
    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  const getPriceGap = (yourPrice, competitorPrice) => {
    if (!competitorPrice || competitorPrice === 0) return null;
    const gap = ((yourPrice - competitorPrice) / competitorPrice) * 100;
    return gap;
  };

  const getGapClass = (gap) => {
    if (gap === null) return '';
    if (gap <= -5) return styles.competitive; // Your price is 5%+ lower
    if (gap >= 5) return styles.expensive; // Your price is 5%+ higher
    return styles.neutral;
  };

  const formatPrice = (price) => {
    if (!price) return '-';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(price);
  };

  const formatGap = (gap) => {
    if (gap === null) return '-';
    const sign = gap > 0 ? '+' : '';
    return `${sign}${gap.toFixed(1)}%`;
  };

  const handleExportCSV = () => {
    if (onExport) {
      onExport('csv', sortedData);
    }
  };

  if (loading) {
    return (
      <div className={`${styles.container} ${className}`} {...props}>
        <div className={styles.header}>
          <h3 className={styles.title}>Competitor Price Matrix</h3>
        </div>
        <LoadingSkeleton variant="table" count={10} />
      </div>
    );
  }

  if (error) {
    return (
      <div className={`${styles.container} ${className}`} {...props}>
        <div className={styles.header}>
          <h3 className={styles.title}>Competitor Price Matrix</h3>
        </div>
        <div className={styles.errorState}>
          <p>{error}</p>
          <Button size="sm" onClick={() => window.location.reload()}>
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className={`${styles.container} ${className}`} {...props}>
        <div className={styles.header}>
          <h3 className={styles.title}>Competitor Price Matrix</h3>
        </div>
        <div className={styles.emptyState}>
          <p>No pricing data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`${styles.container} ${className}`} {...props}>
      <div className={styles.header}>
        <h3 className={styles.title}>
          Competitor Price Matrix
          <span className={styles.count}>({sortedData.length} products)</span>
        </h3>
        <Button size="sm" variant="secondary" onClick={handleExportCSV}>
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Export CSV
        </Button>
      </div>

      <div ref={parentRef} className={styles.tableWrapper}>
        <div className={styles.tableContainer}>
          <table className={styles.table}>
            <thead className={styles.thead}>
              <tr>
                <th
                  className={`${styles.th} ${styles.stickyColumn}`}
                  onClick={() => handleSort('productName')}
                >
                  <div className={styles.thContent}>
                    Product
                    {sortConfig.key === 'productName' && (
                      <span className={styles.sortIcon}>
                        {sortConfig.direction === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th className={styles.th} onClick={() => handleSort('yourPrice')}>
                  <div className={styles.thContent}>
                    Your Price
                    {sortConfig.key === 'yourPrice' && (
                      <span className={styles.sortIcon}>
                        {sortConfig.direction === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                {competitors.map((competitor) => (
                  <th
                    key={competitor.id}
                    className={styles.th}
                    onClick={() => handleSort(`competitor_${competitor.id}`)}
                  >
                    <div className={styles.thContent}>
                      {competitor.name}
                      {sortConfig.key === `competitor_${competitor.id}` && (
                        <span className={styles.sortIcon}>
                          {sortConfig.direction === 'asc' ? '↑' : '↓'}
                        </span>
                      )}
                    </div>
                  </th>
                ))}
                <th className={styles.th}>Avg Gap</th>
              </tr>
            </thead>
            <tbody
              className={styles.tbody}
              style={{
                height: `${rowVirtualizer.getTotalSize()}px`,
              }}
            >
              {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                const row = sortedData[virtualRow.index];
                const avgGap = competitors.reduce((sum, comp) => {
                  const gap = getPriceGap(row.yourPrice, row.competitorPrices?.[comp.id]);
                  return gap !== null ? sum + gap : sum;
                }, 0) / competitors.length;

                return (
                  <tr
                    key={virtualRow.key}
                    className={styles.tr}
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: `${virtualRow.size}px`,
                      transform: `translateY(${virtualRow.start}px)`,
                    }}
                  >
                    <td className={`${styles.td} ${styles.stickyColumn}`}>
                      <div className={styles.productCell}>
                        <span className={styles.productName}>{row.productName}</span>
                        <span className={styles.productSku}>{row.sku}</span>
                      </div>
                    </td>
                    <td className={styles.td}>
                      <span className={styles.price}>{formatPrice(row.yourPrice)}</span>
                    </td>
                    {competitors.map((competitor) => {
                      const competitorPrice = row.competitorPrices?.[competitor.id];
                      const gap = getPriceGap(row.yourPrice, competitorPrice);
                      return (
                        <td key={competitor.id} className={styles.td}>
                          <div className={styles.priceCell}>
                            <span className={styles.price}>{formatPrice(competitorPrice)}</span>
                            {gap !== null && (
                              <span className={`${styles.gap} ${getGapClass(gap)}`}>
                                {formatGap(gap)}
                              </span>
                            )}
                          </div>
                        </td>
                      );
                    })}
                    <td className={styles.td}>
                      <span className={`${styles.gap} ${getGapClass(avgGap)}`}>
                        {formatGap(avgGap)}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
