import { useMemo } from 'react';
import styles from './GaugeChart.module.css';

export default function GaugeChart({ value = 0, isLoading = false }) {
  const normalizedValue = Math.max(0, Math.min(100, value));
  
  const rotation = useMemo(() => {
    // Map 0-100 to -90 to 90 degrees
    return (normalizedValue / 100) * 180 - 90;
  }, [normalizedValue]);

  const color = useMemo(() => {
    if (normalizedValue >= 70) return '#10b981'; // Green
    if (normalizedValue >= 40) return '#f59e0b'; // Yellow
    return '#ef4444'; // Red
  }, [normalizedValue]);

  const sentiment = useMemo(() => {
    if (normalizedValue >= 70) return 'Positive';
    if (normalizedValue >= 40) return 'Neutral';
    return 'Negative';
  }, [normalizedValue]);

  if (isLoading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>Loading...</div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <svg className={styles.gauge} viewBox="0 0 200 120">
        {/* Background arc */}
        <path
          d="M 20 100 A 80 80 0 0 1 180 100"
          fill="none"
          stroke="var(--border-color)"
          strokeWidth="20"
          strokeLinecap="round"
        />
        
        {/* Colored segments */}
        <path
          d="M 20 100 A 80 80 0 0 1 73.6 36.4"
          fill="none"
          stroke="#ef4444"
          strokeWidth="20"
          strokeLinecap="round"
          opacity="0.3"
        />
        <path
          d="M 73.6 36.4 A 80 80 0 0 1 126.4 36.4"
          fill="none"
          stroke="#f59e0b"
          strokeWidth="20"
          strokeLinecap="round"
          opacity="0.3"
        />
        <path
          d="M 126.4 36.4 A 80 80 0 0 1 180 100"
          fill="none"
          stroke="#10b981"
          strokeWidth="20"
          strokeLinecap="round"
          opacity="0.3"
        />
        
        {/* Value arc */}
        <path
          d={`M 20 100 A 80 80 0 ${normalizedValue > 50 ? 1 : 0} 1 ${
            100 + 80 * Math.cos((rotation * Math.PI) / 180)
          } ${100 + 80 * Math.sin((rotation * Math.PI) / 180)}`}
          fill="none"
          stroke={color}
          strokeWidth="20"
          strokeLinecap="round"
        />
        
        {/* Needle */}
        <g transform={`rotate(${rotation} 100 100)`}>
          <line
            x1="100"
            y1="100"
            x2="100"
            y2="30"
            stroke={color}
            strokeWidth="3"
            strokeLinecap="round"
          />
          <circle cx="100" cy="100" r="6" fill={color} />
        </g>
      </svg>
      
      <div className={styles.value} style={{ color }}>
        {normalizedValue.toFixed(0)}
      </div>
      <div className={styles.label}>{sentiment}</div>
    </div>
  );
}
