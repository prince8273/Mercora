import React, { useState } from 'react';
import { Input } from '../../atoms/Input';
import styles from './DateRangePicker.module.css';

export const DateRangePicker = ({
  startDate,
  endDate,
  onChange,
  presets = [
    { label: 'Last 7 days', days: 7 },
    { label: 'Last 30 days', days: 30 },
    { label: 'Last 90 days', days: 90 },
    { label: 'Last 365 days', days: 365 },
  ],
  className = '',
  ...props
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const formatDate = (date) => {
    if (!date) return '';
    const d = new Date(date);
    return d.toISOString().split('T')[0];
  };

  const handlePresetClick = (days) => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - days);

    onChange?.({
      startDate: formatDate(start),
      endDate: formatDate(end),
    });
    setIsOpen(false);
  };

  const handleStartChange = (e) => {
    onChange?.({
      startDate: e.target.value,
      endDate,
    });
  };

  const handleEndChange = (e) => {
    onChange?.({
      startDate,
      endDate: e.target.value,
    });
  };

  return (
    <div className={`${styles.container} ${className}`} {...props}>
      <button
        type="button"
        className={styles.trigger}
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
      >
        <svg className={styles.icon} viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
        </svg>
        <span>
          {startDate && endDate
            ? `${startDate} - ${endDate}`
            : 'Select date range'}
        </span>
        <svg className={styles.chevron} viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      </button>

      {isOpen && (
        <div className={styles.dropdown}>
          <div className={styles.presets}>
            <div className={styles.presetsTitle}>Quick Select</div>
            {presets.map((preset) => (
              <button
                key={preset.label}
                type="button"
                className={styles.presetButton}
                onClick={() => handlePresetClick(preset.days)}
              >
                {preset.label}
              </button>
            ))}
          </div>
          <div className={styles.custom}>
            <div className={styles.customTitle}>Custom Range</div>
            <div className={styles.inputs}>
              <div className={styles.inputGroup}>
                <label className={styles.label}>Start Date</label>
                <Input
                  type="date"
                  value={startDate || ''}
                  onChange={handleStartChange}
                  max={endDate || undefined}
                />
              </div>
              <div className={styles.inputGroup}>
                <label className={styles.label}>End Date</label>
                <Input
                  type="date"
                  value={endDate || ''}
                  onChange={handleEndChange}
                  min={startDate || undefined}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
