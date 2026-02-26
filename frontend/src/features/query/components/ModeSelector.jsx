import React from 'react';
import styles from './ModeSelector.module.css';

export const ModeSelector = ({
  mode = 'quick',
  onChange,
  disabled = false,
  className = '',
  ...props
}) => {
  const modes = [
    {
      value: 'quick',
      label: 'Quick',
      description: 'Fast analysis with basic insights',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
    },
    {
      value: 'deep',
      label: 'Deep',
      description: 'Comprehensive analysis with detailed insights',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
    },
  ];

  return (
    <div className={`${styles.container} ${className}`} {...props}>
      <label className={styles.label}>Analysis Mode</label>
      <div className={styles.modeGrid}>
        {modes.map((modeOption) => (
          <button
            key={modeOption.value}
            type="button"
            className={`${styles.modeButton} ${
              mode === modeOption.value ? styles.active : ''
            }`}
            onClick={() => onChange(modeOption.value)}
            disabled={disabled}
            aria-pressed={mode === modeOption.value}
          >
            <div className={styles.modeIcon}>{modeOption.icon}</div>
            <div className={styles.modeContent}>
              <span className={styles.modeLabel}>{modeOption.label}</span>
              <span className={styles.modeDescription}>
                {modeOption.description}
              </span>
            </div>
            {mode === modeOption.value && (
              <div className={styles.checkmark}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
};
