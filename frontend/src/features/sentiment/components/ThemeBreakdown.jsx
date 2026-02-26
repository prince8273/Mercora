import { useState, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { ChartContainer } from '../../../components/molecules/ChartContainer/ChartContainer';
import styles from './ThemeBreakdown.module.css';

const THEME_COLORS = [
  '#3b82f6',
  '#10b981',
  '#f59e0b',
  '#ef4444',
  '#8b5cf6',
  '#ec4899',
  '#06b6d4',
  '#84cc16',
];

export default function ThemeBreakdown({ data, isLoading }) {
  const [selectedTheme, setSelectedTheme] = useState(null);

  const chartData = useMemo(() => {
    if (!data?.themes) return [];
    
    return data.themes
      .sort((a, b) => b.percentage - a.percentage)
      .slice(0, 8)
      .map((theme, index) => ({
        ...theme,
        color: THEME_COLORS[index % THEME_COLORS.length],
      }));
  }, [data]);

  const topThemes = useMemo(() => {
    if (!data?.themes) return [];
    return data.themes.sort((a, b) => b.percentage - a.percentage).slice(0, 10);
  }, [data]);

  if (!data?.themes || data.themes.length === 0) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <h2 className={styles.title}>Theme Breakdown</h2>
        </div>
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>📊</div>
          <p>No theme data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Theme Breakdown</h2>
      </div>

      <div className={styles.content}>
        {/* Bar Chart */}
        <div className={styles.chartSection}>
          <ChartContainer isLoading={isLoading} height={400}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis type="number" domain={[0, 100]} />
                <YAxis dataKey="name" type="category" width={120} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--card-bg)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '6px',
                  }}
                  formatter={(value) => `${value.toFixed(1)}%`}
                />
                <Bar
                  dataKey="percentage"
                  radius={[0, 4, 4, 0]}
                  onClick={(data) => setSelectedTheme(data.name)}
                  cursor="pointer"
                >
                  {chartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.color}
                      opacity={selectedTheme === entry.name || !selectedTheme ? 1 : 0.3}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </ChartContainer>
        </div>

        {/* Top Themes List */}
        <div className={styles.themesList}>
          <h3 className={styles.sectionTitle}>Top Themes</h3>
          {topThemes.map((theme, index) => (
            <div
              key={theme.name}
              className={`${styles.themeItem} ${
                selectedTheme === theme.name ? styles.selected : ''
              }`}
              onClick={() => setSelectedTheme(theme.name === selectedTheme ? null : theme.name)}
            >
              <div className={styles.themeHeader}>
                <span className={styles.themeName}>{theme.name}</span>
                <span className={styles.themePercentage}>{theme.percentage.toFixed(1)}%</span>
              </div>
              <div className={styles.themeBar}>
                <div
                  className={styles.themeBarFill}
                  style={{
                    width: `${theme.percentage}%`,
                    background: THEME_COLORS[index % THEME_COLORS.length],
                  }}
                />
              </div>
              <div className={styles.themeCount}>{theme.count} mentions</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
