import React, { useState } from 'react';
import { Badge } from '../../atoms/Badge';
import styles from './FilterGroup.module.css';

export const FilterGroup = ({
  options = [],
  selected = [],
  onChange,
  label,
  multiple = true,
  className = '',
  ...props
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const handleToggle = (value) => {
    if (multiple) {
      const newSelected = selected.includes(value)
        ? selected.filter((v) => v !== value)
        : [...selected, value];
      onChange?.(newSelected);
    } else {
      onChange?.([value]);
      setIsOpen(false);
    }
  };

  const handleRemove = (value) => {
    onChange?.(selected.filter((v) => v !== value));
  };

  const handleClearAll = () => {
    onChange?.([]);
  };

  const getOptionLabel = (value) => {
    const option = options.find((opt) => opt.value === value);
    return option?.label || value;
  };

  return (
    <div className={`${styles.filterGroup} ${className}`} {...props}>
      {label && <label className={styles.label}>{label}</label>}
      
      <div className={styles.container}>
        <button
          type="button"
          className={styles.trigger}
          onClick={() => setIsOpen(!isOpen)}
          aria-expanded={isOpen}
          aria-haspopup="listbox"
        >
          <span>
            {selected.length > 0
              ? `${selected.length} selected`
              : 'Select filters'}
          </span>
          <svg className={styles.chevron} viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>

        {isOpen && (
          <div className={styles.dropdown} role="listbox">
            {options.map((option) => (
              <label
                key={option.value}
                className={styles.option}
                role="option"
                aria-selected={selected.includes(option.value)}
              >
                <input
                  type={multiple ? 'checkbox' : 'radio'}
                  checked={selected.includes(option.value)}
                  onChange={() => handleToggle(option.value)}
                  className={styles.checkbox}
                />
                <span>{option.label}</span>
                {option.count !== undefined && (
                  <span className={styles.count}>({option.count})</span>
                )}
              </label>
            ))}
          </div>
        )}
      </div>

      {selected.length > 0 && (
        <div className={styles.chips}>
          {selected.map((value) => (
            <Badge
              key={value}
              variant="primary"
              className={styles.chip}
            >
              {getOptionLabel(value)}
              <button
                type="button"
                onClick={() => handleRemove(value)}
                className={styles.removeButton}
                aria-label={`Remove ${getOptionLabel(value)}`}
              >
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </Badge>
          ))}
          {selected.length > 1 && (
            <button
              type="button"
              onClick={handleClearAll}
              className={styles.clearAll}
            >
              Clear all
            </button>
          )}
        </div>
      )}
    </div>
  );
};
