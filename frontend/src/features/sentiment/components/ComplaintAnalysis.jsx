import { useState, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { ChartContainer } from '../../../components/molecules/ChartContainer/ChartContainer';
import styles from './ComplaintAnalysis.module.css';

export default function ComplaintAnalysis({ data, isLoading }) {
  const [selectedCategory, setSelectedCategory] = useState(null);

  const categoryData = useMemo(() => {
    if (!data?.categories) return [];
    return data.categories.sort((a, b) => b.count - a.count);
  }, [data]);

  const trendData = useMemo(() => {
    if (!data?.trend) return [];
    return data.trend;
  }, [data]);

  const topComplaints = useMemo(() => {
    if (!selectedCategory || !data?.complaints) return [];
    return data.complaints
      .filter((c) => c.category === selectedCategory)
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);
  }, [selectedCategory, data]);

  if (!data?.categories || data.categories.length === 0) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <h2 className={styles.title}>Complaint Analysis</h2>
        </div>
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>📋</div>
          <p>No complaint data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Complaint Analysis</h2>
        <div className={styles.stats}>
          <div className={styles.statItem}>
            <span className={styles.statValue}>{data.totalComplaints || 0}</span>
            <span className={styles.statLabel}>Total Complaints</span>
          </div>
          <div className={styles.statItem}>
            <span className={styles.statValue} style={{ color: '#ef4444' }}>
              {data.criticalCount || 0}
            </span>
            <span className={styles.statLabel}>Critical</span>
          </div>
        </div>
      </div>

      <div className={styles.content}>
        {/* Category Bar Chart */}
        <div className={styles.chartSection}>
          <h3 className={styles.sectionTitle}>Complaints by Category</h3>
          <ChartContainer isLoading={isLoading} height={300}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categoryData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--card-bg)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '6px',
                  }}
                />
                <Bar
                  dataKey="count"
                  fill="#ef4444"
                  radius={[4, 4, 0, 0]}
                  onClick={(data) => setSelectedCategory(data.name)}
                  cursor="pointer"
                />
              </BarChart>
            </ResponsiveContainer>
          </ChartContainer>
        </div>

        {/* Trend Line Chart */}
        <div className={styles.chartSection}>
          <h3 className={styles.sectionTitle}>Complaint Trend Over Time</h3>
          <ChartContainer isLoading={isLoading} height={300}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--card-bg)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '6px',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="#ef4444"
                  strokeWidth={2}
                  dot={{ fill: '#ef4444', r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartContainer>
        </div>
      </div>

      {/* Top Complaints List */}
      <div className={styles.complaintsList}>
        <h3 className={styles.sectionTitle}>
          {selectedCategory ? `Top Complaints: ${selectedCategory}` : 'Top Complaints'}
        </h3>
        {selectedCategory && topComplaints.length > 0 ? (
          <div className={styles.complaints}>
            {topComplaints.map((complaint, index) => (
              <div key={index} className={styles.complaintItem}>
                <div className={styles.complaintHeader}>
                  <span className={styles.complaintText}>{complaint.text}</span>
                  <span className={styles.complaintCount}>{complaint.count}</span>
                </div>
                <div className={styles.complaintBar}>
                  <div
                    className={styles.complaintBarFill}
                    style={{
                      width: `${(complaint.count / topComplaints[0].count) * 100}%`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className={styles.selectPrompt}>
            Click on a category in the chart above to view specific complaints
          </div>
        )}
      </div>

      {/* Category Cards */}
      <div className={styles.categoryGrid}>
        {categoryData.slice(0, 6).map((category) => (
          <div
            key={category.name}
            className={`${styles.categoryCard} ${
              selectedCategory === category.name ? styles.selected : ''
            }`}
            onClick={() =>
              setSelectedCategory(category.name === selectedCategory ? null : category.name)
            }
          >
            <div className={styles.categoryName}>{category.name}</div>
            <div className={styles.categoryCount}>{category.count}</div>
            <div className={styles.categoryPercentage}>
              {((category.count / data.totalComplaints) * 100).toFixed(1)}%
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
