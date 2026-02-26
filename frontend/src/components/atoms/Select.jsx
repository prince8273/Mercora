import React from 'react';
import styles from './Select.module.css';

export const Select = ({ 
  label, 
  value, 
  onChange, 
  options = [], 
  placeholder = 'Select an option',
  error,
  disabled = false,
  required = false,
  className = '',
  ...props 
}) => {
  return (
    <div className={`${styles.selectWrapper} ${className}`}>
      {label && (
        <label className={styles.label}>
          {label}
          {required && <span className={styles.required}>*</span>}
        </label>
      )}
      <select
        value={value}
        onChange={onChange}
        disabled={disabled}
        required={required}
        className={`${styles.select} ${error ? styles.error : ''} ${disabled ? styles.disabled : ''}`}
        {...props}
      >
        {placeholder && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {options.map((option) => (
          <option 
            key={option.value} 
            value={option.value}
            disabled={option.disabled}
          >
            {option.label}
          </option>
        ))}
      </select>
      {error && <span className={styles.errorText}>{error}</span>}
    </div>
  );
};
